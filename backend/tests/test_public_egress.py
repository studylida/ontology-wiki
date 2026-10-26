"""Deterministic network-boundary tests; no real DNS, proxy or model calls."""
from types import SimpleNamespace

import httpcore
import httpx
import pytest
from pydantic import ValidationError

from knowledge.core.config import Settings
from knowledge.core.errors import AppError
from knowledge.integrations.public_egress import (
    GoogleDohResolver, PinnedProxyBackend, PinnedProxyTransport, public_fetch_options,
)
from knowledge.integrations.public_fetch import fetch_public

PROXY = "http://test-egress.invalid:8889"
SOURCE = "https://paper.example.test/article?q=public"
PUBLIC_IP = "9.9.9.9"  # An inert fixture; no test contacts this address.


def dns_response(request, a=None, aaaa=None, **patch):
    kind = request.url.params["type"]
    assert request.url.host == "dns.google"
    assert request.url.params["cd"] == "false"
    assert request.url.params["edns_client_subnet"] == "0.0.0.0/0"
    record_type = 1 if kind == "A" else 28
    values = (a if a is not None else [PUBLIC_IP]) if kind == "A" else (aaaa or [])
    payload = {"Status": 0, "TC": False, "CD": False, "AD": False,
        "Question": [{"name": "paper.example.test.", "type": record_type}],
        "Answer": [{"type": record_type, "data": value} for value in values]}
    payload.update(patch)
    return httpx.Response(200, json=payload)


@pytest.mark.asyncio
async def test_doh_checks_a_and_aaaa_before_pinning_and_does_not_claim_dnssec():
    audit, queried = [], []
    def reply(request):
        queried.append(request.url.params["type"])
        return dns_response(request, aaaa=["2606:4700:4700::1111"])
    resolver = GoogleDohResolver(PROXY, audit=audit, transport=httpx.MockTransport(reply))
    assert await resolver(SOURCE) == (f"https://{PUBLIC_IP}/article?q=public", "paper.example.test")
    assert queried == ["A", "AAAA"]
    assert all(item["dnssecValidated"] is False for item in audit)


@pytest.mark.asyncio
@pytest.mark.parametrize("a,aaaa", [([PUBLIC_IP, "127.0.0.1"], []), ([PUBLIC_IP], ["::1"]), (["10.0.0.1"], [])])
async def test_any_private_a_or_aaaa_rejects_the_whole_resolution(a, aaaa):
    resolver = GoogleDohResolver(PROXY, transport=httpx.MockTransport(lambda request: dns_response(request, a=a, aaaa=aaaa)))
    with pytest.raises(AppError) as caught:
        await resolver(SOURCE)
    assert caught.value.code == "unsafe_source_url"


@pytest.mark.asyncio
@pytest.mark.parametrize("patch", [{"Status": 3}, {"TC": True}, {"CD": True},
                                  {"Question": [{"name": "different.example.", "type": 1}]}])
async def test_invalid_doh_response_fails_without_other_resolver(patch, monkeypatch):
    import socket
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: pytest.fail("No system fallback"))
    resolver = GoogleDohResolver(PROXY, transport=httpx.MockTransport(lambda request: dns_response(request, **patch)))
    with pytest.raises(AppError) as caught:
        await resolver(SOURCE)
    assert caught.value.code == "source_dns_response_invalid"


@pytest.mark.asyncio
async def test_doh_denial_does_not_retry_with_another_endpoint():
    calls = []
    def denied(request):
        calls.append(str(request.url))
        return httpx.Response(403)
    resolver = GoogleDohResolver(PROXY, transport=httpx.MockTransport(denied))
    with pytest.raises(AppError) as caught:
        await resolver(SOURCE)
    assert caught.value.code == "source_dns_unavailable" and len(calls) == 1


@pytest.mark.asyncio
async def test_private_url_rejected_before_any_doh_request():
    resolver = GoogleDohResolver(PROXY, transport=httpx.MockTransport(lambda _: pytest.fail("No DNS for private IP")))
    with pytest.raises(AppError) as caught:
        await resolver("https://127.0.0.1/private")
    assert caught.value.code == "unsafe_source_url"


class TunnelStream(httpcore.AsyncNetworkStream):
    def __init__(self, *, connect_status=200, response=None, tls_failure=False):
        self.data = bytearray(f"HTTP/1.1 {connect_status} Test\r\n\r\n".encode())
        self.response = response or b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 13\r\n\r\npublic source"
        self.writes, self.tls = [], []
        self.closed, self.tls_failure = False, tls_failure

    async def read(self, max_bytes, timeout=None):
        part = bytes(self.data[:max_bytes])
        del self.data[:max_bytes]
        return part

    async def write(self, buffer, timeout=None):
        self.writes.append(buffer)

    async def start_tls(self, ssl_context, server_hostname=None, timeout=None):
        self.tls.append({"hostname": server_hostname, "check_hostname": ssl_context.check_hostname,
                         "verify_mode": ssl_context.verify_mode})
        if self.tls_failure:
            raise httpcore.ConnectError("Fixture certificate verification failure")
        self.data.extend(self.response)
        return self

    async def aclose(self):
        self.closed = True


