"""Deterministic text segmentation. Offsets describe preserved text, not truth."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def metadata_digest(value: dict) -> str:
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str))


def model_source_metadata(metadata: dict) -> dict:
    return {key: metadata[key] for key in (
        "publisher", "publisherId", "author", "attributedTo", "attributionBasis", "sourceType",
        "documentForm", "publishedAt", "url") if key in metadata}


@dataclass(frozen=True)
class ParsedPassage:
    ordinal: int
    text: str
    locator: str
    start_offset: int
    end_offset: int
    embedding_text: str
    input_hash: str
    excluded: bool = False
    exclusion_reason: str | None = None


def frontmatter(text: str) -> dict:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if not match:
        return {}
    try:
        data = yaml.safe_load(match.group(1))
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def declared_document_form(text: str) -> str | None:
    data = frontmatter(text)
    value = data.get("document_form")
    if isinstance(value, str) and value in {
        "original", "editorial_summary", "edited_derivative", "text_extraction", "unknown"
    }:
        return value
    return "edited_derivative" if data.get("editorial_derivative") is True else None


def segment(text: str, title: str, *, max_chars: int = 1400, overlap: int = 150) -> list[ParsedPassage]:
    from knowledge.documents.preprocessing import markdown_blocks
    blocks, notes = markdown_blocks(text)
    passages, pending = [], []

    def emit():
        if not pending:
            return
        begin, end = pending[0]["inputStart"], pending[-1]["inputEnd"]
        value, locator = text[begin:end], pending[0]["locator"]
        embedded = f"문헌: {title}\n절: {locator}\n{value}"
        # UTF-8 byte count bounds token count without a tokenizer dependency.
        oversized = len(embedded.encode("utf-8")) > 7000
        passages.append(ParsedPassage(len(passages), value, locator, begin, end, embedded, digest(embedded),
            oversized, "긴 문단 또는 표의 분할 검토 필요" if oversized else None))

    for block in blocks:
        table_note = (any(p["kind"] == "table" for p in pending) and
                      bool(re.match(r"^(?:[*†‡]|주\s*[:：]|note\s*[:：]|footnote\s*[:：])", block["text"], re.I)))
        if pending and (block["kind"] == "heading" or block["locator"] != pending[-1]["locator"]
                or (block["kind"] != "table" and not table_note and block["inputEnd"] - pending[0]["inputStart"] > max_chars)
                or any(pending[-1]["inputEnd"] <= n["inputStart"] < block["inputStart"] for n in notes)):
            emit()
            pending = []
        pending.append(block)
    emit()
    return passages


def prepared_passages(content: str, records: list[dict]) -> list[ParsedPassage]:
    """Accept parser-produced chunks only when they map to the stored extraction."""
    if not isinstance(records, list) or not records:
        raise ValueError("Structured parsing produced no passages")
    result, previous_end = [], 0
    for ordinal, record in enumerate(records):
        text, start, end = record.get("text"), record.get("start_offset"), record.get("end_offset")
        locator, embedded = record.get("locator"), record.get("embedding_text")
        if (not isinstance(text, str) or not text.strip()
                or type(start) is not int or type(end) is not int
                or not 0 <= start < end <= len(content) or start < previous_end
                or content[start:end] != text or not isinstance(locator, str) or not locator.strip()
                or not isinstance(embedded, str) or not embedded.strip() or text not in embedded):
            raise ValueError("Structured passage does not match preserved content")
        hold = record.get("qualityHold")
        if hold is not None and (not isinstance(hold, str) or not hold.strip()):
            raise ValueError("Invalid structured quality hold")
        result.append(ParsedPassage(ordinal, text, locator, start, end, embedded, digest(embedded), bool(hold), hold))
        previous_end = end
    return result


def read_raw_json(storage_path: str, relative_path: str):
    root = Path(storage_path).resolve()
    target = (root / relative_path).resolve()
    if not target.is_relative_to(root) or target.suffix != ".bin":
        raise ValueError("Invalid source artifact path")
    body = target.read_bytes()
    if hashlib.sha256(body).hexdigest() != target.stem:
        raise ValueError("Source artifact hash mismatch")
    return json.loads(body)


def save_raw(storage_path: str, body: bytes) -> str:
    root = Path(storage_path).resolve()
    hashed = hashlib.sha256(body).hexdigest()
    relative = Path(hashed[:2]) / f"{hashed}.bin"
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        # A complete temporary file is linked atomically. Concurrent transfers
        # cannot expose a partially written content-addressed original.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
                temporary = handle.name
                handle.write(body)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, target)
            except FileExistsError:
                pass
        finally:
            if temporary:
                os.unlink(temporary)
    if hashlib.sha256(target.read_bytes()).hexdigest() != hashed:
        from knowledge.core.errors import AppError
        raise AppError(500, "raw_storage_mismatch", "보존 원문의 해시를 확인할 수 없습니다.")
    return relative.as_posix()
