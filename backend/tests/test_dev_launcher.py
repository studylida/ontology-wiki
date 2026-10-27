import runpy
from pathlib import Path

import pytest


@pytest.mark.parametrize("command,enabled", [("serve", True), ("worker", True), ("test", False)])
def test_local_rag_settings_do_not_override_credentials_or_leak_into_tests(monkeypatch, command, enabled):
    import dotenv
    import subprocess
    import sys
    seen = {}
    monkeypatch.delenv("OW_RERANKER_MODE", raising=False)
    monkeypatch.setattr(sys, "argv", ["dev.py", command])
    monkeypatch.setattr(dotenv, "dotenv_values", lambda path, **kwargs: (
        {"OW_RERANKER_MODE": "cross_encoder", "OW_AUTH_SECRET": "untrusted-overlay", "OPENAI_API_KEY": "ignored"}
        if path.name == ".env.rag.local" else {"OW_AUTH_SECRET": "base-test-secret"}))
    monkeypatch.setattr(subprocess, "call", lambda *args, **kwargs: seen.update(kwargs) or 0)
    with pytest.raises(SystemExit) as result:
        runpy.run_path(str(Path(__file__).resolve().parents[2] / "scripts/v2/dev.py"), run_name="__main__")
    assert result.value.code == 0
    assert seen["env"]["OW_AUTH_SECRET"] == "base-test-secret"
    assert seen["env"].get("OW_RERANKER_MODE") == ("cross_encoder" if enabled else None)
    assert seen["env"].get("OPENAI_API_KEY") != "ignored"
