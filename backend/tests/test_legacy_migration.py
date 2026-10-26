"""Migration mechanics on synthetic exports and disposable PostgreSQL schemas.

No operational legacy database, private production record or model API is used.
"""
from argparse import Namespace
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import zipfile

import numpy as np
import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from knowledge.documents.entities import Document, DocumentRevision, EmbeddingRecord, Passage, PassageEmbedding, ReviewDecision
from knowledge.documents.repository import DocumentRepository
from knowledge.jobs.entities import Job
from knowledge.migration.entities import LegacyArchive, LegacyImport, LegacyMapping
from knowledge.migration.legacy import import_legacy
from knowledge.ontology.entities import Concept, ConceptRelation


def export_fixture():
    return {"exportVersion": "fixture-1", "tables": {
        "sources": [{"id": "source-private", "title": "fixture-private-canary",
            "raw_path": "C:\\legacy-fixture\\original.pdf", "raw_sha256": "ab" * 32,
            "visibility": "private", "security_level": 3,
            "raw_text": "검증용 원문\n원문 문자열과 조건을 바꾸지 않는다."}],
        "concepts": [{"id": "concept-a", "name": "검증용 개념", "aliases": ["fixture"],
            "expert_modified": True, "expert_id": "legacy-expert-7", "description": "전문가가 고친 설명"}],
        "causal_edges": [{"id": "edge-a", "source_id": "concept-a", "target_id": "concept-b",
            "type": "precedes", "conditions": "조건 A에 한함", "source_document_id": "source-private"}],
        "source_links": [{"id": "link-a", "source_id": "source-private", "concept_id": "concept-a",
            "quote": "검증용 원문", "locator": "기존 위치 표기"}],
        "perspective_cases": [{"id": "case-a", "concept_id": "concept-a", "security_level": 3,
            "specifications": {"value": "0.12345678901234567890123456789", "unit": "mW"},
            "expert_changes": [{"actor": "legacy-expert-7", "before": "초안", "after": "수정본"}]}],
        "review_tickets": [{"id": "review-a", "status": "approved", "workingDraft": {"body": "검토 작업본"},
            "instructions": ["조건 보존"], "reviewer_id": "legacy-expert-7"}],
        "audit_logs": [{"id": "audit-a", "previous_hash": "cd" * 32, "action": "approve",
            "actor": "legacy-expert-7", "payload": {"ticket_id": "review-a", "source_id": "source-private"}}],
    }}


def write_export(tmp_path, payload, *, name="legacy-export.json"):
    path = tmp_path / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def no_session():
    raise AssertionError("Dry run/invalid input must not open a database session")


async def counts(sessions):
    async with sessions() as session:
        return {model.__tablename__: await session.scalar(select(func.count()).select_from(model))
                for model in (LegacyImport, LegacyArchive, LegacyMapping)}


@pytest.mark.asyncio
async def test_dry_run_reads_only_and_reports_unmapped_preservation(tmp_path, settings):
    path = write_export(tmp_path, export_fixture())
    before = path.read_bytes()
    result = await import_legacy(no_session, path, "fixture-legacy", settings=settings)
    assert result["mode"] == "dry_run" and result["recordCount"] == 7
    assert result["sharedSearchImported"] is False
    assert result["importId"] is None and result["rawPath"] is None
    assert result["exportSha256"] == sha256(before).hexdigest()
    assert path.read_bytes() == before and not Path(settings.storage_path).exists()


@pytest.mark.asyncio
async def test_apply_preserves_records_original_bytes_and_pending_id_mappings(sessions, tmp_path, settings):
    payload = export_fixture()
    path = write_export(tmp_path, payload)
    original = path.read_bytes()
    result = await import_legacy(sessions, path, "fixture-legacy", apply=True, settings=settings)
    async with sessions() as session:
        manifest = await session.get(LegacyImport, result["importId"])
        rows = list(await session.scalars(select(LegacyArchive)))
        mappings = list(await session.scalars(select(LegacyMapping)))
    assert manifest.export_sha256 == sha256(original).hexdigest()
    assert manifest.record_count == 7 and manifest.counts == {key: 1 for key in payload["tables"]}
    assert (Path(settings.storage_path) / manifest.raw_path).read_bytes() == original
    assert path.read_bytes() == original
    for row in rows:
        assert row.payload == payload["tables"][row.source_table][0]
        assert row.access_classification == "restricted_legacy_archive"
        assert row.first_import_id == manifest.id
    assert len(mappings) == 7
    assert all(row.target_type is None and row.target_id is None for row in mappings)
    assert all(row.disposition == "preserved_pending_mapping" for row in mappings)


