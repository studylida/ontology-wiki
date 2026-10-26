"""Verify CI isolation guards locally; this does not run Docker or claim it did."""
import importlib.util
from io import BytesIO
import json
import os
from pathlib import Path
import socket
import stat
from types import SimpleNamespace

import pytest

path = Path(__file__).resolve().parents[2] / "scripts/v2/compose_smoke.py"
spec = importlib.util.spec_from_file_location("compose_smoke_test_module", path)
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


@pytest.mark.skipif(os.name == "nt", reason="Compose smoke requires Unix sockets and POSIX file permissions")
def test_smoke_state_is_private_and_caller_credentials_are_not_inherited(tmp_path, monkeypatch):
    # A temporary socket only satisfies the file-type preflight; no daemon runs.
    endpoint = tmp_path / "fixture.sock"
    with socket.socket(socket.AF_UNIX) as connection:
        connection.bind(str(endpoint))
        state = smoke.prepare(tmp_path / "state", "unix://" + str(endpoint))
    monkeypatch.setenv("OW_PROVIDER_MODE", "live")
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-parent-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "fixture-unrelated-key")
    monkeypatch.setenv("GITHUB_TOKEN", "fixture-repository-token")
    stack = smoke.Stack(tmp_path / "state", state)
    assert stack.environment["OPENAI_API_KEY"] == ""
    assert "GOOGLE_API_KEY" not in stack.environment and "GITHUB_TOKEN" not in stack.environment
    assert "OW_PROVIDER_MODE" not in stack.environment
    config = (tmp_path / "state/compose.env").read_text()
    assert "OW_PROVIDER_MODE=fixture\n" in config and "OPENAI_API_KEY=\n" in config
    for name in ("state.json", "compose.env"):
        assert stat.S_IMODE((tmp_path / "state" / name).stat().st_mode) == 0o600
    assert len({state["dbPort"], state["apiPort"], state["webPort"]}) == 3
    assert stack.redact(state["password"] + state["dbPassword"] + state["authSecret"]) == "[redacted]" * 3
    assert stack.command[stack.command.index("--project-name") + 1] == state["project"]


@pytest.mark.parametrize("endpoint", ["tcp://production.example:2376", "ssh://operator@remote.example"])
def test_remote_daemon_is_rejected_before_writes(tmp_path, endpoint):
    with pytest.raises(smoke.SmokeFailure, match="local unix"):
        smoke.prepare(tmp_path / "state", endpoint)
    assert not (tmp_path / "state").exists()


def test_cleanup_refuses_non_smoke_project(tmp_path):
    (tmp_path / "state.json").write_text(json.dumps({"createdBy": "ontology-wiki-compose-smoke-v1",
        "project": "production", "dockerHost": "unix:///var/run/docker.sock"}))
    with pytest.raises(smoke.SmokeFailure, match="unrecognized"):
        smoke.load_state(tmp_path)


@pytest.fixture
def readiness_stack(tmp_path):
    # No daemon, network connection, or generated credentials are needed here.
    return smoke.Stack(tmp_path, {"project": "ow-ci-1111111111111111",
        "dockerHost": "unix:///fixture-only.sock", "apiPort": 18000, "webPort": 15173,
        "password": "fixture-password", "dbPassword": "fixture-db", "authSecret": "fixture-secret"})


def test_api_readiness_retries_reset_but_still_requires_connected_fixture(readiness_stack, monkeypatch):
    responses = iter([ConnectionResetError("startup socket reset"),
        {"database": "connected", "providerMode": "live"},
        {"database": "connected", "providerMode": "fixture"}])
    calls, sleeps = [], []

    def request(method, path):
        calls.append((method, path))
        value = next(responses)
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(readiness_stack, "request", request)
    monkeypatch.setattr(smoke, "time", SimpleNamespace(monotonic=lambda: 0, sleep=sleeps.append))
    assert readiness_stack.health() == {"database": "connected", "providerMode": "fixture"}
    assert calls == [("GET", "/health")] * 3 and sleeps == [1, 1]


def test_api_readiness_fails_at_deadline_if_resets_continue(readiness_stack, monkeypatch):
    clock = iter([0, 1, 59, 60])
    calls = []

    def request(method, path):
        calls.append((method, path))
        raise ConnectionResetError("still not ready")

    monkeypatch.setattr(readiness_stack, "request", request)
    monkeypatch.setattr(smoke, "time", SimpleNamespace(monotonic=lambda: next(clock), sleep=lambda _: None))
    with pytest.raises(smoke.SmokeFailure, match="did not become healthy"):
        readiness_stack.health()
    assert calls == [("GET", "/health")] * 2


def test_web_readiness_retries_reset_but_still_requires_application(readiness_stack, monkeypatch):
    responses = iter([ConnectionResetError("startup socket reset"), b"starting", b'<div id="root"></div>'])
    calls = []

    def open_response(url, **kwargs):
        calls.append(url)
        value = next(responses)
        if isinstance(value, Exception):
            raise value
        return BytesIO(value)

    monkeypatch.setattr(smoke, "OPENER", SimpleNamespace(open=open_response))
    monkeypatch.setattr(smoke, "time", SimpleNamespace(monotonic=lambda: 0, sleep=lambda _: None))
    assert readiness_stack.wait_web() == "http://127.0.0.1:15173"
    assert calls == ["http://127.0.0.1:15173"] * 3


def test_web_readiness_fails_at_deadline_if_resets_continue(readiness_stack, monkeypatch):
    clock = iter([0, 1, 29, 30])
    calls = []

    def open_response(url, **kwargs):
        calls.append(url)
        raise ConnectionResetError("still not ready")

    monkeypatch.setattr(smoke, "OPENER", SimpleNamespace(open=open_response))
    monkeypatch.setattr(smoke, "time", SimpleNamespace(monotonic=lambda: next(clock), sleep=lambda _: None))
    with pytest.raises(smoke.SmokeFailure, match="did not serve the application"):
        readiness_stack.wait_web()
    assert calls == ["http://127.0.0.1:15173"] * 2


def test_mutating_api_request_is_not_retried_on_connection_reset(readiness_stack, monkeypatch):
    calls = []

    def open_response(request, **kwargs):
        calls.append(request.get_method())
        raise ConnectionResetError("outcome is unknown")

    monkeypatch.setattr(smoke, "OPENER", SimpleNamespace(open=open_response))
    with pytest.raises(ConnectionResetError):
        readiness_stack.request("POST", "/conversations", {"title": "fixture"})
    assert calls == ["POST"]
