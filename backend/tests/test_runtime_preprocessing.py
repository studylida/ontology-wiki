import json

import pytest

from knowledge.documents.dto import NewDocument
from knowledge.documents.entities import Passage
from knowledge.documents.parsing import prepared_passages, segment
from knowledge.documents.preprocessing import link_xml, repair_jats, sha, xml_nodes, xml_text
from knowledge.documents.repository import DocumentRepository
from knowledge.documents.runtime_preprocessing import prepare_conversion
from knowledge.integrations import public_fetch
from knowledge.integrations.docling_artifacts import conversion_key, model_fingerprint, preserve_conversion


def pdf_result(raw, *, damaged=True):
    table_text = "| Chip | Current (mA) |\n| 0 283.8 240.9 |\n| 1 254.5 250.6 |" if damaged else "| Chip | Current (mA) |\n| 0 | 283.8 |\n| 1 | 254.5 |"
    content = table_text + "\n\nExperiment: 250°C for 30 min."
    tail_start = content.index("Experiment:")
    records = [{"text": table_text, "locator": "페이지 20 · 표", "start_offset": 0,
                "end_offset": len(table_text), "embedding_text": table_text},
               {"text": content[tail_start:], "locator": "페이지 20 · 본문", "start_offset": tail_start,
                "end_offset": len(content), "embedding_text": content[tail_start:]}]
    source_map = [{"startOffset": r["start_offset"], "endOffset": r["end_offset"], "locator": r["locator"],
                   "documentRefs": ["#/tables/0"] if i == 0 else ["#/texts/1"],
                   "label": "table" if i == 0 else "text", "pageNumbers": [20], "provenance": []}
                  for i, r in enumerate(records)]
    cells = ["0 283.8 240.9", "1 254.5 250.6"] if damaged else ["283.8", "254.5"]
    return {"title": "Experiment", "content": content, "readScope": "full", "limitations": [],
            "metadata": {"sourceSha256": sha(raw), "parserProfile": {"version": "2.143.0"}},
            "structuredDocument": {"texts": [{"self_ref": "#/texts/0", "text": "Table 1: Current at 250°C (mA)"}],
                "tables": [{"self_ref": "#/tables/0", "prov": [{"page_no": 20}],
                            "captions": [{"$ref": "#/texts/0"}],
                            "data": {"table_cells": [{"text": t, "start_row_offset_idx": i} for i, t in enumerate(cells)]}}]},
            "sourceMap": source_map, "preparedPassages": records}


@pytest.mark.asyncio
async def test_real_repository_receives_held_passage_and_preserves_clean_passage():
    result = prepare_conversion(pdf_result(b"original"), b"original")
    assert "Table 1: Current at 250°C (mA)" in result["preparedPassages"][0]["text"]
    assert result["metadata"]["preprocessingQuality"]["heldPassages"] == 1
    assert result["readScope"] == "partial"
    clean = prepared_passages(result["content"], result["preparedPassages"])
    assert clean[0].excluded and clean[0].exclusion_reason and not clean[1].excluded

    class Session:
        def __init__(self): self.items = []
        def add(self, item): self.items.append(item)
        async def flush(self): pass
    class Principal:
        id = "user"
    session = Session()
    await DocumentRepository(session).create_source(Principal(), NewDocument(title="Experiment", content=result["content"]),
        "preserved-original", processing_metadata=result["metadata"], passage_records=result["preparedPassages"])
    stored = [item for item in session.items if isinstance(item, Passage)]
    assert len(stored) == 2 and stored[0].excluded and not stored[1].excluded
    assert stored[0].exclusion_reason == "전처리 구조 또는 수식 확인 필요"


@pytest.mark.asyncio
async def test_repository_holds_docling_content_without_structure_records():
    class Session:
        def __init__(self): self.items = []
        def add(self, item): self.items.append(item)
        async def flush(self): pass
    class Principal:
        id = "user"
    session = Session()
    await DocumentRepository(session).create_source(Principal(), NewDocument(title="문헌", content="표 자료"),
        "raw", processing_metadata={"parserProfile": {"engine": "docling"}, "preprocessingQuality": {"version": 2}})
    stored = [item for item in session.items if isinstance(item, Passage)]
    assert len(stored) == 1 and stored[0].excluded
    assert stored[0].exclusion_reason == "이전 구조 추출본의 전처리 검토 필요"