@pytest.mark.asyncio
async def test_repeated_and_reordered_imports_are_row_idempotent(sessions, tmp_path, settings):
    payload = export_fixture()
    path = write_export(tmp_path, payload)
    first = await import_legacy(sessions, path, "fixture-legacy", apply=True, settings=settings)
    second = await import_legacy(sessions, path, "fixture-legacy", apply=True, settings=settings)
    assert first["importId"] == second["importId"]
    assert await counts(sessions) == {"legacy_imports": 1, "legacy_archive": 7, "legacy_mappings": 7}
    # A different byte representation gets an original manifest, while identical
    # row values keep their canonical record identity and first-import provenance.
    reordered = {"tables": {name: [{key: value for key, value in reversed(list(rows[0].items()))}]
                             for name, rows in reversed(list(payload["tables"].items()))}}
    other = write_export(tmp_path, reordered, name="reordered-export.json")
    await import_legacy(sessions, other, "fixture-legacy", apply=True, settings=settings)
    assert await counts(sessions) == {"legacy_imports": 2, "legacy_archive": 7, "legacy_mappings": 7}


@pytest.mark.asyncio
async def test_new_expert_version_appends_and_missing_rows_never_delete_history(sessions, tmp_path, settings):
    payload = export_fixture()
    path = write_export(tmp_path, payload)
    await import_legacy(sessions, path, "fixture-legacy", apply=True, settings=settings)
    changed = deepcopy(payload["tables"]["concepts"][0])
    changed["description"] = "나중에 전문가가 정정한 설명"
    update_path = write_export(tmp_path, {"tables": {"concepts": [changed]}}, name="changed-export.json")
    await import_legacy(sessions, update_path, "fixture-legacy", apply=True, settings=settings)
    assert await counts(sessions) == {"legacy_imports": 2, "legacy_archive": 8, "legacy_mappings": 7}
    async with sessions() as session:
        versions = list(await session.scalars(select(LegacyArchive).where(LegacyArchive.source_table == "concepts")))
    assert {v.payload["description"] for v in versions} == {"전문가가 고친 설명", "나중에 전문가가 정정한 설명"}
    assert len({v.record_hash for v in versions}) == len({v.first_import_id for v in versions}) == 2


@pytest.mark.asyncio
async def test_manual_mapping_is_preserved_and_namespaces_do_not_collide(sessions, tmp_path, settings):
    path = write_export(tmp_path, {"tables": {"table_a": [{"id": "same"}], "table_b": [{"id": "same"}]}})
    await import_legacy(sessions, path, "system-a", apply=True, settings=settings)
    async with sessions() as session, session.begin():
        concept = Concept(id="fixture-mapped-concept", name="검증용 수동 대상", origin="fixture")
        session.add(concept)
        mapping = await session.scalar(select(LegacyMapping).where(LegacyMapping.source_table == "table_a"))
        mapping.target_type, mapping.target_id, mapping.disposition = "ontology_concept", concept.id, "mapped_fixture"
        preserved_id = mapping.id
    await import_legacy(sessions, path, "system-a", apply=True, settings=settings)
    await import_legacy(sessions, path, "system-b", apply=True, settings=settings)
    async with sessions() as session:
        mapping = await session.get(LegacyMapping, preserved_id)
        assert mapping.target_id == "fixture-mapped-concept" and mapping.disposition == "mapped_fixture"
    assert await counts(sessions) == {"legacy_imports": 2, "legacy_archive": 4, "legacy_mappings": 4}


