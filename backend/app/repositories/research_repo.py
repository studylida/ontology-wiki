"""Stored literature and public Crossref metadata I/O. Never manufacture results."""
from pathlib import Path
import asyncio
from datetime import datetime
from hashlib import sha256
import ipaddress
import socket
import httpx
from sqlalchemy import select, update
from backend.app.models.entities import ResearchSessionModel, EvidenceSourceModel
from backend.app.core.cache import cache_manager


class ResearchConflict(RuntimeError):
    pass


class ResearchRepository:
    async def get(self, db, session_id):
        return await db.get(ResearchSessionModel, session_id)

    async def list(self, db, limit):
        result = await db.execute(select(ResearchSessionModel).order_by(
            ResearchSessionModel.created_at.desc()).limit(limit))
        return list(result.scalars())

    async def evidences(self, db):
        result = await db.execute(select(EvidenceSourceModel))
        return list(result.scalars())

    def source_documents(self):
        root = Path(__file__).resolve().parents[3] / "sources"
        for path in sorted(root.rglob("*.md")):
            # Only the configured source tree is readable, including through symlinks.
            if path.resolve().is_relative_to(root.resolve()):
                yield path.relative_to(root).as_posix(), path.read_text(encoding="utf-8-sig")

    async def crossref(self, query):
        key = "research:crossref:" + sha256(query.casefold().strip().encode()).hexdigest()
        cached = await cache_manager.get(key)
        if cached is not None:
            return cached
        blocked = await cache_manager.get("research:crossref:retry")
        if blocked:
            raise ValueError("crossref_rate_limited")
        async with httpx.AsyncClient(timeout=12, headers={"User-Agent": "OntologyWiki/1.0"}) as client:
            response = await client.get("https://api.crossref.org/works", params={
                "query.bibliographic": query, "rows": 8, "sort": "score"})
            if response.status_code == 429:
                retry = response.headers.get("retry-after", "60")
                await cache_manager.set("research:crossref:retry", True, min(300, max(30, int(retry) if retry.isdigit() else 60)))
            response.raise_for_status()
            items = response.json()["message"]["items"]
            await cache_manager.set(key, items, 300)
            return items

    async def fetch_public(self, url):
        """Bounded HTTPS fetch, pinning validated DNS addresses including redirects."""
        for _ in range(5):
            target = httpx.URL(url)
            host = target.host
            if target.scheme != "https" or target.port not in {None, 443} or target.username or target.password or not host:
                raise ValueError("unsafe_public_url")
            addresses = await asyncio.get_running_loop().getaddrinfo(host, 443, type=socket.SOCK_STREAM)
            ips = list(dict.fromkeys(entry[4][0] for entry in addresses))
            if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
                raise ValueError("unsafe_public_address")
            blocked_key = "research:retry:" + sha256(str(target).encode()).hexdigest()
            if await cache_manager.get(blocked_key):
                raise ValueError("retry_later")
            # Pin DNS to prevent a hostname changing to a private address during connection.
            async with httpx.AsyncClient(timeout=12, trust_env=False) as client:
                async with client.stream("GET", target.copy_with(host=ips[0]),
                        headers={"Host": host, "User-Agent": "OntologyWiki/1.0", "Accept-Encoding": "identity"},
                        extensions={"sni_hostname": host}) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        url = str(target.join(response.headers.get("location", "")))
                        continue
                    if response.status_code == 429:
                        retry = response.headers.get("retry-after", "60")
                        await cache_manager.set(blocked_key, True, min(300, max(30, int(retry) if retry.isdigit() else 60)))
                    response.raise_for_status()
                    if response.headers.get("content-encoding", "identity").casefold() != "identity":
                        raise ValueError("unsupported_encoding")
                    kind = response.headers.get("content-type", "").split(";")[0].lower()
                    if kind not in {"text/html", "application/xhtml+xml", "application/pdf", "text/plain"}:
                        raise ValueError("unsupported_content_type")
                    body = bytearray()
                    async for chunk in response.aiter_raw():
                        body.extend(chunk)
                        if len(body) > 5_000_000:
                            raise ValueError("content_too_large")
                    return bytes(body), kind, str(target)
        raise ValueError("too_many_redirects")

    async def checkpoint(self, db, session, feed, report, notice, candidates=None):
        stamp = datetime.utcnow()
        values = dict(evidence_feed=feed, synthesis_report=report, trust_pool_notice=notice, updated_at=stamp)
        if candidates is not None:
            values["candidates"] = candidates
        result = await db.execute(update(ResearchSessionModel).where(
            ResearchSessionModel.id == session.id, ResearchSessionModel.updated_at == session.updated_at
        ).values(**values)
            .execution_options(synchronize_session=False))
        if result.rowcount != 1:
            raise ResearchConflict("조사 내용이 변경됐습니다. 최신 세션을 열어 다시 시도해 주세요.")

    def add(self, db, session):
        db.add(session)


research_repo = ResearchRepository()