def test_normal_table_is_not_held_and_caption_keeps_source_offsets():
    result = prepare_conversion(pdf_result(b"original", damaged=False), b"original")
    assert result["metadata"]["preprocessingQuality"]["issues"] == []
    assert result["metadata"]["preprocessingQuality"]["heldPassages"] == 0
    assert "Table 1: Current at 250°C (mA)" in result["preparedPassages"][0]["text"]
    assert all(result["content"][p["start_offset"]:p["end_offset"]] == p["text"] for p in result["preparedPassages"])


@pytest.mark.parametrize("empty", [False, True])
def test_missing_table_structure_is_held(empty):
    data = pdf_result(b"original", damaged=False)
    if empty:
        data["structuredDocument"]["tables"][0]["data"]["table_cells"] = []
    else:
        data["structuredDocument"]["tables"][0].pop("data")
    result = prepare_conversion(data, b"original")
    assert result["metadata"]["preprocessingQuality"]["heldPassages"] == 1
    assert result["metadata"]["preprocessingQuality"]["issues"][0]["reason"] == "table_structure_missing"


@pytest.mark.asyncio
async def test_legacy_cache_is_reused_without_mutating_old_artifacts(tmp_path, monkeypatch):
    raw = b"original"
    models = tmp_path / "models"
    models.mkdir()
    (models / "weights").write_bytes(b"weights")
    storage = tmp_path / "store"
    key = conversion_key(raw, max_pages=100, max_characters=500000, ocr=False, model_artifacts_hash=model_fingerprint(str(models)))
    old = pdf_result(raw)
    old["metadata"]["processing"] = {"elapsedMs": 1, "cacheHit": False}
    preserve_conversion(str(storage), key, raw, old)
    manifest = storage / "derived/docling" / (key + ".json")
    before = manifest.read_bytes()
    async def no_worker(*args, **kwargs):
        raise AssertionError("Existing PDF conversion must be reused")
    monkeypatch.setattr(public_fetch, "run_bounded_python", no_worker)
    result = await public_fetch.parse_download(raw, "application/pdf", parser="docling", python_executable="unused",
        artifacts_path=str(models), storage_path=str(storage))
    assert result["metadata"]["preprocessingQuality"]["heldPassages"] == 1
    assert result["metadata"]["conversionKey"] != key
    assert manifest.read_bytes() == before
    saved = json.loads((storage / result["metadata"]["preparedPassagesArtifact"]).read_bytes())
    assert saved[0]["qualityHold"] and not saved[1].get("qualityHold")


def test_unique_literal_fragment_maps_original_xml_but_ambiguous_text_does_not():
    prefix = "The four experimentally measured factors were carefully selected for the process conditions "
    raw = (f"<article><body><sec id='methods'><p>{prefix}<math><msub><mi>a</mi><mi>i</mi></msub></math> were measured.</p></sec></body></article>").encode()
    blocks = [{"text": prefix + "a_{i} were measured.", "documentRefs": []}]
    result = {"structuredDocument": {"texts": []}}
    link_xml(blocks, result, raw)
    assert blocks[0]["rawXmlLocations"][0]["matchMethod"] == "unique_literal_fragment"
    assert "local-name()='p'" in blocks[0]["rawXmlLocations"][0]["xpath"]
    duplicate = raw.replace(b"</sec>", (f"<p>{prefix}<math><mi>x</mi></math> were measured.</p></sec>").encode())
    blocks = [{"text": prefix + "a_{i} were measured.", "documentRefs": []}]
    link_xml(blocks, result, duplicate)
    assert not blocks[0].get("rawXmlLocations")


def test_unique_plain_fragment_after_chemical_subscript_maps_only_its_original_paragraph():
    before = "A brief explanation of Al"
    after = "deposition conditions were measured carefully for every specimen during the experiment."
    raw = f"<article><body><p>{before}<sub>2</sub>O<sub>3</sub> {after}</p></body></article>".encode()
    blocks = [{"text": before + "₂O₃ " + after, "documentRefs": []}]
    result = {"structuredDocument": {"texts": []}}
    assert not link_xml(blocks, result, raw)["unmatchedParagraphs"]
    assert blocks[0]["rawXmlLocations"][0]["matchMethod"] == "unique_literal_fragment"
    duplicate = raw.replace(b"</body>", f"<p>Another Al<sub>2</sub>O<sub>3</sub> {after}</p></body>".encode())
    blocks = [{"text": before + "₂O₃ " + after, "documentRefs": []}]
    link_xml(blocks, result, duplicate)
    assert not blocks[0].get("rawXmlLocations")


