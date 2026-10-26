import socket

import httpx
import pytest

from knowledge.core.errors import AppError
from knowledge.integrations.public_fetch import fetch_public, resolve_public_url


@pytest.mark.asyncio
async def test_dns_failure_is_retryable_infrastructure_error_not_unsafe_url(monkeypatch):
    import socket
    def unavailable(*args, **kwargs):
        raise socket.gaierror("test DNS unavailable")
    monkeypatch.setattr(socket, "getaddrinfo", unavailable)
    with pytest.raises(AppError) as caught:
        await resolve_public_url("https://example.org/literature")
    assert caught.value.status_code == 502
    assert caught.value.code == "source_dns_unavailable"
    assert caught.value.retryable is True


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["http://example.com", "https://user:pass@example.com", "https://example.com:444/a", "https://127.0.0.1", "https://[::1]/"])
async def test_rejects_nonpublic_or_credential_urls(url):
    with pytest.raises(AppError):
        await resolve_public_url(url)


@pytest.mark.asyncio
async def test_rejects_mixed_public_private_dns(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.1.1.1", 443))])
    with pytest.raises(AppError):
        await resolve_public_url("https://example.test/")


@pytest.mark.asyncio
async def test_redirect_revalidates_destination_and_pins_host():
    calls = []
    async def resolver(url):
        if url.endswith("private"):
            raise AppError(422, "unsafe_source_url", "blocked")
        return "https://8.8.8.8/paper", "example.test"
    def handle(request):
        calls.append(request)
        assert request.url.host == "8.8.8.8" and request.headers["host"] == "example.test"
        assert request.extensions["sni_hostname"] == "example.test"
        return httpx.Response(302, headers={"Location": "https://example.test/private"})
    with pytest.raises(AppError):
        await fetch_public("https://example.test/paper", resolver=resolver, transport=httpx.MockTransport(handle))
    assert len(calls) == 1
