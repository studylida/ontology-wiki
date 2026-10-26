"""Preserve a supplied export without connecting to or publishing the old system."""
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

from sqlalchemy import Text, cast, literal, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.dialects.postgresql import JSONB

from knowledge.core.config import get_settings
from knowledge.core.ids import new_id
from knowledge.documents.parsing import save_raw
from knowledge.migration.entities import LegacyArchive, LegacyImport, LegacyMapping


def _reject_constant(value):
    raise ValueError("Non-finite JSON numbers are not supported")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object keys are not allowed")
        result[key] = value
    return result


def exact_json(value):
    """Canonical JSON for SQL JSONB casts, never Decimal → float or quoted number.

    Byte-level fidelity belongs to the original export blob. This representation
    preserves JSON types and decimal precision while ignoring object key order.
    """
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        if "\x00" in value:
            raise ValueError("PostgreSQL JSONB cannot preserve null characters")
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Non-finite JSON numbers are not supported")
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(exact_json(item) for item in value) + "]"
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("JSON object keys must be strings")
        return "{" + ", ".join(exact_json(key) + ": " + exact_json(value[key]) for key in sorted(value)) + "}"
    raise ValueError("Unsupported export value type")


def _source_id(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("Original IDs must be non-empty strings or integers")
    if isinstance(value, str) and (not value.strip() or "\x00" in value):
        raise ValueError("Original IDs must be non-empty strings or integers")
    return str(value)


async def import_legacy(sessions, export_path, source_system, *, apply=False, settings=None):
    """Dry run never opens a database session or writes an original file.

    Apply retains original bytes, then atomically commits their manifest, archived
    versions and pending mappings. A failed DB transaction can leave an unreferenced
    immutable blob, but never a partially committed import or shared knowledge.
    """
    if not isinstance(source_system, str) or not source_system.strip() or len(source_system) > 160 or "\x00" in source_system:
        raise ValueError("source_system must be a non-empty identifier of at most 160 characters")
    original = Path(export_path).read_bytes()
    raw = json.loads(original.decode("utf-8-sig"), parse_float=Decimal,
                     parse_constant=_reject_constant, object_pairs_hook=_unique_object)
    if not isinstance(raw, dict) or not isinstance(raw.get("tables"), dict):
        raise ValueError("Expected JSON export with tables mapping")
    counts, records = {}, []
    for table, rows in raw["tables"].items():
        if not table.strip() or len(table) > 160 or "\x00" in table:
            raise ValueError("Source table names must be non-empty and at most 160 characters")
        if not isinstance(rows, list) or any(not isinstance(row, dict) or "id" not in row for row in rows):
            raise ValueError(f"Every {table} record needs its original id")
        ids = [_source_id(row["id"]) for row in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate IDs in export table {table}")
        counts[table] = len(rows)
        for source_id, row in zip(ids, rows):
            encoded = exact_json(row)
            try:
                record_hash = sha256(encoded.encode("utf-8")).hexdigest()
            except UnicodeEncodeError as exc:
                raise ValueError("The export contains invalid Unicode") from exc
            records.append((table, source_id, encoded, record_hash))
    export_hash = sha256(original).hexdigest()
    import_id, raw_path = None, None
    if apply:
        settings = settings or get_settings()
        raw_path = save_raw(settings.storage_path, original)
        async with sessions() as session, session.begin():
            import_id = await session.scalar(insert(LegacyImport).values(id=new_id("legacy_import"),
                source_system=source_system, export_sha256=export_hash, raw_path=raw_path,
                counts=counts, record_count=len(records))
                .on_conflict_do_nothing(index_elements=["source_system", "export_sha256"])
                .returning(LegacyImport.id))
            if import_id is None:
                import_id = await session.scalar(select(LegacyImport.id).where(
                    LegacyImport.source_system == source_system, LegacyImport.export_sha256 == export_hash))
            for table, source_id, encoded, record_hash in records:
                await session.execute(insert(LegacyArchive).values(id=new_id("archive"), source_system=source_system,
                    source_table=table, source_id=source_id, record_hash=record_hash, first_import_id=import_id,
                    payload=cast(literal(encoded, type_=Text), JSONB))
                    .on_conflict_do_nothing(index_elements=["source_system", "source_table", "source_id", "record_hash"]))
                await session.execute(insert(LegacyMapping).values(id=new_id("mapping"), source_system=source_system,
                    source_table=table, source_id=source_id).on_conflict_do_nothing(index_elements=["source_system", "source_table", "source_id"]))
    return {"mode": "apply" if apply else "dry_run", "sourceSystem": source_system, "counts": counts,
            "recordCount": len(records), "sharedSearchImported": False,
            "importId": import_id, "exportSha256": export_hash, "rawPath": raw_path,
            "disposition": "Restricted original export and exact JSON archive. Mapping and source validation remain required before current publication."}
