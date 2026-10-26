"""Explicit public DoH + pinned CONNECT adapter for proxy-only environments.

This is selected only by research_network_mode=google_doh_egress. The system-DNS
path remains the default. Resolver/proxy failures never weaken public-IP checks
or fall back to a different destination. No proxy URL or credentials are logged.
"""
from __future__ import annotations

import asyncio
import ipaddress
import os
from urllib.parse import urlsplit, urlunsplit

import httpcore
import httpx

from knowledge.core.errors import AppError
from knowledge.integrations.public_fetch import validate_public_target

DOH_URL = "https://dns.google/resolve"


def _proxy_settings(proxy_url):
    try:
        proxy = urlsplit(proxy_url)
        if proxy.scheme != "http" or not proxy.hostname or proxy.username or proxy.password:
            raise ValueError()
        return proxy.hostname, proxy.port or 80
    except (ValueError, TypeError) as exc:
        raise AppError(503, "research_network_configuration", "지원되는 HTTP egress 프록시 설정을 확인하세요.") from exc


class GoogleDohResolver:
    def __init__(self, proxy_url, *, audit=None, transport=None):
        _proxy_settings(proxy_url)
        self.proxy_url, self.audit, self.transport = proxy_url, audit, transport

    async def __call__(self, url):
        parsed, hostname, literal = validate_public_target(url)
        if literal is not None:
            addresses = [str(literal)]
        else:
            addresses = []
            connection = {"transport": self.transport} if self.transport is not None else {"proxy": self.proxy_url}
            try:
                # Honor the environment's trusted CA bundle without inheriting
                # proxy routing or allowing certificate/hostname checks off.
                tls = httpx.create_ssl_context(verify=True, trust_env=True)
                async with httpx.AsyncClient(timeout=20, follow_redirects=False, trust_env=False,
                                             verify=tls, **connection) as client:
                    for record_type, number in (("A", 1), ("AAAA", 28)):
                        response = await client.get(DOH_URL, params={"name": hostname, "type": record_type,
                            "cd": "false", "edns_client_subnet": "0.0.0.0/0"})
                        entry = {"hostname": hostname, "type": record_type, "httpStatus": response.status_code}
                        if self.audit is not None:
                            self.audit.append(entry)
                        if response.status_code != 200:
                            raise AppError(502, "source_dns_unavailable", "공식 DoH 응답을 확인하지 못했습니다.", retryable=True)
                        raw = response.json()
                        expected = [{"name": hostname.rstrip(".").casefold(), "type": number}]
                        questions = [{"name": str(q.get("name", "")).rstrip(".").casefold(), "type": q.get("type")}
                                     for q in raw.get("Question", [])]
                        entry.update(dnsStatus=raw.get("Status"), truncated=raw.get("TC"), dnssecValidated=raw.get("AD"))
                        if raw.get("Status") != 0 or raw.get("TC") or raw.get("CD") or questions != expected:
                            raise AppError(502, "source_dns_response_invalid", "DNS 응답의 질문·상태를 확인할 수 없습니다.", retryable=True)
                        answers = [str(row["data"]) for row in raw.get("Answer", []) if row.get("type") in (1, 28)]
                        entry["addresses"] = answers
                        for value in answers:
                            try:
                                valid = ipaddress.ip_address(value).is_global
                            except ValueError:
                                valid = False
                            if not valid:
                                raise AppError(422, "unsafe_source_url", "DNS 응답에 공개 주소가 아닌 대상이 있습니다.")
                        addresses.extend(answers)
            except httpx.HTTPError as exc:
                raise AppError(502, "source_dns_unavailable", "공식 DoH 서버에 연결하지 못했습니다.", retryable=True) from exc
            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                raise AppError(502, "source_dns_response_invalid", "DNS 응답을 읽지 못했습니다.", retryable=True) from exc
        if not addresses:
            raise AppError(502, "source_dns_unavailable", "공개 A·AAAA 주소를 확보하지 못했습니다.", retryable=True)
        # Prefer IPv4 only after validating every returned A and AAAA address.
        address = next((a for a in addresses if ipaddress.ip_address(a).version == 4), addresses[0])
        authority = f"[{address}]" if ":" in address else address
        return urlunsplit(("https", authority, parsed.path or "/", parsed.query, "")), hostname


