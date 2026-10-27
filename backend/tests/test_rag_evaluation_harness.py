"""Evaluation must not quietly compare changed sources or miscount cached judge calls."""
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts/v2" / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def test_frozen_manifest_rejects_edited_or_revoked_source_but_ignores_new_documents():
    validate = module("evaluate_rag_pipeline").validate_manifest
    original = {"revisionId": "r1", "contentHash": "a", "metadataHash": "b", "metadataVersion": 1}
    assert validate([original, {"revisionId": "r2"}], [original]) == [original]
    for changed in ([], [{**original, "metadataVersion": 2}], [{**original, "contentHash": "edited"}]):
        with pytest.raises(ValueError, match="no longer active or changed"):
            validate(changed, [original])
    with pytest.raises(ValueError, match="distinct"):
        validate([original], [original, original])


def test_judge_cache_reuses_output_without_claiming_new_provider_usage(tmp_path, monkeypatch):
    from knowledge.integrations import providers
    checker = module("check_rag_results")
    calls = []

    class FakeClient:
        def __init__(self, model, **kwargs):
            pass

        async def stream(self, messages, **kwargs):
            calls.append(messages)
            yield providers.ProviderDelta(text="Entailment", usage={"inputTokens": 10, "outputTokens": 1})

    monkeypatch.setattr(providers, "OpenAIGenerationClient", FakeClient)
    judge = checker.ResponsesJudge("test", "medium", tmp_path, max_calls=1)
    assert judge(["claim"]) == ["Entailment"]
    assert judge(["claim"]) == ["Entailment"]
    assert len(calls) == 1
    assert judge.calls[-1]["cacheHit"] is True
    assert judge.calls[-1]["usage"] is None
    with pytest.raises(RuntimeError, match="budget"):
        judge(["different claim"])


def test_judge_rejects_refusal_and_missing_labels_instead_of_neutral_padding():
    validate = module("check_rag_results").validate_judge_format
    prompt = '### Claims:\n("a", "is", "b")\n("c", "is", "d")\n\nYour answer should always be only a list of labels.'
    validate(prompt, "Entailment\nNeutral")
    validate(prompt, '["Entailment", "Neutral"]')
    validate(prompt, "1. Entailment\n2. Neutral")
    for invalid in ("I cannot evaluate this input.", "Entailment", "Entailment Neutral Contradiction", "Entailment\nNeutral because no information"):
        with pytest.raises(ValueError, match="label format/count"):
            validate(prompt, invalid)
