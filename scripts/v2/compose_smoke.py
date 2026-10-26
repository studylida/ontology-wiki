"""Build/run an isolated development Compose stack using fixture providers only.

Use an explicit local Docker socket; no credentials from an existing .env or
Docker config are read. Generated secrets and state stay in --state-dir (0600).
No deployment, push, real model request or global Docker cleanup is performed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets
import socket
import stat
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
OPENER = build_opener(ProxyHandler({}))  # Local ephemeral API must not use an egress proxy.


class SmokeFailure(RuntimeError):
    pass


def private_write(path, content):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(content)


def free_ports():
    sockets = [socket.socket() for _ in range(3)]
    try:
        for connection in sockets:
            connection.bind(("127.0.0.1", 0))
        return [connection.getsockname()[1] for connection in sockets]
    finally:
        for connection in sockets:
            connection.close()


def prepare(directory, docker_host):
    if not docker_host.startswith("unix://"):
        raise SmokeFailure("Use an explicit local unix Docker socket")
    try:
        if not stat.S_ISSOCK(Path(docker_host.removeprefix("unix://")).stat().st_mode):
            raise SmokeFailure("Docker endpoint is not a local socket")
    except OSError as exc:
        raise SmokeFailure("A local Docker daemon is required") from exc
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if (directory / "state.json").exists():
        raise SmokeFailure("Existing smoke state must be cleaned up before a new run")
    db_port, api_port, web_port = free_ports()
    state = {"createdBy": "ontology-wiki-compose-smoke-v1", "project": "ow-ci-" + secrets.token_hex(8),
        "dockerHost": docker_host, "dbPort": db_port, "apiPort": api_port, "webPort": web_port,
        "username": "compose-reviewer", "password": secrets.token_urlsafe(24),
        "dbPassword": secrets.token_urlsafe(24), "authSecret": secrets.token_urlsafe(40)}
    values = {"OW_DEV_DB_PASSWORD": state["dbPassword"], "OW_AUTH_SECRET": state["authSecret"],
        "OW_DEV_DB_PORT": db_port, "OW_DEV_API_PORT": api_port, "OW_DEV_WEB_PORT": web_port,
        "OW_PROVIDER_MODE": "fixture", "OW_GENERATION_MODEL": "fixture-generation",
        "OW_GENERATION_EFFORT": "", "OW_EMBEDDING_MODEL": "text-embedding-3-large",
        "OW_EMBEDDING_API_DIMENSIONS": 1536, "OW_EMBEDDING_TRANSFORM": "native",
        "OW_RESEARCH_NETWORK_MODE": "system", "OPENAI_API_KEY": ""}
    private_write(directory / "compose.env", "".join(f"{key}={value}\n" for key, value in values.items()))
    private_write(directory / "state.json", json.dumps(state))
    (directory / "docker-config").mkdir(mode=0o700)
    return state


def load_state(directory):
    path = directory / "state.json"
    if not path.exists():
        return None
    state = json.loads(path.read_text())
    if state.get("createdBy") != "ontology-wiki-compose-smoke-v1" or not re.fullmatch(r"ow-ci-[0-9a-f]{16}", state.get("project", "")):
        raise SmokeFailure("Refusing cleanup of an unrecognized project")
    if not state.get("dockerHost", "").startswith("unix://"):
        raise SmokeFailure("Refusing nonlocal Docker endpoint")
    return state


class Stack:
    def __init__(self, directory, state):
        self.directory, self.state = directory, state
        self.redactions = [state[key] for key in ("password", "dbPassword", "authSecret")]
        # Only inherit process/network necessities. Provider and repository
        # credentials from the caller must not reach Compose or build steps.
        inherited = ("PATH", "LANG", "LC_ALL", "TMPDIR", "TERM", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
                     "http_proxy", "https_proxy", "all_proxy", "no_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR")
        self.environment = {key: os.environ[key] for key in inherited if key in os.environ}
        self.environment.update(DOCKER_HOST=state["dockerHost"], DOCKER_CONFIG=str(directory / "docker-config"),
                                OPENAI_API_KEY="", OW_BOOTSTRAP_PASSWORD=state["password"])
        self.command = ["docker", "compose", "--env-file", str(directory / "compose.env"),
                        "--project-name", state["project"], "--file", str(ROOT / "compose.dev.yml")]
        self.api = f"http://127.0.0.1:{state['apiPort']}/api/v1"
        self.token = None

    def redact(self, value):
        for secret in self.redactions:
            value = value.replace(secret, "[redacted]")
        return value

    def compose(self, *arguments, timeout=120):
        print("compose stage:", " ".join(arguments[:3]), flush=True)
        try:
            result = subprocess.run([*self.command, *arguments], cwd=ROOT, env=self.environment,
                                    capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise SmokeFailure("Compose command exceeded its time budget") from exc
        if result.returncode:
            diagnostic = self.redact((result.stdout + result.stderr)[-10000:])
            raise SmokeFailure(f"Compose exited {result.returncode}: {diagnostic}")
        return result.stdout

    def request(self, method, path, body=None, *, base=None):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        data = json.dumps(body).encode() if body is not None else None
        try:
            with OPENER.open(Request((base or self.api) + path, data=data, headers=headers, method=method), timeout=15) as response:
                return json.load(response)
        except HTTPError as exc:
            detail = self.redact(exc.read(4000).decode("utf-8", errors="replace"))
            raise SmokeFailure(f"HTTP {exc.code} {method} {path}: {detail}") from exc

    def health(self):
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                value = self.request("GET", "/health")
                if value.get("database") == "connected" and value.get("providerMode") == "fixture":
                    return value
            except (SmokeFailure, URLError, TimeoutError, ConnectionError):
                pass
            time.sleep(1)
        raise SmokeFailure("Fixture API did not become healthy")

    def wait_web(self):
        web_base = f"http://127.0.0.1:{self.state['webPort']}"
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                with OPENER.open(web_base, timeout=10) as response:
                    html = response.read(100000).decode()
                if 'id="root"' in html:
                    return web_base
            except (URLError, TimeoutError, ConnectionError):
                pass
            time.sleep(1)
        raise SmokeFailure("Vite web container did not serve the application")

    def events(self, path):
        request = Request(f"http://127.0.0.1:{self.state['apiPort']}" + path,
                          headers={"Authorization": "Bearer " + self.token, "Accept": "text/event-stream"})
        result, data = [], []
        with OPENER.open(request, timeout=30) as response:
            if not response.headers.get("Content-Type", "").startswith("text/event-stream"):
                raise SmokeFailure("Answer endpoint did not return SSE")
            for raw in response:
                line = raw.decode("utf-8").rstrip("\r\n")
                if line.startswith("data:"):
                    data.append(line[5:].lstrip(" "))
                elif not line and data:
                    event = json.loads("\n".join(data))
                    data.clear()
                    if result and event["seq"] <= result[-1]["seq"]:
                        raise SmokeFailure("SSE sequence did not advance")
                    result.append(event)
                    if event["type"] in ("run.completed", "run.failed", "run.cancelled"):
                        break
        if not result or result[-1]["type"] != "run.completed":
            raise SmokeFailure("Fixture answer SSE did not complete successfully")
        return result

    def wait_jobs(self, kinds, timeout=60):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            jobs = self.request("GET", "/jobs")["items"]
            picked = {kind: next((job for job in jobs if job["kind"] == kind), None) for kind in kinds}
            if all(job and job["status"] not in ("pending", "running") for job in picked.values()):
                return picked
            time.sleep(1)
        raise SmokeFailure("Expected jobs did not reach terminal states")


def verify(stack):
    stack.compose("config", "--quiet")
    stack.compose("build", timeout=600)
    stack.compose("up", "-d", "--wait", "db", timeout=90)
    stack.compose("run", "--rm", "--no-deps", "api", "python", "-m", "knowledge.cli",
                  "migrate", "--database-name", "ontology_wiki_dev")
    stack.compose("run", "--rm", "--no-deps", "-e", "OW_BOOTSTRAP_PASSWORD", "api", "python", "-m",
                  "knowledge.cli", "create-user", "--username", stack.state["username"], "--role", "reviewer")
    stack.compose("up", "--no-build", "-d", "api", "worker", "web")
    health = stack.health()
    versions = json.loads(stack.compose("exec", "-T", "db", "psql", "-U", "ontology_dev", "-d", "ontology_wiki_dev", "-Atc",
        "SELECT json_build_object('postgres',current_setting('server_version'),'pgvector',(SELECT extversion FROM pg_extension WHERE extname='vector'))"))
    if not versions.get("pgvector"):
        raise SmokeFailure("pgvector extension was not installed by migration")
    web_base = stack.wait_web()
    if stack.request("GET", "/api/v1/health", base=web_base).get("providerMode") != "fixture":
        raise SmokeFailure("Web-to-API Compose proxy failed")
    login = stack.request("POST", "/auth/login", {"username": stack.state["username"], "password": stack.state["password"]})
    stack.token = login["accessToken"]
    stack.redactions.append(stack.token)
    document = stack.request("POST", "/documents", {"title": "CI fixture — smoke bonding",
        "content": "# Smoke bonding\nCI fixture only. Smoke bonding 정의와 적용 조건을 확인하는 저장·검색 검증 본문입니다. 실제 반도체 지식이 아닙니다.",
        "format": "markdown", "visibility": "shared_candidate", "publisher": "CI fixture",
        "publisherId": "ci-fixture", "sourceType": "fixture", "attributionBasis": "explicit_ci_fixture"})
    revision = document["currentRevisionId"]
    approved = stack.request("POST", f"/documents/revisions/{revision}/review",
        {"decision": "approve", "reason": "Isolated CI fixture; not production or expert approval"})
    if approved["reviewStatus"] != "approved" or approved["indexStatus"] == "ready":
        raise SmokeFailure("Document approval and indexing state were conflated")
    stack.request("POST", "/index-jobs", {"sourceRevisionIds": [revision], "immediate": True})
    index = stack.wait_jobs(["index"])["index"]
    if index["status"] != "succeeded":
        raise SmokeFailure("Fixture indexing did not succeed")
    source = stack.request("GET", f"/documents/revisions/{revision}")
    if source["indexStatus"] != "ready" or not source["passages"]:
        raise SmokeFailure("Source revision/passages were not retrievable after indexing")
    conversation = stack.request("POST", "/conversations", {"title": "Compose smoke fixture"})
    if conversation["nextSettings"].get("responseMode") != "wiki" or conversation["nextSettings"].get("extended") is not False:
        raise SmokeFailure("New conversation defaults changed")
    payload = {"clientRequestId": str(uuid4()), "conversationId": conversation["id"],
        "message": "Smoke bonding 정의와 적용 조건을 설명해 주세요.", "responseMode": "wiki", "extended": False,
        "sourceRevisionIds": [revision]}
    run = stack.request("POST", "/answer-runs", payload)
    events = stack.events(run["eventsUrl"])
    kinds = {event["type"] for event in events}
    if not {"run.started", "retrieval.status", "text.delta", "citation.add", "run.completed"}.issubset(kinds):
        raise SmokeFailure("Required SSE lifecycle/evidence events were missing")
    body = "".join(event["data"]["text"] for event in events if event["type"] == "text.delta")
    saved = stack.request("GET", f"/answer-runs/{run['runId']}")
    if saved["status"] != "completed" or saved["message"]["content"] != body or "fixture" not in body.lower():
        raise SmokeFailure("Actual fixture deltas and persisted answer differ")
    if saved["usage"]["calls"] != 0 or saved["usage"].get("costStatus") != "fixture":
        raise SmokeFailure("Fixture execution was reported as a live provider call")
    if not any(citation["sourceRevisionId"] == revision for citation in saved["message"]["citations"]):
        raise SmokeFailure("Saved answer lost its original source revision")
    same = stack.request("POST", "/answer-runs", payload)
    if same["runId"] != run["runId"]:
        raise SmokeFailure("Idempotent submission started another run")
    stack.compose("restart", "api")
    stack.health()
    restored = stack.request("GET", f"/conversations/{conversation['id']}")
    restored_message = next((message for message in restored["messages"] if message["id"] == run["messageId"]), None)
    if not restored_message or restored_message["content"] != body or len(restored["messages"]) != 2:
        raise SmokeFailure("Conversation did not restore after API restart")
    replay = stack.events(run["eventsUrl"] + "?after=0")
    if [(e["seq"], e["type"], e["data"]) for e in replay] != [(e["seq"], e["type"], e["data"]) for e in events]:
        raise SmokeFailure("Durable SSE replay differed after API restart")
    structured = stack.wait_jobs(["ontology_extract", "personal_wiki"])
    for kind, job in structured.items():
        if job["status"] != "failed" or (job.get("error") or {}).get("code") != "structured_output_invalid":
            raise SmokeFailure(f"{kind}: fixture JSON failure must be explicit, not a fabricated success")
        if (job.get("usage") or {}).get("calls") != 0:
            raise SmokeFailure(f"{kind}: fixture was counted as an external model call")
    if stack.request("GET", "/personal-wiki")["items"]:
        raise SmokeFailure("Fixture JSON failure created a fake personal wiki page")
    return {"status": "passed", "scope": "container_execution_with_fixture_provider",
        "database": versions, "health": health, "webServed": True, "webApiProxy": True,
        "documentApprovedAndIndexed": True, "sourceRevisionReadable": True,
        "sseEventCount": len(events), "sseReplayAfterApiRestart": True,
        "conversationRestoredAfterApiRestart": True, "idempotentSubmission": True,
        "externalModelCalls": 0, "semanticQualityEvaluated": False,
        "structuredFixtureJobs": {kind: {"status": job["status"], "errorCode": job["error"]["code"]}
                                  for kind, job in structured.items()},
        "structuredGenerationSuccessVerified": False}


def write_report(directory, result):
    (directory / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write("## Isolated Compose smoke\n\n```json\n" + json.dumps(result, ensure_ascii=False, indent=2) + "\n```\n")


def main(args):
    directory = Path(args.state_dir).resolve()
    if args.command == "cleanup":
        state = load_state(directory)
        if state:
            Stack(directory, state).compose("down", "--volumes", "--remove-orphans", timeout=90)
            for name in ("state.json", "compose.env"):
                (directory / name).unlink(missing_ok=True)
        return 0
    state = prepare(directory, args.docker_host)
    stack = Stack(directory, state)
    try:
        result = verify(stack)
    except Exception as exc:
        result = {"status": "failed", "scope": "container_execution_with_fixture_provider",
                  "errorType": type(exc).__name__, "message": stack.redact(str(exc)),
                  "externalModelCalls": 0, "semanticQualityEvaluated": False}
    result["checkedAt"] = datetime.now(timezone.utc).isoformat()
    write_report(directory, result)
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "cleanup"))
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--docker-host", default="unix:///var/run/docker.sock")
    raise SystemExit(main(parser.parse_args()))