class TunnelBackend(httpcore.AsyncNetworkBackend):
    def __init__(self, stream):
        self.stream, self.connects = stream, []

    async def connect_tcp(self, host, port, **kwargs):
        self.connects.append((host, port))
        return self.stream


async def public_resolver(url):
    return f"https://{PUBLIC_IP}/article?q=public", "paper.example.test"


@pytest.mark.asyncio
async def test_connect_uses_ip_and_tls_verifies_original_hostname():
    import ssl
    stream = TunnelStream()
    backend = TunnelBackend(stream)
    transport = PinnedProxyTransport(PROXY, backend=backend)
    raw, media_type, final_url = await fetch_public(SOURCE, resolver=public_resolver, transport=transport)
    assert raw == b"public source" and media_type == "text/plain" and final_url == SOURCE
    assert backend.connects == [("test-egress.invalid", 8889)]
    assert stream.writes[0].startswith(f"CONNECT {PUBLIC_IP}:443 HTTP/1.1\r\n".encode())
    assert stream.tls == [{"hostname": "paper.example.test", "check_hostname": True, "verify_mode": ssl.CERT_REQUIRED}]
    assert b"Host: paper.example.test\r\n" in b"".join(stream.writes[1:])
    assert stream.closed


@pytest.mark.asyncio
async def test_connect_denial_closes_without_tls_or_retry():
    stream = TunnelStream(connect_status=403)
    backend = TunnelBackend(stream)
    transport = PinnedProxyTransport(PROXY, backend=backend)
    with pytest.raises(AppError) as caught:
        await fetch_public(SOURCE, resolver=public_resolver, transport=transport)
    assert caught.value.code == "source_connection"
    assert len(backend.connects) == 1 and stream.tls == [] and stream.closed


@pytest.mark.asyncio
async def test_tls_failure_does_not_disable_verification_or_retry():
    stream = TunnelStream(tls_failure=True)
    backend = TunnelBackend(stream)
    transport = PinnedProxyTransport(PROXY, backend=backend)
    with pytest.raises(AppError) as caught:
        await fetch_public(SOURCE, resolver=public_resolver, transport=transport)
    assert caught.value.code == "source_connection"
    assert len(backend.connects) == len(stream.tls) == 1
    assert stream.tls[0]["check_hostname"] is True


@pytest.mark.asyncio
async def test_redirect_private_target_is_rejected_before_second_connect():
    stream = TunnelStream(response=b"HTTP/1.1 302 Found\r\nLocation: https://127.0.0.1/private\r\nContent-Length: 0\r\n\r\n")
    backend = TunnelBackend(stream)
    resolver = GoogleDohResolver(PROXY, transport=httpx.MockTransport(dns_response))
    transport = PinnedProxyTransport(PROXY, backend=backend)
    with pytest.raises(AppError) as caught:
        await fetch_public(SOURCE, resolver=resolver, transport=transport)
    assert caught.value.code == "unsafe_source_url" and len(backend.connects) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("host,port", [("paper.example.test", 443), ("127.0.0.1", 443), (PUBLIC_IP, 80)])
async def test_transport_rejects_unpinned_private_or_wrong_port_before_connect(host, port):
    backend = TunnelBackend(TunnelStream())
    with pytest.raises(httpcore.ConnectError):
        await PinnedProxyBackend(PROXY, backend=backend).connect_tcp(host, port)
    assert backend.connects == []


def test_opt_in_only_and_proxy_credentials_are_not_exposed(monkeypatch):
    assert Settings().research_network_mode == "system"
    assert public_fetch_options("system") == {}
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.delenv("https_proxy", raising=False)
    with pytest.raises(AppError) as absent:
        public_fetch_options("google_doh_egress")
    assert absent.value.code == "research_network_configuration"
    monkeypatch.setenv("HTTPS_PROXY", "http://fixture-user:fixture-secret@test-egress.invalid:8889")
    with pytest.raises(AppError) as invalid:
        public_fetch_options("google_doh_egress")
    assert "fixture-secret" not in str(invalid.value.public())
    with pytest.raises(ValidationError):
        Settings(research_network_mode="automatic_unsafe_fallback")


@pytest.mark.asyncio
async def test_research_service_selects_explicit_network_adapter_before_fetch(settings, monkeypatch):
    import knowledge.research.service as module
    settings = settings.model_copy(update={"research_network_mode": "google_doh_egress"})
    selected = []
    marker = object()
    monkeypatch.setattr(module, "public_fetch_options", lambda mode: selected.append(mode) or {"transport": marker})
    async def stop_after_options(url, **kwargs):
        assert kwargs == {"transport": marker}
        raise AppError(502, "test_stop", "Fixture stops before storage or generation")
    monkeypatch.setattr(module, "fetch_public", stop_after_options)
    service = module.ResearchService(lambda: pytest.fail("No DB call"), settings, None)
    principal = SimpleNamespace(require=lambda _: None)
    with pytest.raises(AppError) as caught:
        await service.fetch(principal, SimpleNamespace(conversation_id=None, url=SOURCE))
    assert caught.value.code == "test_stop" and selected == ["google_doh_egress"]