def test_formula_hash_location_requires_unique_original_formula_and_passage():
    raw = b'<article><body><p>Formula: <math id="m1"><mi>symbol</mi></math></p></body></article>'
    notation = r'\frac{very_long_experimental_measurement}{reference_condition}'
    entry = {"xmlId": "m1", "sha256": sha(notation.encode()), "length": len(notation)}
    result = {"structuredDocument": {"texts": []}, "metadata": {"mathmlNotationHashes": [entry]}}
    blocks = [{"text": "$$" + notation + "$$", "documentRefs": []}]
    link_xml(blocks, result, raw)
    location = blocks[0]["rawXmlLocations"][0]
    assert location["matchMethod"] == "unique_formula_hash" and location["formulaXmlId"] == "m1"
    ambiguous = {**result, "metadata": {"mathmlNotationHashes": [entry, {**entry, "xmlId": "m2"}]}}
    blocks = [{"text": "$$" + notation + "$$", "documentRefs": []}]
    link_xml(blocks, ambiguous, raw)
    assert not blocks[0].get("rawXmlLocations")
    blocks = [{"text": "$$" + notation + "$$", "documentRefs": []} for _ in range(2)]
    link_xml(blocks, result, raw)
    assert all(not block.get("rawXmlLocations") for block in blocks)


def test_short_ambiguous_paragraphs_are_reported_as_unmatched():
    raw = b'<article><notes><p>Not applicable.</p></notes><notes><p>Not applicable.</p></notes></article>'
    blocks = [{"text": "Not applicable.\nNot applicable.", "documentRefs": []}]
    mapping = link_xml(blocks, {"structuredDocument": {"texts": []}}, raw)
    assert len(mapping["unmatchedParagraphs"]) == 2 and not blocks[0].get("rawXmlLocations")
    same = b"<article><body><p>This complete paragraph is identical in two different original sections.</p><p>This complete paragraph is identical in two different original sections.</p></body></article>"
    blocks = [{"text": "This complete paragraph is identical in two different original sections.", "documentRefs": []}]
    link_xml(blocks, {"structuredDocument": {"texts": []}}, same)
    assert not blocks[0].get("rawXmlLocations")


def test_titled_note_requires_unique_title_and_parent_reference():
    raw = b'<article><back><notes><title>Ethics</title><p>Not applicable.</p></notes><notes><title>Consent</title><p>Not applicable.</p></notes></back></article>'
    items = [{'self_ref': '#/texts/0', 'label': 'section_header', 'text': 'Ethics'},
             {'self_ref': '#/texts/1', 'label': 'text', 'text': 'Not applicable.', 'parent': {'$ref': '#/texts/0'}},
             {'self_ref': '#/texts/2', 'label': 'section_header', 'text': 'Consent'},
             {'self_ref': '#/texts/3', 'label': 'text', 'text': 'Not applicable.', 'parent': {'$ref': '#/texts/2'}}]
    result = {'structuredDocument': {'texts': items}}
    blocks = [{'text': 'Ethics\nNot applicable.', 'documentRefs': ['#/texts/1']},
              {'text': 'Consent\nNot applicable.', 'documentRefs': ['#/texts/3']}]
    assert not link_xml(blocks, result, raw)['unmatchedParagraphs']
    assert all(block['rawXmlLocations'][0]['matchMethod'] == 'unique_titled_note' for block in blocks)
    ambiguous = raw.replace(b'Consent', b'Ethics')
    blocks = [{'text': 'Ethics\nNot applicable.', 'documentRefs': ['#/texts/1']}]
    assert len(link_xml(blocks, result, ambiguous)['unmatchedParagraphs']) == 2


