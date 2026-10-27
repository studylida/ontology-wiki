import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from knowledge.documents.entities import Document, DocumentRevision, ReviewDecision


spec = importlib.util.spec_from_file_location("corpus_intake", Path(__file__).parents[2] / "scripts/v2/register_corpus_batch.py")
intake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intake)


def fixture_manifest(tmp_path):
    source = tmp_path / "original.md"
    content = tmp_path / "edited.md"
    source.write_text("# 원본\n기존 문장을 보존합니다.", encoding="utf-8")
    content.write_text("# 정정 편집본\n검토한 문장입니다.", encoding="utf-8")
    row = {"id": "e-test", "title": "검토 문헌", "source_file": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "content_file": str(content),
        "content_sha256": hashlib.sha256(content.read_bytes()).hexdigest(), "document_form": "edited_derivative",
        "decision": "approve", "review_reason": "범위 내 검토 완료", "review_scope": "제공된 본문과 정정 문장 대조"}
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([row]), encoding="utf-8")
    return manifest, row


def test_manifest_refuses_changed_reviewed_content(tmp_path):
    manifest, row = fixture_manifest(tmp_path)
    Path(row["content_file"]).write_text("교체된 미검토 본문", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        intake.load_manifest(manifest)


def test_manifest_requires_explicit_review_and_form(tmp_path):
    manifest, row = fixture_manifest(tmp_path)
    row["decision"] = "approve-all"
    manifest.write_text(json.dumps([row]), encoding="utf-8")
    with pytest.raises(ValueError, match="review decision"):
        intake.load_manifest(manifest)


def test_lineage_groups_fragments_and_encoded_source_paths():
    assert intake.canonical_lineage("https://example.org/%EB%B0%98%EB%8F%84%EC%B2%B4/#page=2") == "https://example.org/반도체"
    assert intake.canonical_lineage("https://doi.org/10.3390/MA17092150") == "doi:10.3390/ma17092150"


def test_job_costs_include_flat_generation_usage_and_prior_unknown_attempts():
    from knowledge.core.usage import summarize_usage
    job = SimpleNamespace(usage={"calls": 1, "costUsd": 0.002}, result={"attemptHistory": [
        {"usage": {"components": [{"calls": 1, "costUsd": None}]}}]})
    total = summarize_usage(intake.job_usage_components(job))
    assert total["knownCostUsd"] == 0.002
    assert total["costUsd"] is None
    assert total["calls"] == 2
    assert total["unknownCostCalls"] == 1


@pytest.mark.asyncio
async def test_registration_preserves_raw_and_review_scope_and_is_idempotent(tmp_path, sessions, settings, reviewer, embedding_client):
    manifest, row = fixture_manifest(tmp_path)
    rows = intake.load_manifest(manifest)
    output = tmp_path / "report.json"
    first = await intake.register(rows, sessions, settings, reviewer, embedding_client, output)
    second = await intake.register(rows, sessions, settings, reviewer, embedding_client, output)
    assert first["items"][0]["revisionId"] == second["items"][0]["revisionId"]
    async with sessions() as session:
        revision = await session.get(DocumentRevision, first["items"][0]["revisionId"])
        assert revision.metadata_json["documentForm"] == "edited_derivative"
        assert revision.metadata_json["originalSha256"] == row["source_sha256"]
        assert revision.metadata_json["reviewScope"] == row["review_scope"]
        assert (Path(settings.storage_path) / revision.raw_path).read_bytes() == Path(row["source_file"]).read_bytes()
        assert await session.scalar(select(func.count()).select_from(Document)) == 1
        assert await session.scalar(select(func.count()).select_from(ReviewDecision)) == 1


@pytest.mark.asyncio
async def test_held_archive_is_preserved_without_index_job(tmp_path, sessions, settings, reviewer, embedding_client):
    manifest, row = fixture_manifest(tmp_path)
    row["decision"] = "hold"
    manifest.write_text(json.dumps([row]), encoding="utf-8")
    result = await intake.register(intake.load_manifest(manifest), sessions, settings, reviewer, embedding_client, tmp_path / "report.json")
    assert "jobId" not in result["items"][0]
    async with sessions() as session:
        revision = await session.get(DocumentRevision, result["items"][0]["revisionId"])
        document = await session.get(Document, revision.document_id)
        assert revision.review_status == "held"
        assert document.active_revision_id is None
