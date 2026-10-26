"""Verify actual public fetching without a DB, model call or config change.

The default exercises system DNS. The explicit google-doh-egress diagnostic uses
the same opt-in adapter as ResearchService: Google DoH A+AAAA validation, the
environment's HTTP proxy, public-IP CONNECT, original Host/SNI and verified TLS.
No failed endpoint is retried through a different route.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from knowledge.core.errors import AppError
from knowledge.integrations.public_egress import GoogleDohResolver, PinnedProxyTransport
from knowledge.integrations.public_fetch import fetch_public, parse_download


async def verify(args):
    result = {"operation": "public_fetch_and_parse", "checkedAt": datetime.now(timezone.utc).isoformat(),
        "mode": args.network, "url": args.url, "modelCalls": 0, "databaseWrites": False,
        "productNetworkConfigurationChanged": False, "dnsQueries": [], "connections": []}
    try:
        if args.network == "google-doh-egress":
            proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
            if not proxy:
                raise AppError(503, "research_network_configuration", "환경 egress 프록시가 설정되지 않았습니다.")
            resolver = GoogleDohResolver(proxy, audit=result["dnsQueries"])
            transport = PinnedProxyTransport(proxy, audit=result["connections"])
            raw, media_type, final_url = await fetch_public(args.url, resolver=resolver, transport=transport)
        else:
            raw, media_type, final_url = await fetch_public(args.url)
        os.environ["PYTHONPATH"] = str(ROOT / "backend")
        parsed = await parse_download(raw, media_type)
        result.update(status="passed", finalUrl=final_url, bytes=len(raw), mediaType=media_type,
            bodySha256=sha256(raw).hexdigest(), title=parsed["title"],
            readScope=parsed["readScope"], extractedCharacters=len(parsed["content"]),
            limitations=parsed["limitations"])
    except AppError as exc:
        result.update(status="blocked" if exc.code in ("source_dns_unavailable", "research_network_configuration") else "failed",
                      error={"httpStatus": exc.status_code, **exc.public()})
    except Exception as exc:
        result.update(status="failed", error={"type": type(exc).__name__})
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result["status"] == "passed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--network", choices=("system", "google-doh-egress"), default="system")
    parser.add_argument("--output")
    raise SystemExit(0 if asyncio.run(verify(parser.parse_args())) else 1)