def test_math_display_and_table_formula_are_held_without_holding_clean_text():
    raw = b'<article><body><p>Source</p></body></article>'
    normalized = '<article><body><tex-math>{x}_{i}</tex-math><tex-math>\\frac{a}{b}</tex-math></body></article>'
    values = ['Condition 250°C.', '$${x}_{i}$$', '| Value |\n| --- |\n| \\frac{a}{b} |']
    content = '\n\n'.join(values)
    starts = [content.index(value) for value in values]
    records = [{'text': value, 'locator': 'source', 'start_offset': start, 'end_offset': start + len(value), 'embedding_text': value}
               for value, start in zip(values, starts)]
    source_map = [{'startOffset': r['start_offset'], 'endOffset': r['end_offset'], 'locator': 'source',
                   'documentRefs': [], 'label': 'text', 'pageNumbers': [], 'provenance': []} for r in records]
    data = {'title': 'source', 'content': content, 'readScope': 'full', 'limitations': [],
            'metadata': {'sourceSha256': sha(raw), 'parserInputSha256': sha(normalized.encode()), 'mathmlNotationConverted': 2},
            'normalizedXml': normalized, 'structuredDocument': {'texts': [], 'tables': []},
            'sourceMap': source_map, 'preparedPassages': records}
    result = prepare_conversion(data, raw, jats=True)
    assert [bool(p.get('qualityHold')) for p in result['preparedPassages']] == [False, True, True]
    assert [p.excluded for p in prepared_passages(result['content'], result['preparedPassages'])] == [False, True, True]
    assert any(issue['reason'] == 'math_display_requires_review' for issue in result['metadata']['preprocessingQuality']['issues'])
    data['metadata']['parserInputSha256'] = 'invalid'
    assert prepare_conversion(data, raw, jats=True)['metadata']['preprocessingQuality']['heldPassages'] == 3


@pytest.mark.parametrize("lost", ["105 mA", "10.5 mA"])
def test_xml_caption_numeric_sign_and_decimal_mismatch_stays_on_hold(lost):
    raw = b'<article><body><fig id="f1"><label>Figure 1</label><caption><p>Measured current was &#8722;10.5 mA.</p></caption></fig></body></article>'
    old = "Figure 1 Measured current was " + lost + "."
    data = {"title": "Example", "content": old, "readScope": "full", "limitations": [],
            "metadata": {"sourceSha256": sha(raw)},
            "structuredDocument": {"tables": [], "texts": [{"self_ref": "#/texts/0", "label": "caption", "text": old}]},
            "sourceMap": [{"startOffset": 0, "endOffset": len(old), "label": "caption", "locator": "Figure 1",
                "documentRefs": ["#/texts/0"], "pageNumbers": [], "provenance": []}],
            "preparedPassages": [{"text": old, "locator": "Figure 1", "start_offset": 0,
                "end_offset": len(old), "embedding_text": old}]}
    result = prepare_conversion(data, raw, jats=True)
    assert result["metadata"]["preprocessingQuality"]["heldPassages"] == 1
    assert result["preparedPassages"][0]["text"] == old
    assert not result["sourceMap"][0].get("rawXmlLocations")


def test_duplicate_original_caption_is_not_assigned_a_location():
    raw = b'<article><fig id="first"><caption><p>Same caption.</p></caption></fig><fig id="second"><caption><p>Same caption.</p></caption></fig></article>'
    data = {"structuredDocument": {"texts": [{"self_ref": "#/texts/0", "label": "caption", "text": "Same caption."}]},
            "sourceMap": [{"documentRefs": ["#/texts/0"]}], "preparedPassages": [{"text": "Same caption."}]}
    result, edits, unresolved = repair_jats(data, raw)
    assert len(unresolved) == 2 and not edits
    assert "rawXmlLocation" not in result["structuredDocument"]["texts"][0]


def test_unique_caption_reference_connects_its_only_original_paragraph():
    raw = b'<article><fig id="f"><caption><p>Short <sup>2</sup> caption.</p></caption></fig></article>'
    path = "/*[local-name()='article'][1]/*[local-name()='fig'][1]"
    result = {"structuredDocument": {"texts": [{"self_ref": "#/texts/0", "rawXmlLocation": {"xmlId": "f", "xpath": path}}]}}
    blocks = [{"text": "Short ² caption.", "documentRefs": ["#/texts/0"]}]
    link_xml(blocks, result, raw)
    paragraph = next(loc for loc in blocks[0]["rawXmlLocations"] if loc.get("matchMethod") == "unique_caption_reference")
    assert paragraph["xpath"].endswith("/*[local-name()='caption'][1]/*[local-name()='p'][1]")


def test_caption_repair_never_changes_unrelated_passages():
    raw = b'<article xmlns:m="http://www.w3.org/1998/Math/MathML"><fig id="f"><caption><p>Factor <m:math><m:msub><m:mi>a</m:mi><m:mi>i</m:mi></m:msub></m:math> was measured.</p></caption></fig></article>'
    old = "Factor  was measured."
    data = {"structuredDocument": {"texts": [{"self_ref": "#/texts/0", "label": "caption", "text": old}]},
            "sourceMap": [{"documentRefs": ["#/texts/0"]}, {"documentRefs": ["#/texts/1"]}],
            "preparedPassages": [{"text": old}, {"text": old}]}
    result, edits, unresolved = repair_jats(data, raw)
    assert edits and not unresolved
    assert result["preparedPassages"][0]["text"] == "Factor aᵢ was measured."
    assert result["preparedPassages"][1]["text"] == old