class PinnedProxyBackend(httpcore.AsyncNetworkBackend):
    """CONNECT is addressed to a validated IP; DNS never shifts to the proxy."""

    def __init__(self, proxy_url, *, audit=None, backend=None):
        self.proxy_host, self.proxy_port = _proxy_settings(proxy_url)
        self.audit = audit
        self.backend = backend or httpcore.AnyIOBackend()

    async def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        try:
            valid = ipaddress.ip_address(host).is_global and port == 443
        except ValueError:
            valid = False
        if not valid:
            raise httpcore.ConnectError("Public egress requires a validated public IP on 443")
        stream = await self.backend.connect_tcp(self.proxy_host, self.proxy_port, timeout=timeout)
        authority = f"[{host}]" if ":" in host else host
        entry = {"connectAuthority": f"{authority}:{port}"}
        if self.audit is not None:
            self.audit.append(entry)
        try:
            await stream.write(f"CONNECT {authority}:{port} HTTP/1.1\r\nHost: {authority}:{port}\r\n\r\n".encode(), timeout=timeout)
            header = bytearray()
            while not header.endswith(b"\r\n\r\n"):
                chunk = await stream.read(1, timeout=timeout)
                if not chunk or len(header) >= 16384:
                    raise httpcore.ProxyError("Incomplete or oversized CONNECT response")
                header.extend(chunk)
            status = bytes(header).split(b"\r\n", 1)[0].decode("ascii", errors="replace")
            entry["statusLine"] = status
            pieces = status.split(" ", 2)
            if len(pieces) < 2 or pieces[1] != "200":
                raise httpcore.ProxyError("Egress proxy did not allow the pinned CONNECT target")
            return stream
        except BaseException:
            await stream.aclose()
            raise

    async def sleep(self, seconds):
        await asyncio.sleep(seconds)


class _ResponseStream(httpx.AsyncByteStream):
    def __init__(self, stream):
        self.stream = stream

    async def __aiter__(self):
        try:
            async for chunk in self.stream:
                yield chunk
        except (httpcore.NetworkError, httpcore.TimeoutException, httpcore.ProtocolError) as exc:
            raise httpx.TransportError(type(exc).__name__) from exc

    async def aclose(self):
        await self.stream.aclose()


class PinnedProxyTransport(httpx.AsyncBaseTransport):
    """Use the ordinary TLS connection's original-host SNI and verification.

The standard httpcore proxy path currently uses URL.host as TLS hostname. An IP
URL therefore needs a CONNECT network backend for the ordinary connection path
to honor sni_hostname. All APIs used here are public httpcore transport APIs.
"""

    def __init__(self, proxy_url, *, audit=None, backend=None):
        self.audit = audit
        self.pool = httpcore.AsyncConnectionPool(
            network_backend=PinnedProxyBackend(proxy_url, audit=audit, backend=backend),
            ssl_context=httpx.create_ssl_context(verify=True, trust_env=True),
            max_connections=1, max_keepalive_connections=0)

    async def handle_async_request(self, request):
        hostname = request.extensions.get("sni_hostname")
        if not hostname or request.headers.get("host") != hostname:
            raise httpx.TransportError("Original Host and TLS SNI must agree")
        entry = {"requestHost": request.url.host, "hostHeader": hostname,
                 "tlsServerName": hostname, "tlsCertificateVerification": True}
        if self.audit is not None:
            self.audit.append(entry)
        core_request = httpcore.Request(method=request.method,
            url=httpcore.URL(scheme=request.url.raw_scheme, host=request.url.raw_host,
                             port=request.url.port, target=request.url.raw_path),
            headers=request.headers.raw, content=request.stream, extensions=request.extensions)
        try:
            response = await self.pool.handle_async_request(core_request)
        except (httpcore.NetworkError, httpcore.TimeoutException, httpcore.ProtocolError, httpcore.ProxyError) as exc:
            entry["errorType"] = type(exc).__name__
            raise httpx.TransportError(type(exc).__name__) from exc
        entry["httpStatus"] = response.status
        return httpx.Response(response.status, headers=response.headers,
                              stream=_ResponseStream(response.stream), extensions=response.extensions)

    async def aclose(self):
        await self.pool.aclose()


def public_fetch_options(mode):
    if mode == "system":
        return {}
    if mode != "google_doh_egress":
        raise AppError(503, "research_network_configuration", "문헌 확보 네트워크 설정을 확인하세요.")
    proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if not proxy_url:
        raise AppError(503, "research_network_configuration", "문헌 확보 egress 설정이 필요합니다.")
    return {"resolver": GoogleDohResolver(proxy_url), "transport": PinnedProxyTransport(proxy_url)}
