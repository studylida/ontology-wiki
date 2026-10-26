"""Bounded public HTTPS fetch, with DNS pinning and validation at every redirect."""
from __future__ import annotations

import asyncio
import ipaddress
import json
import os
import socket
import sys
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx

from knowledge.core.errors import AppError

MAX_BYTES = 5 * 1024 * 1024


def validate_public_target(url: str):
    """Validate the original HTTPS authority before either resolver does I/O."""
    try:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
            raise ValueError()
        hostname = parsed.hostname.encode("idna").decode("ascii")
        try:
            literal = ipaddress.ip_address(hostname)
        except ValueError:
            literal = None
        if literal is not None and not literal.is_global:
            raise ValueError()
        return parsed, hostname, literal
    except (ValueError, UnicodeError) as exc:
        raise AppError(422, "unsafe_source_url", "공개 HTTPS 문헌 주소만 가져올 수 있습니다.") from exc


async def resolve_public_url(url: str):
    parsed, hostname, literal = validate_public_target(url)
    try:
        if literal is not None:
            ips = [str(literal)]
        else:
            addresses = await asyncio.wait_for(asyncio.to_thread(socket.getaddrinfo, hostname, 443, type=socket.SOCK_STREAM), timeout=10)
            ips = sorted({row[4][0] for row in addresses})
        if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
            raise ValueError()
    except (OSError, asyncio.TimeoutError) as exc:
        raise AppError(502, "source_dns_unavailable", "문헌 서버 주소를 확인하지 못했습니다. 잠시 후 다시 시도하세요.", retryable=True) from exc
    except (ValueError, UnicodeError) as exc:
        raise AppError(422, "unsafe_source_url", "공개 HTTPS 문헌 주소만 가져올 수 있습니다.") from exc
    ip = ips[0]
    authority = f"[{ip}]" if ":" in ip else ip
    pinned_url = urlunsplit(("https", authority, parsed.path or "/", parsed.query, ""))
    return pinned_url, hostname


async def fetch_public(url: str, *, transport=None, resolver=resolve_public_url):
    # trust_env=False prevents proxy routing from defeating the public-IP pin.
    async with httpx.AsyncClient(timeout=20, follow_redirects=False, trust_env=False, transport=transport) as client:
        current = url
        for hop in range(4):
            pinned, hostname = await resolver(current)
            try:
                async with client.stream("GET", pinned, headers={"Host": hostname,
                    "User-Agent": "OntologyKnowledge/1.0 (explicit user literature fetch)",
                    "Accept": "text/html,application/pdf,text/plain,text/markdown"},
                    extensions={"sni_hostname": hostname}) as response:
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("location")
                        if not location or hop == 3:
                            raise AppError(422, "redirect_limit", "문헌 주소의 이동 횟수가 제한을 넘었습니다.")
                        current = urljoin(current, location)
                        continue
                    if response.status_code != 200:
                        raise AppError(502, "source_unavailable", "문헌 본문을 가져오지 못했습니다.",
                                       details={"upstreamStatus": response.status_code})
                    length = response.headers.get("content-length")
                    if length and int(length) > MAX_BYTES:
                        raise AppError(413, "source_too_large", "첫 버전의 문헌 다운로드 한도는 5MB입니다.")
                    media_type = response.headers.get("content-type", "").split(";")[0].lower()
                    if media_type not in ("text/html", "application/pdf", "text/plain", "text/markdown", "application/xhtml+xml"):
                        raise AppError(422, "unsupported_source_type", "HTML·PDF·텍스트 문헌만 가져올 수 있습니다.")
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_BYTES:
                            raise AppError(413, "source_too_large", "문헌이 다운로드 한도를 넘었습니다.")
                    return bytes(body), media_type, current
            except httpx.HTTPError as exc:
                raise AppError(502, "source_connection", "문헌 서버에 연결하지 못했습니다.", retryable=True) from exc
    raise AppError(422, "redirect_limit", "문헌 주소 이동을 완료하지 못했습니다.")


async def parse_download(body: bytes, media_type: str):
    env = {key: value for key, value in os.environ.items() if key in ("PATH", "PYTHONPATH", "LANG", "LC_ALL")}
    proc = await asyncio.create_subprocess_exec(sys.executable, "-m", "knowledge.integrations.parse_document", media_type,
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, env=env)
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(body), timeout=12)
    except asyncio.TimeoutError as exc:
        proc.kill()
        await proc.wait()
        raise AppError(422, "source_parse_timeout", "문헌 해석 시간이 제한을 넘었습니다.") from exc
    if proc.returncode != 0:
        raise AppError(422, "source_parse_failed", "문헌 본문을 안전하게 추출하지 못했습니다.")
    return json.loads(stdout)