@pytest.mark.parametrize("original,extracted", [("m<sup>2</sup>", "m2"), ("a<sub>i</sub>", "ai")])
def test_caption_scripts_are_not_confused_with_plain_characters(original, extracted):
    raw = f'<article><fig><caption><p>Value {original}.</p></caption></fig></article>'.encode()
    old = f"Value {extracted}."
    data = {"structuredDocument": {"texts": [{"self_ref": "#/texts/0", "label": "caption", "text": old}]},
            "sourceMap": [{"documentRefs": ["#/texts/0"]}], "preparedPassages": [{"text": old}]}
    result, edits, unresolved = repair_jats(data, raw)
    assert unresolved and not edits and result["preparedPassages"][0]["text"] == old


def test_mathml_direct_text_is_preserved_or_flagged():
    raw = b"<math><mrow><mi>a</mi> + <mi>b</mi></mrow></math>"
    assert xml_text(xml_nodes(raw)[0][0]) == "a + b"
    malformed = b"<math><msub><mi>a</mi> + <mi>i</mi></msub></math>"
    with pytest.raises(ValueError, match="manual review"):
        xml_text(xml_nodes(malformed)[0][0])
    unsupported = b'<m:math xmlns:m="http://www.w3.org/1998/Math/MathML"><m:mfenced><m:mi>x</m:mi></m:mfenced></m:math>'
    with pytest.raises(ValueError, match="manual review"):
        xml_text(xml_nodes(unsupported)[0][0])
    with pytest.raises(ValueError, match="manual review"):
        xml_text(xml_nodes(b'<math><mfenced><mi>x</mi></mfenced></math>')[0][0])


def test_real_markdown_segmentation_preserves_table_caption_and_technical_notes():
    paragraph = "실험 조건 250°C, 30 min. " * 20
    table = "| 온도 | 결과 |\n| --- | --- |\n| 250°C | 31.24% |"
    source = "# 실험\n\n" + paragraph + "\n\n표 1: 온도별 결과 (단위 %).\n\n" + table + "\n\n* 측정 조건 주석.\n\n## 원문·편집 계보\n\n편집자 메모."
    chunks = segment(source, "실험", max_chars=80)
    text = "\n".join(p.text for p in chunks)
    assert "* 측정 조건 주석" in text and "편집자 메모" not in text
    assert any("표 1:" in p.text and table in p.text and "* 측정 조건 주석" in p.text for p in chunks)
    assert all(source[p.start_offset:p.end_offset] == p.text for p in chunks)


def test_oversized_single_paragraph_is_preserved_but_not_indexable():
    source = "기술 설명. " * 10000
    passage = segment(source, "문헌")[0]
    assert source[passage.start_offset:passage.end_offset] == passage.text
    assert passage.excluded and passage.exclusion_reason == "긴 문단 또는 표의 분할 검토 필요"


def test_table_caption_repeated_on_each_split_passage():
    result = pdf_result(b"original", damaged=False)
    first = "Table 1: Current at 250°C (mA)\n\n| Chip | Current (mA) |\n| 0 | 283.8 |"
    second = "| Chip | Current (mA) |\n| 1 | 254.5 |"
    result["content"] = first + "\n\n" + second
    for i, (record, source, value, start) in enumerate(zip(result["preparedPassages"], result["sourceMap"],
            [first, second], [0, len(first) + 2], strict=True)):
        record.update(text=value, start_offset=start, end_offset=start + len(value), embedding_text=value)
        source.update(startOffset=start, endOffset=start + len(value), documentRefs=["#/tables/0"], label="table")
    converted = prepare_conversion(result, b"original")
    assert all("Table 1: Current at 250°C (mA)" in p["text"] for p in converted["preparedPassages"])
    assert all(converted["content"][p["start_offset"]:p["end_offset"]] == p["text"] for p in converted["preparedPassages"])


@pytest.mark.asyncio
async def test_xml_requires_jats_parser_and_never_accepts_ocr():
    with pytest.raises(Exception) as missing:
        await public_fetch.parse_download(b"<article/>", "application/xml")
    assert missing.value.code == "parser_configuration"
    with pytest.raises(Exception) as invalid:
        await public_fetch.parse_download(b"<article/>", "application/xml", parser="docling", ocr=True)
    assert invalid.value.code == "parser_configuration"
