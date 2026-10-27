import json

import pytest
from sqlalchemy import select

from knowledge.documents.dto import NewDocument, NewRevision, ReviewRequest
from knowledge.documents.entities import DocumentRevision, Passage
from knowledge.documents.parsing import digest, prepared_passages, read_raw_json, save_raw
from knowledge.documents.service import DocumentService


@pytest.mark.asyncio
async def test_held_extraction_and_edited_revision_require_explicit_review(sessions, settings, reviewer):
    docs = DocumentService(sessions, settings)
    content = "표: 0 283.8 240.9\n\n조건: 250°C, 30 min"
    first, second = content.split("\n\n")
    first_record = record(first) | {"qualityHold": "전처리 구조 또는 수식 확인 필요"}
    second_record = record(second, len(first) + 2)
    created = await docs.create(reviewer, NewDocument(title="실험", content=content,
        visibility="shared_candidate", documentForm="text_extraction"), raw_bytes=b"original-pdf",
        media_type="application/pdf", passage_records=[first_record, second_record], processing_metadata={
            "parserProfile": {"engine": "docling"}, "preprocessingQuality": {"version": 2, "issues": [{"reason": "table"}]}})
    original_id = created["currentRevisionId"]
    await docs.review(reviewer, original_id, ReviewRequest(decision="approve", reason="기존 구간 검토"))
    old = await docs.detail(reviewer, original_id)
    assert [p["excluded"] for p in old["passages"]] == [True, False]
    edited = await docs.add_revision(reviewer, created["id"], NewRevision(content="표: 열을 원문과 대조해 수정\n\n조건: 250°C, 30 min"))
    edited_id = edited["currentRevisionId"]
    before_review = await docs.detail(reviewer, edited_id)
    assert before_review["reviewStatus"] == "pending"
    assert before_review["metadata"]["preprocessingEditReviewRequired"]
    assert all(p["excluded"] for p in before_review["passages"])
    await docs.review(reviewer, edited_id, ReviewRequest(decision="approve", reason="편집본의 표와 조건 대조"))
    after_review = await docs.detail(reviewer, edited_id)
    assert all(not p["excluded"] for p in after_review["passages"])
    assert (await docs.detail(reviewer, original_id))["passages"][0]["excluded"]


def record(text, offset=0):
    return {"text": text, "start_offset": offset, "end_offset": offset + len(text),
            "locator": "페이지 2 · 표 1", "embedding_text": "문헌: 실험\n" + text,
            "input_hash": "untrusted-supplied-hash"}


def test_parser_offsets_and_embedding_identity_are_verified():
    text = "온도 | 접합률\n250°C | 31.24%"
    result = prepared_passages(text, [record(text)])
    assert result[0].input_hash == digest(result[0].embedding_text)
    assert result[0].input_hash != "untrusted-supplied-hash"
    with pytest.raises(ValueError):
        prepared_passages(text, [record("300°C")])
    with pytest.raises(ValueError):
        prepared_passages(text, [record(text), record(text)])


def test_parser_artifact_is_hash_checked_and_confined_to_storage(tmp_path):
    relative = save_raw(str(tmp_path), json.dumps([{"page": 2}]).encode())
    assert read_raw_json(str(tmp_path), relative) == [{"page": 2}]
    with pytest.raises(ValueError):
        read_raw_json(str(tmp_path), "../outside.bin")
    (tmp_path / relative).write_text("modified")
    with pytest.raises(ValueError):
        read_raw_json(str(tmp_path), relative)


@pytest.mark.asyncio
async def test_structured_source_keeps_original_and_old_provenance_on_manual_revision(sessions, settings, principal):
    content = "온도 | 접합률\n250°C | 31.24%"
    original = b"%PDF-test-original-preservation"
    docs = DocumentService(sessions, settings)
    created = await docs.create(principal,
        NewDocument(title="실험", content=content, documentForm="text_extraction"),
        raw_bytes=original, media_type="application/pdf", read_scope_value="partial", passage_records=[record(content)],
        processing_metadata={"parserProfile": {"engine": "docling", "version": "test"},
                             "preparedPassagesArtifact": "prepared-reference", "sourceMapArtifact": "map-reference",
                             "totalPages": 10, "pagesRead": 10, "sourceSha256": "original-hash", "rawPath": "original-path",
                             "processing": {"elapsedMs": 123}})
    previous_id = created["currentRevisionId"]
    changed = await docs.add_revision(principal, created["id"],
        NewRevision(content="---\ndocument_form: original\n---\n" + content + "\n편집 설명"))
    async with sessions() as session:
        old = await session.get(DocumentRevision, previous_id)
        new = await session.get(DocumentRevision, changed["currentRevisionId"])
        chunks = list((await session.scalars(select(Passage).where(Passage.source_revision_id == previous_id))).all())
    assert len(chunks) == 1 and chunks[0].locator == "페이지 2 · 표 1"
    assert chunks[0].text == content and old.content == content
    from pathlib import Path
    assert (Path(settings.storage_path) / old.raw_path).read_bytes() == original
    assert old.metadata_json["sourceMapArtifact"] == "map-reference"
    assert old.metadata_json["documentForm"] == "text_extraction"
    assert new.metadata_json["derivedFromRevisionId"] == previous_id
    assert new.metadata_json["documentForm"] == "edited_derivative"
    assert new.read_scope == old.read_scope == "partial"
    assert old.metadata_json["processing"]["elapsedMs"] == 123
    assert not {"totalPages", "pagesRead", "sourceSha256", "rawPath", "processing"}.intersection(new.metadata_json)
    assert "sourceMapArtifact" not in new.metadata_json
    assert "parserProfile" not in new.metadata_json


@pytest.mark.asyncio
async def test_editorial_revision_updates_hash_without_reusing_old_review_or_file(sessions, settings, principal):
    docs = DocumentService(sessions, settings)
    created = await docs.create(principal, NewDocument(title="편집본", content="이전 본문", documentForm="editorial_summary"),
        processing_metadata={"editorialSha256": digest("이전 본문"), "editorialFile": "old.md",
                             "reviewScope": "이전 본문 검토", "editorialCorrections": ["이전 교정"], "originalSha256": "original"})
    changed = await docs.add_revision(principal, created["id"], NewRevision(content="새 본문"))
    async with sessions() as session:
        new = await session.get(DocumentRevision, changed["currentRevisionId"])
        old = await session.get(DocumentRevision, created["currentRevisionId"])
    assert new.metadata_json["editorialSha256"] == digest("새 본문")
    assert not {"editorialFile", "reviewScope", "editorialCorrections"}.intersection(new.metadata_json)
    assert new.metadata_json["originalSha256"] == "original"
    assert new.metadata_json["derivedFromRevisionId"] == old.id
    assert old.metadata_json["editorialFile"] == "old.md"
