import copy
import importlib.util
import json
from pathlib import Path

import pytest

from knowledge.documents.preprocessing import (
    apply_table_repairs, assemble, docling_blocks, group_markdown, link_xml,
    markdown_blocks, repair_jats, sha, xml_nodes,
)


def test_paragraphs_tables_and_meaningful_notes_stay_intact():
    paragraph = "공정 조건 800~1,200℃에서 SiO₂를 형성한다. " * 90
    table = "| 조건 | 결과 |\n| --- | --- |\n" + "| 250°C, 30 min | 31.24% |\n" * 90
    text = "# 실험\n\n" + paragraph + "\n\n" + table + "\n*Si₃N₄: 의미 있는 소재 주석.\n\n※ 외부 필자 의견.\n\n## 원문·편집 계보\n\n원문: https://example.org\n"
    blocks, notes = markdown_blocks(text)
    chunks = group_markdown(blocks)
    assert any(c["text"] == paragraph.strip() for c in chunks)
    assert any(table.strip() in c["text"] for c in chunks)
    content, passages = assemble(chunks, "실험", {"inputSha256": sha(text.encode())})
    assert "*Si₃N₄" in content and "※ 외부 필자 의견" in content
    assert "원문: https" not in content
    assert "원문: https" in "\n".join(n["text"] for n in notes)
    assert all(content[p["start_offset"]:p["end_offset"]] == p["text"] for p in passages)
    assert passages[1]["previousId"] == passages[0]["id"]


def test_crlf_offsets_code_and_navigation():
    text = '---\r\nsource_url: example\r\n---\r\n# 본문\r\n\r\n```text\r\n## 검토 메모\r\n250°C\r\n```\r\n\r\n공유하기\r\n\r\n검토 메모라는 단어가 있는 기술 본문.\r\n'
    blocks, notes = markdown_blocks(text)
    assert any("250°C" in b["text"] for b in blocks)
    assert any("기술 본문" in b["text"] for b in blocks)
    assert len(notes) == 1 and notes[0]["text"] == "공유하기"
    assert all(text[b["inputStart"]:b["inputEnd"]] == b["text"] for b in blocks + notes)
    adjacent = "Technical paragraph.\n```text\n## 검토 메모\n250°C is technical code\n```\n"
    blocks, notes = markdown_blocks(adjacent)
    assert not notes and "250°C" in "\n".join(b["text"] for b in blocks)


def caption_fixture():
    old = "Figure 12 Measured insertion losses () of the TSV channels."
    body = "Experimental conditions and results refer to Figure 12."
    return {"structuredDocument": {"texts": [{"self_ref": "#/texts/0", "label": "caption", "text": old}]},
            "preparedPassages": [{"text": body}, {"text": old}],
            "sourceMap": [{"documentRefs": [], "startOffset": 0, "endOffset": len(body), "locator": "Methods", "pageNumbers": [], "provenance": [], "label": "paragraph"},
                          {"documentRefs": ["#/texts/0"], "startOffset": 100, "endOffset": 100 + len(old), "locator": "Figures", "pageNumbers": [], "provenance": [], "label": "caption"}]}


def test_caption_symbol_repair_and_raw_xml_references():
    raw = b'''<article xmlns:m="http://www.w3.org/1998/Math/MathML"><body><p id="p1">Experimental conditions and results refer to <xref rid="f12">Figure 12</xref>.</p></body><floats-group><fig id="f12"><label>Figure 12</label><caption><p>Measured insertion losses (<m:math><m:msub><m:mi>S</m:mi><m:mn>21</m:mn></m:msub></m:math>) of the TSV channels.</p></caption></fig></floats-group></article>'''
    original = caption_fixture()
    repaired, edits, unresolved = repair_jats(original, raw)
    assert not unresolved and len(edits) == 1
    assert "S₂₁" in repaired["preparedPassages"][1]["text"]
    assert "S₂₁" not in original["preparedPassages"][1]["text"]
    blocks = docling_blocks(repaired)
    link_xml(blocks, repaired, raw)
    assert blocks[0]["relatedOrdinals"] == [1]
    assert blocks[1]["relatedOrdinals"] == [0]
    assert blocks[1]["rawXmlLocations"][0]["xmlId"] == "f12"