@pytest.mark.asyncio
async def test_private_legacy_is_not_published_indexed_or_approved(sessions, tmp_path, settings, principal, reviewer):
    path = write_export(tmp_path, export_fixture())
    await import_legacy(sessions, path, "fixture-private", apply=True, settings=settings)
    async with sessions() as session:
        for model in (Document, DocumentRevision, Passage, EmbeddingRecord, PassageEmbedding,
                      Concept, ConceptRelation, ReviewDecision, Job):
            assert await session.scalar(select(func.count()).select_from(model)) == 0
        for actor in (principal, reviewer):
            result = await DocumentRepository(session).search(actor, [1.0] + [0.0] * 1535,
                "fixture:sha256:1536:v1", "fixture-private-canary")
            assert result["hits"] == []
    # An old approved ticket remains archival data, not a new document approval.
    assert (await counts(sessions))["legacy_archive"] == 7


@pytest.mark.asyncio
async def test_decimal_json_numbers_remain_numbers_with_full_precision(sessions, tmp_path, settings):
    raw = b'{"tables":{"specifications":[{"id":"precise","small":0.12345678901234567890123456789,"large":123456789012345678901234567890,"exponent":-1.234567890123456789e-30,"text":"001.20","flag":true}]}}'
    path = tmp_path / "precision.json"
    path.write_bytes(raw)
    result = await import_legacy(sessions, path, "precision-fixture", apply=True, settings=settings)
    async with sessions() as session:
        row = (await session.execute(select(
            LegacyArchive.payload["small"].astext,
            LegacyArchive.payload["large"].astext,
            LegacyArchive.payload["exponent"].astext,
            func.jsonb_typeof(LegacyArchive.payload["small"]),
            func.jsonb_typeof(LegacyArchive.payload["text"]),
            func.jsonb_typeof(LegacyArchive.payload["flag"]),
        ))).one()
    assert row[0] == "0.12345678901234567890123456789"
    assert row[1] == "123456789012345678901234567890"
    assert Decimal(row[2]) == Decimal("-1.234567890123456789e-30")
    assert tuple(row[3:]) == ("number", "string", "boolean")
    assert (Path(settings.storage_path) / result["rawPath"]).read_bytes() == raw


@pytest.mark.asyncio
async def test_manifest_rows_and_mappings_rollback_together(sessions, tmp_path, settings):
    async with sessions() as session, session.begin():
        schema = await session.scalar(text("SELECT current_schema()"))
        assert schema.startswith("ow_test_")
        await session.execute(text(f'ALTER TABLE "{schema}".legacy_archive ADD CONSTRAINT fixture_reject_record CHECK (source_id <> \'reject-after-manifest\')'))
    path = write_export(tmp_path, {"tables": {"records": [{"id": "accepted-first"}, {"id": "reject-after-manifest"}]}})
    original = path.read_bytes()
    with pytest.raises(IntegrityError):
        await import_legacy(sessions, path, "rollback-fixture", apply=True, settings=settings)
    assert await counts(sessions) == {"legacy_imports": 0, "legacy_archive": 0, "legacy_mappings": 0}
    blobs = list(Path(settings.storage_path).rglob("*.bin"))
    assert len(blobs) == 1 and blobs[0].read_bytes() == original


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_id", [None, "", "  ", {}, [], True, 1.5])
async def test_invalid_original_ids_are_rejected_before_any_write(tmp_path, settings, bad_id):
    path = write_export(tmp_path, {"tables": {"records": [{"id": bad_id}]}})
    with pytest.raises(ValueError):
        await import_legacy(no_session, path, "fixture", apply=True, settings=settings)
    assert not Path(settings.storage_path).exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("source_system", ["", "  ", "x" * 161, None])
async def test_invalid_source_system_is_rejected(tmp_path, settings, source_system):
    path = write_export(tmp_path, {"tables": {"records": [{"id": "a"}]}})
    with pytest.raises(ValueError):
        await import_legacy(no_session, path, source_system, apply=True, settings=settings)
    assert not Path(settings.storage_path).exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", [
    '{"tables":{"records":[{"id":"same"},{"id":"same"}]}}',
    '{"tables":{"records":[{"id":1},{"id":"1"}]}}',
    '{"tables":{"records":[{"id":"a","value":NaN}]}}',
    '{"tables":{"records":[{"id":"a","value":Infinity}]}}',
    '{"tables":{"records":[{"id":"a","value":1,"value":2}]}}',
    '{"tables":{"records":[{"missingId":"a"}]}}',
    '{"tables":{"records":{}}}',
    '[]',
])
async def test_ambiguous_or_invalid_exports_do_not_partially_import(tmp_path, settings, raw):
    path = tmp_path / "invalid.json"
    path.write_text(raw)
    with pytest.raises(ValueError):
        await import_legacy(no_session, path, "fixture", apply=True, settings=settings)
    assert not Path(settings.storage_path).exists()


