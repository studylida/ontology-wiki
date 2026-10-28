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
        "username": "compose-employee", "password": secrets.token_urlsafe(24),
        "dbPassword": secrets.token_urlsafe(24), "authSecret": secrets.token_urlsafe(40)}
    values = {"OW_DEV_DB_PASSWORD": state["dbPassword"], "OW_AUTH_SECRET": state["authSecret"],
        "OW_DEV_DB_PORT": db_port, "OW_DEV_API_PORT": api_port, "OW_DEV_WEB_PORT": web_port,
        "OW_PROVIDER_MODE": "fixture", "OW_GENERATION_MODEL": "fixture-generation",
        "OW_GENERATION_EFFORT": "", "OW_EMBEDDING_MODEL": "text-embedding-3-large",
        "OW_EMBEDDING_API_DIMENSIONS": 1536, "OW_EMBEDDING_TRANSFORM": "native",
        "OPENAI_API_KEY": ""}
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
                    if event["type"] == "stream_error":
                        raise SmokeFailure("SSE access or storage error")
                    if result and event["seq"] <= result[-1]["seq"]:
                        raise SmokeFailure("SSE sequence did not advance")
                    result.append(event)
                    if event["type"] in ("complete", "error", "cancelled", "interrupted"):
                        break
        if not result or result[-1]["type"] != "complete":
            raise SmokeFailure("Fixture answer SSE did not complete successfully")
        return result

    def upload(self, content):
        boundary = "smoke-" + uuid4().hex
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="title"\r\n\r\nSmoke fixture\r\n'
                f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="fixture.md"\r\n'
                'Content-Type: text/markdown\r\n\r\n').encode() + content + f'\r\n--{boundary}--\r\n'.encode()
        request = Request(self.api + '/documents', data=body, method='POST', headers={
            'Authorization': 'Bearer ' + self.token, 'Content-Type': 'multipart/form-data; boundary=' + boundary})
        with OPENER.open(request, timeout=20) as response:
            if response.status != 202:
                raise SmokeFailure('Upload was not accepted')
            return json.load(response)

    def wait_document(self, document_id):
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            document = self.request('GET', '/documents/' + document_id)
            if document['status'] in ('ready', 'partial', 'failed', 'inactive'):
                if not document['searchable']:
                    raise SmokeFailure('Document did not become searchable')
                return document
            time.sleep(.2)
        raise SmokeFailure('Document worker did not finish')


def verify(stack):
    stack.compose("config", "--quiet")
    stack.compose("build", timeout=600)
    stack.compose("up", "-d", "--wait", "db", timeout=90)
    stack.compose("run", "--rm", "--no-deps", "api", "python", "-m", "knowledge.cli",
                  "migrate", "--database-name", "ontology_wiki_dev")
    stack.compose("run", "--rm", "--no-deps", "-e", "OW_BOOTSTRAP_PASSWORD", "api", "python", "-m",
                  "knowledge.cli", "create-user", "--username", stack.state["username"], "--role", "user")
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
    raw = b'# Smoke fixture\n\nSynthetic alpha material is measured at 250 C for 30 min. Not company knowledge.\n'
    accepted = stack.upload(raw)
    source = stack.wait_document(accepted['documentId'])
    original = Request(stack.api + '/documents/' + source['id'] + '/raw', headers={'Authorization': 'Bearer ' + stack.token})
    with OPENER.open(original, timeout=10) as response:
        if response.read() != raw:
            raise SmokeFailure('Raw source changed')
    conv = stack.request('POST', '/conversations', {'title': 'Isolated smoke'})
    run_ids = []
    for question in ('Explain the alpha material conditions.', 'Which temperature was used?'):
        run = stack.request('POST', '/conversations/' + conv['id'] + '/turns',
                            {'question': question, 'requestId': uuid4().hex})
        stack.events(run['eventsUrl'])
        saved = stack.request('GET', '/answer-runs/' + run['runId'])
        if saved['status'] != 'completed' or not saved['answer']['citations']:
            raise SmokeFailure('Fixture answer did not persist evidence')
        citation = saved['answer']['citations'][0]
        content = stack.request('GET', '/documents/' + citation['documentId'] + '/passages?revisionId=' + citation['sourceRevisionId'])
        if citation['passageId'] not in {p['id'] for p in content['passages']}:
            raise SmokeFailure('Citation did not resolve')
        run_ids.append(run['runId'])
    transcript = stack.request('GET', '/conversations/' + conv['id'])
    if len(transcript['messages']) != 4:
        raise SmokeFailure('Follow-up transcript was not restored')
    stack.request('POST', '/documents/' + source['id'] + '/deactivate')
    redacted = stack.request('GET', '/conversations/' + conv['id'])
    if not all(m['sourceUnavailable'] and not m['content'] for m in redacted['messages'] if m['role'] == 'assistant'):
        raise SmokeFailure('Withdrawn evidence remained visible')
    return {'status': 'passed', 'providerMode': health['providerMode'], 'versions': versions,
            'documentId': source['id'], 'answerRunIds': run_ids,
            'checks': ['fresh_migrations', 'employee_upload', 'automatic_worker_index', 'raw_integrity',
                       'web_proxy', 'answer_events', 'citation_resolution', 'followup_restore', 'withdrawal'],
            'limitations': ['fixture providers; no live model quality evaluation', 'HTTP smoke, not browser interaction']}


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
