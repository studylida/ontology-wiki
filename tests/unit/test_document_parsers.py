import hashlib
import json
from pathlib import Path

import pytest

from knowledge.core.errors import AppError
from knowledge.integrations import document_parser
from knowledge.integrations.docling_artifacts import conversion_key, load_conversion, preserve_conversion
from knowledge.integrations.docling_parser import assemble_blocks


def sample_result(body=b"original-pdf"):
    content = "250°C | 0.5 h | 31.24%"
    return {"title": "Example", "content": content, "readScope": "full",
            "metadata": {"sourceSha256": hashlib.sha256(body).hexdigest(),
                         "parserProfile": {"version": "2.143.0"}},
            "limitations": [], "structuredDocument": {"tables": []},
            "sourceMap": [{"startOffset": 0, "endOffset": len(content), "locator": "페이지 3",
                           "label": "text", "documentRefs": [], "pageNumbers": [3], "provenance": []}],
            "preparedPassages": [{"text": content, "locator": "페이지 3", "start_offset": 0,
                                  "end_offset": len(content), "embedding_text": content}]}


def test_whole_structured_blocks_keep_exact_offsets():
    blocks = [{"text": text, "label": "table", "locator": "페이지 3 · 표 1",
               "documentRefs": ["#/tables/0"], "provenance": [{"page_no": 3}]}
              for text in ("| 온도 | 접합률 |\n| 250°C | 31.24% |", "next complete block")]
    content, mapping, partial = assemble_blocks(blocks, 55)
    assert partial and len(mapping) == 1
    assert content[mapping[0]["startOffset"]:mapping[0]["endOffset"]] == blocks[0]["text"]
    assert mapping[0]["documentRefs"] == ["#/tables/0"]
    assert "next" not in content


def test_parser_environment_does_not_inherit_credentials(monkeypatch):
    for key in ("OPENAI_API_KEY", "HF_TOKEN", "OW_DATABASE_URL", "USERPROFILE", "PYTHONPATH"):
        monkeypatch.setenv(key, "sensitive-parent-value")
    env = document_parser._parser_environment()
    assert "sensitive-parent-value" not in env.values()
    assert env["HF_HUB_OFFLINE"] == "1"
    assert env["HF_HUB_DISABLE_IMPLICIT_TOKEN"] == "1"


@pytest.mark.asyncio
async def test_legacy_html_is_actually_extracted_on_current_platform():
    result = await document_parser.parse_file(b"<html><title>A</title><nav>menu</nav><main>250 C bonding</main></html>", "text/html")
    assert "250 C bonding" in result["content"]
    assert "menu" not in result["content"]


def test_content_addressed_cache_preserves_and_validates_every_artifact(tmp_path):
    result = sample_result()
    preserve_conversion(str(tmp_path), "a" * 64, b"original-pdf", result)
    loaded = load_conversion(str(tmp_path), "a" * 64, b"original-pdf")
    assert loaded == result
    assert (tmp_path / result["metadata"]["rawPath"]).read_bytes() == b"original-pdf"
    assert json.loads((tmp_path / result["metadata"]["preparedPassagesArtifact"]).read_bytes()) == result["preparedPassages"]
    (tmp_path / result["metadata"]["sourceMapPath"]).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="artifact hash"):
        load_conversion(str(tmp_path), "a" * 64, b"original-pdf")


def test_cache_rejects_wrong_conversion_profile_and_escaped_path(tmp_path):
    result = sample_result()
    preserve_conversion(str(tmp_path), "a" * 64, b"original-pdf", result)
    manifest = tmp_path / "derived/docling" / ("a" * 64 + ".json")
    alternate = manifest.with_name("b" * 64 + ".json")
    alternate.write_bytes(manifest.read_bytes())
    with pytest.raises(ValueError, match="profile mismatch"):
        load_conversion(str(tmp_path), "b" * 64, b"original-pdf")
    alternate.write_text(json.dumps({"resultPath": "../escaped.bin"}))
    with pytest.raises(ValueError, match="escapes storage"):
        load_conversion(str(tmp_path), "b" * 64, b"original-pdf")


def test_incremental_key_changes_only_with_input_or_conversion_profile():
    options = dict(max_pages=100, max_characters=500000, ocr=False, model_artifacts_hash="model-v1")
    key = conversion_key(b"pdf", **options)
    assert conversion_key(b"pdf", **options) == key
    assert conversion_key(b"changed-pdf", **options) != key
    assert conversion_key(b"pdf", **(options | {"max_pages": 30})) != key
    assert conversion_key(b"pdf", **(options | {"model_artifacts_hash": "model-v2"})) != key
    assert conversion_key(b"pdf", **(options | {"ocr": True})) != key


@pytest.mark.asyncio
async def test_docling_cache_avoids_worker_and_saves_prepared_passages(tmp_path, monkeypatch):
    body = b"original-pdf"
    calls = []
    async def worker(*args, **kwargs):
        calls.append({**kwargs, "args": args})
        assert kwargs["memory_bytes"] > 512 * 1024 * 1024
        assert Path(kwargs["env"]["USERPROFILE"]).is_dir()
        return json.dumps(sample_result(body)).encode()
    models = tmp_path / "models"
    models.mkdir()
    (models / "weights").write_bytes(b"model")
    monkeypatch.setattr(document_parser, "run_bounded_python", worker)
    options = dict(parser="docling", python_executable="isolated-python", artifacts_path=str(models), storage_path=str(tmp_path / "store"))
    first = await document_parser.parse_file(body, "application/pdf", **options)
    second = await document_parser.parse_file(body, "application/pdf", **options)
    assert len(calls) == 1
    assert first["preparedPassages"] == second["preparedPassages"]
    assert second["metadata"]["processing"]["cacheHit"]
    assert not Path(calls[0]["env"]["USERPROFILE"]).exists()
    ocr = await document_parser.parse_file(body, "application/pdf", **options, ocr=True)
    assert len(calls) == 2
    assert "--ocr" not in calls[0]["args"][2]
    assert "--ocr" in calls[1]["args"][2]
    assert ocr["metadata"]["conversionKey"] != first["metadata"]["conversionKey"]


@pytest.mark.asyncio
async def test_docling_missing_runtime_fails_without_legacy_fallback():
    with pytest.raises(AppError) as error:
        await document_parser.parse_file(b"pdf", "application/pdf", parser="docling")
    assert error.value.code == "parser_configuration"