@pytest.mark.asyncio
async def test_schema_migration_name_guard_precedes_connection(monkeypatch, settings):
    import knowledge.migration.schema as schema
    monkeypatch.setattr(schema, "get_settings", lambda: settings)
    monkeypatch.setattr(schema, "create_async_engine", lambda *_: (_ for _ in ()).throw(AssertionError("Unexpected connection")))
    with pytest.raises(ValueError, match="Explicit --database-name"):
        await schema.migrate("wrong-target-name")


@pytest.mark.asyncio
async def test_schema_versions_are_idempotent_and_applied_sql_cannot_change(monkeypatch, pg_engine, settings, tmp_path):
    import knowledge.migration.schema as schema
    from sqlalchemy.engine import make_url
    migrations = tmp_path / "schema-fixture"
    migrations.mkdir()
    migration = migrations / "002_legacy_imports.sql"
    migration.write_text((Path(__file__).resolve().parents[1] / "migrations/v2/002_legacy_imports.sql").read_text())
    async with pg_engine.begin() as connection:
        current = await connection.scalar(text("SELECT current_schema()"))
        assert current.startswith("ow_test_")
        # Recreate the exact pre-002 shape inside this disposable schema only.
        await connection.execute(text(f'ALTER TABLE "{current}".legacy_archive DROP COLUMN first_import_id'))
        await connection.execute(text(f'DROP TABLE "{current}".legacy_imports'))
        await connection.execute(text(f'''INSERT INTO "{current}".legacy_archive
            (id,source_system,source_table,source_id,record_hash,payload,access_classification,imported_at)
            VALUES ('preupgrade','fixture','concepts','old-id','fixture-hash',
                    '{{"expert":"preserved"}}'::jsonb,'restricted_legacy_archive',now())'''))
    monkeypatch.setattr(schema, "MIGRATION_ROOT", migrations)
    monkeypatch.setattr(schema, "get_settings", lambda: settings)
    monkeypatch.setattr(schema, "create_async_engine", lambda *_: pg_engine)
    name = make_url(settings.database_url).database
    assert (await schema.migrate(name))["applied"] == ["002_legacy_imports.sql"]
    assert (await schema.migrate(name))["applied"] == []
    async with pg_engine.connect() as connection:
        current = await connection.scalar(text("SELECT current_schema()"))
        assert current.startswith("ow_test_")
        row = (await connection.execute(text(f'SELECT payload->>\'expert\', first_import_id FROM "{current}".legacy_archive WHERE id=\'preupgrade\''))).one()
        assert tuple(row) == ("preserved", None)
    migration.write_text(migration.read_text() + "\n-- changed after application\n")
    with pytest.raises(RuntimeError, match="Applied migration changed"):
        await schema.migrate(name)


