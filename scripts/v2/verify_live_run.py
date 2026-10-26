"""Explicit, single paid-answer verification against a local development API.

Requires --allow-live, an existing app user, OW_LIVE_PASSWORD, and a configured
local server. Never reads provider credentials, retries generation, or runs in
pytest. Each invocation submits exactly one answer request and saves its actual
stream/final state. Keep private or operational questions out of public reports.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from urllib.parse import urlsplit
from uuid import uuid4

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-live", action="store_true", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--mode", choices=["wiki", "analysis"], default="wiki")
    parser.add_argument("--extended", action="store_true")
    parser.add_argument("--conversation-id")
    parser.add_argument("--source-revision", action="append", default=[])
    parser.add_argument("--concept", action="append", default=[])
    parser.add_argument("--publisher", action="append", default=[])
    parser.add_argument("--attachment", action="append", default=[])
    parser.add_argument("--disable-auto-wiki", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = urlsplit(args.base_url)
    if target.scheme != "http" or target.hostname not in ("127.0.0.1", "localhost"):
        parser.error("Live verification is restricted to the local development API")
    password = os.environ.get("OW_LIVE_PASSWORD")
    if not password:
        parser.error("Set OW_LIVE_PASSWORD privately; it is never written to the report")
    report = {"checkedAt": datetime.now(timezone.utc).isoformat(), "scope": "explicit_live_development_run",
              "question": args.question, "responseMode": args.mode, "extended": args.extended,
              "automaticRetry": False}
    with httpx.Client(base_url=args.base_url, timeout=httpx.Timeout(180, connect=10)) as client:
        health = client.get("/api/v1/health")
        health.raise_for_status()
        status = health.json()
        if status.get("providerMode") != "live" or status.get("generationModel") != "gpt-6-luna":
            raise SystemExit("Expected explicitly configured live gpt-6-luna; no answer submitted")
        auth = client.post("/api/v1/auth/login", json={"username": args.username, "password": password})
        auth.raise_for_status()
        client.headers["Authorization"] = "Bearer " + auth.json()["accessToken"]
        conversation_id = args.conversation_id
        if not conversation_id:
            created = client.post("/api/v1/conversations", json={"title": args.question[:120]})
            created.raise_for_status()
            conversation_id = created.json()["id"]
        if args.disable_auto_wiki:
            update = client.patch(f"/api/v1/conversations/{conversation_id}", json={"autoWiki": False})
            update.raise_for_status()
        request = {"clientRequestId": str(uuid4()), "conversationId": conversation_id,
                   "message": args.question, "responseMode": args.mode, "extended": args.extended,
                   "sourceRevisionIds": args.source_revision, "conceptIds": args.concept,
                   "sourceGroups": [{"groupId": f"publisher:{p}", "publisherId": p} for p in args.publisher],
                   "attachmentIds": args.attachment}
        report["request"] = request
        started = time.perf_counter()
        submitted = client.post("/api/v1/answer-runs", json=request)
        submitted.raise_for_status()
        run_id = submitted.json()["runId"]
        report.update(runId=run_id, conversationId=conversation_id)
        event_counts, sequence, chunks, first_text_ms, terminal = Counter(), [], [], None, None
        try:
            with client.stream("GET", f"/api/v1/answer-runs/{run_id}/events") as response:
                response.raise_for_status()
                data = []
                for line in response.iter_lines():
                    if line.startswith("data:"):
                        data.append(line[5:].lstrip())
                    elif not line and data:
                        event = json.loads("\n".join(data))
                        data = []
                        event_counts[event["type"]] += 1
                        sequence.append(event["seq"])
                        if event["type"] == "text.delta" and event["data"].get("text"):
                            if first_text_ms is None:
                                first_text_ms = (time.perf_counter() - started) * 1000
                            chunks.append(event["data"]["text"])
                        if event["type"] in ("run.completed", "run.failed", "run.cancelled"):
                            terminal = event["type"]
                            break
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            report["streamError"] = type(exc).__name__
        final = client.get(f"/api/v1/answer-runs/{run_id}")
        final.raise_for_status()
        report.update(final=final.json(), stream={"eventCounts": dict(event_counts),
            "firstTextObservedMs": first_text_ms, "elapsedMs": (time.perf_counter() - started) * 1000,
            "strictlyIncreasingSequence": all(a < b for a, b in zip(sequence, sequence[1:])),
            "terminal": terminal, "text": "".join(chunks)})
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"runId": run_id, "conversationId": conversation_id,
            "status": report["final"].get("status"), "eventCounts": dict(event_counts),
            "firstTextObservedMs": first_text_ms, "report": str(args.output)}, ensure_ascii=False))
        if report["final"].get("status") != "completed":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
