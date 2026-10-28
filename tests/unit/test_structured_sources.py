import json

import pytest

from knowledge.documents.parsing import digest, prepared_passages, read_raw_json, save_raw


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
        read_raw_json(str(tmp_path), "../escaped.json")
    (tmp_path / relative).write_text("tampered")
    with pytest.raises(ValueError):
        read_raw_json(str(tmp_path), relative)
