"""Only pure guards and a fixture stream run here; no live verifier execution."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from knowledge.core.errors import AppError
from knowledge.integrations.providers import ProviderDelta


_path = Path(__file__).resolve().parents[2] / "scripts" / "v2" / "verify_live_ontology.py"
_spec = importlib.util.spec_from_file_location("live_ontology_verification_guards", _path)
verifier = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verifier)


def configuration(tmp_path):
    settings = SimpleNamespace(database_url="postgresql+asyncpg://127.0.0.1/ontology_dev",
                               provider_mode="live", generation_model="gpt-6-luna")
    args = SimpleNamespace(allow_live=True, source_revision=["rev_a", "rev_b"],
                           schema_prefix="ow_live_ontology_", output=tmp_path / "new-report.json")
    return settings, args


@pytest.mark.parametrize("field,value", [("database_url", "postgresql+asyncpg://db.example/ontology_dev"),
    ("database_url", "postgresql+asyncpg://127.0.0.1/ontology_prod"),
    ("database_url", "sqlite:///ontology_dev"), ("provider_mode", "fixture"), ("generation_model", "other-model")])
def test_live_verifier_rejects_wrong_target_without_calling_anything(tmp_path, field, value):
    settings, args = configuration(tmp_path)
    setattr(settings, field, value)
    with pytest.raises(ValueError):
        verifier.check_target(settings, args)


@pytest.mark.parametrize("field,value", [("allow_live", False), ("schema_prefix", "public"),
    ("schema_prefix", 'ow_live_bad";'), ("source_revision", []), ("source_revision", ["rev_a", "rev_a"])])
def test_live_verifier_requires_optin_unique_sources_and_owned_schema_prefix(tmp_path, field, value):
    settings, args = configuration(tmp_path)
    setattr(args, field, value)
    with pytest.raises(ValueError):
        verifier.check_target(settings, args)


def test_live_verifier_accepts_explicit_dev_configuration_and_refuses_report_overwrite(tmp_path):
    settings, args = configuration(tmp_path)
    verifier.check_target(settings, args)
    args.output.write_text("existing report")
    with pytest.raises(ValueError):
        verifier.check_target(settings, args)
    assert args.output.read_text() == "existing report"


def test_live_verifier_redacts_driver_and_validation_error_text():
    result = verifier._safe_error(RuntimeError("source text and secret DSN must not be printed"))
    assert "secret" not in str(result) and "message" not in result


@pytest.mark.asyncio
async def test_live_verifier_keeps_observed_usage_on_failed_fixture_stream_without_retry():
    class FailingFixture:
        model = "fixture-source"
        calls = 0
        async def stream(self, messages, **kwargs):
            self.calls += 1
            yield ProviderDelta(usage={"calls": 0, "fixtureCalls": 1, "costUsd": None, "totalTokens": 12})
            raise AppError(502, "provider_incomplete", "Fixture incomplete")
    client = FailingFixture()
    observed = verifier.ObservedGeneration(client)
    with pytest.raises(AppError):
        _ = [delta async for delta in observed.stream([])]
    assert client.calls == 1 and observed.invocations == 1
    assert observed.observed_usage()["totalTokens"] == 12
    assert observed.observed_usage()["costUsd"] is None