def test_complex_caption_math_and_entities_fail_without_invention():
    raw = b'<article><fig id="f"><caption><math><mfrac><mi>a</mi><mi>b</mi></mfrac></math></caption></fig></article>'
    result, edits, unresolved = repair_jats(caption_fixture(), raw)
    assert not edits and unresolved[0]["reason"] == "complex_caption_math_preserved_in_original"
    assert result["preparedPassages"] == caption_fixture()["preparedPassages"]
    for raw in [b'<!DOCTYPE article [<!ENTITY secret "private">]><article>&secret;</article>',
                '<!DOCTYPE article [<!ENTITY secret "private">]><article>&secret;</article>'.encode('utf-16')]:
        with pytest.raises(ValueError, match="entities"):
            xml_nodes(raw)


def test_reviewed_table_repair_preserves_values_and_repeats_conditions():
    table = {"self_ref": "#/tables/0"}
    old_rows = ["0 2.0 ± 0.1 3.0 ± 0.2 50.0", "All chips 2.1 ± 0.1 3.1 ± 0.2 47.6"]
    result = {"structuredDocument": {"tables": [table]}, "preparedPassages": [{"text": "Results\n| " + old + " |"} for old in old_rows],
              "sourceMap": [{"documentRefs": ["#/tables/0"]}] * 2}
    repair = {"documentRef": "#/tables/0", "tableSha256": sha(json.dumps(table, sort_keys=True, ensure_ascii=False).encode()),
              "beforeRows": old_rows, "rows": [["0", "2.0 ± 0.1", "3.0 ± 0.2", "50.0"], ["All chips", "2.1 ± 0.1", "3.1 ± 0.2", "47.6"]],
              "columns": ["Chip", "IDD4R (mA)", "Pattern (mA)", "Increase (%)"], "caption": "Table 10; 35 chips; average ± SD"}
    fixed, edits = apply_table_repairs(result, [repair])
    assert len(edits) == 1 and all("35 chips" in p["text"] for p in fixed["preparedPassages"])
    assert "| All chips | 2.1 ± 0.1 |" in fixed["preparedPassages"][1]["text"]
    broken = copy.deepcopy(repair)
    broken["rows"][0][1] = "-2.0 ± 0.1"
    with pytest.raises(ValueError, match="changes cell values"):
        apply_table_repairs(result, [broken])
    broken = copy.deepcopy(repair)
    broken["tableSha256"] = "changed"
    with pytest.raises(ValueError, match="table changed"):
        apply_table_repairs(result, [broken])
    unknown = copy.deepcopy(result)
    unknown["preparedPassages"][0]["text"] += "\n| IMPORTANT 900 mA |"
    with pytest.raises(ValueError, match="Unreviewed"):
        apply_table_repairs(unknown, [repair])
    signed = copy.deepcopy(result)
    signed["preparedPassages"][0]["text"] = signed["preparedPassages"][0]["text"].replace("2.0", "-2.0")
    with pytest.raises(ValueError, match="Unreviewed"):
        apply_table_repairs(signed, [repair])


def test_cli_hash_guards_new_directory_and_roundtrip(tmp_path):
    path = Path(__file__).parents[2] / "scripts/v2/preprocess_documents.py"
    spec = importlib.util.spec_from_file_location("preprocess_cli", path)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    source = tmp_path / "source.md"
    source.write_bytes("# 온도\r\n\r\n250°C, 30 min.\r\n".encode("utf-8"))
    entry = {"path": str(source), "sha256": sha(source.read_bytes())}
    manifest = tmp_path / "manifest.json"
    record = {"id": "sample", "format": "markdown", "original": entry, "input": entry,
              "lineageKey": "sample-lineage", "documentForm": "original", "title": "Example"}
    manifest.write_text(json.dumps({"documents": [record]}), encoding="utf-8")
    output = tmp_path / "output"
    assert cli.prepare(manifest, output)[0]["passages"] == 1
    candidates = [json.loads(line) for line in (output / "index-candidates.jsonl").read_bytes().splitlines()]
    assert candidates[0]["indexingDisposition"] == "candidate_for_index_review"
    assert (output / "sample/original.md").read_bytes() == source.read_bytes()
    stored = (output / "sample/clean.md").read_bytes()
    metadata = json.loads((output / "sample/provenance.json").read_bytes())
    assert sha(stored) == metadata["cleanSha256"]
    for passage in json.loads((output / "sample/passages.json").read_bytes()):
        assert stored.decode()[passage["start_offset"]:passage["end_offset"]] == passage["text"]
        for span in passage["sourceSpans"]:
            assert source.read_bytes().decode()[span["start"]:span["end"]] in passage["text"]
    with pytest.raises(ValueError, match="new directory"):
        cli.prepare(manifest, output)
    source.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        cli.prepare(manifest, tmp_path / "another")
    assert not (tmp_path / "another").exists()
