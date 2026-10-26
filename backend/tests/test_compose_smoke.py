"""Verify CI isolation guards locally; this does not run Docker or claim it did."""
import importlib.util
import json
from pathlib import Path
import socket
import stat

import pytest

path = Path(__file__).resolve().parents[2] / "scripts/v2/compose_smoke.py"
spec = importlib.util.spec_from_file_location("compose_smoke_test_module", path)
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


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