def cached_corpus_fixture(tmp_path, monkeypatch, owner):
    import knowledge.migration.evaluation as evaluation
    directory = tmp_path / "frozen-evaluation-fixture"
    (directory / "data").mkdir(parents=True)
    (directory / "cache").mkdir()
    body = "---\r\npublisher: Fixture Publisher\r\ntype: fixture\r\n---\r\n# 본문\r\n검증 본문\r\n# 메뉴\r\n검증 메뉴\r\n".encode()
    archive = tmp_path / "frozen-fixture.zip"
    source_path = "fixture/source.md"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr(source_path, body)
    chunks = []
    for index, passage_text in enumerate(("검증 본문", "검증 메뉴")):
        input_text = "fixture embedding input\n" + passage_text
        start = body.decode().index(passage_text)
        chunks.append({"chunk_id": f"fixture-chunk-{index}", "source_path": source_path,
            "title": "검증 문헌", "text": passage_text, "section_path": "검증 구간",
            "start": start, "end": start + len(passage_text), "embedding_text": input_text,
            "embedding_input_sha256": sha256(input_text.encode()).hexdigest()})
    chunk_path = directory / "data/chunks.jsonl"
    chunk_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in chunks) + "\n")
    filter_path = directory / "navigation_chunk_filter_v1.json"
    filter_path.write_text(json.dumps({"excluded_chunk_ids": ["fixture-chunk-1"]}))
    for model, dimensions, column in (("text-embedding-3-large", 3072, 0), ("text-embedding-3-small", 1536, 1)):
        matrix = np.zeros((2, dimensions), dtype=np.float32)
        matrix[:, column] = 1.0
        np.savez(directory / "cache" / f"corpus-{model}.npz", ids=[row["chunk_id"] for row in chunks], vectors=matrix)
    for field, path in (("ZIP_SHA", archive), ("CHUNK_SHA", chunk_path), ("FILTER_SHA", filter_path)):
        monkeypatch.setattr(evaluation, field, sha256(path.read_bytes()).hexdigest())
    return Namespace(approve_for_development=True, evaluation_dir=str(directory), corpus_zip=str(archive),
                     owner=owner, model="text-embedding-3-large"), body


@pytest.mark.asyncio
async def test_cached_evaluation_reuses_originals_and_keeps_profiles_separate(sessions, settings, tmp_path, monkeypatch, reviewer):
    from knowledge.migration.evaluation import import_evaluation
    args, original = cached_corpus_fixture(tmp_path, monkeypatch, reviewer.username)
    first = await import_evaluation(sessions, settings, args)
    repeated = await import_evaluation(sessions, settings, args)
    assert first["documentsImported"] == 1 and first["indexedPassages"] == 1
    assert repeated["documentsAlreadyPresent"] == 1 and repeated["indexedPassages"] == 0
    async with sessions() as session:
        document = await session.scalar(select(Document))
        source_id, active_id = document.current_revision_id, document.active_revision_id
        revision = await session.get(DocumentRevision, source_id)
        snapshot = revision.index_snapshot_id
        assert revision.content.encode() == original
        assert (Path(settings.storage_path) / revision.raw_path).read_bytes() == original
        assert revision.metadata_json["authenticity"] == "not_verified_in_import"
    args.model = "text-embedding-3-small"
    alternative = await import_evaluation(sessions, settings, args)
    assert alternative["documentsImported"] == 0 and alternative["indexedPassages"] == 1
    assert (await import_evaluation(sessions, settings, args))["indexedPassages"] == 0
    async with sessions() as session:
        document = await session.scalar(select(Document))
        revision = await session.get(DocumentRevision, source_id)
        assert document.current_revision_id == source_id and document.active_revision_id == active_id
        assert revision.index_snapshot_id == snapshot
        assert await session.scalar(select(func.count()).select_from(Document)) == 1
        assert await session.scalar(select(func.count()).select_from(Passage)) == 2
        assert await session.scalar(select(func.count()).select_from(PassageEmbedding)) == 2
        assert await session.scalar(select(func.count()).select_from(ReviewDecision)) == 1
        vector = [1.0] + [0.0] * 1535
        large = await DocumentRepository(session).search(reviewer, vector, first["profileId"], "")
        small = await DocumentRepository(session).search(reviewer, vector, alternative["profileId"], "")
        assert large["hits"][0]["cosineDistance"] == pytest.approx(0.0)
        assert small["hits"][0]["cosineDistance"] == pytest.approx(1.0)
    assert first["modelCalls"] == repeated["modelCalls"] == alternative["modelCalls"] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("approved,database", [(False, "corpus_dev"), (True, "corpus_operational")])
async def test_evaluation_import_requires_explicit_development_target(settings, approved, database):
    from knowledge.migration.evaluation import import_evaluation
    local = settings.model_copy(update={"database_url": f"postgresql+asyncpg://unused@127.0.0.1/{database}"})
    args = Namespace(approve_for_development=approved, evaluation_dir="not-opened", corpus_zip="not-opened")
    with pytest.raises(ValueError, match="restricted"):
        await import_evaluation(no_session, local, args)
