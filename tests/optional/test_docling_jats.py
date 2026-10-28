"""Optional installed-runtime contract test; API environments stay ML-free."""
import hashlib
import json
import os
import re
from pathlib import Path

import pytest

from knowledge.integrations.bounded_process import BoundedProcessError, run_bounded_python
from knowledge.integrations.document_parser import _parser_environment


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = Path(os.environ.get("OW_TEST_DOCLING_PYTHON", ROOT / "var/runtimes/docling/Scripts/python.exe"))
MODELS = Path(os.environ.get("OW_TEST_DOCLING_MODELS", ROOT / "var/models/docling"))
pytestmark = pytest.mark.skipif(not RUNTIME.exists(), reason="isolated Docling runtime not installed")

ARTICLE = """<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
<record><metadata><article xmlns="https://jats.nlm.nih.gov/ns/archiving/1.4/"
 xmlns:mml="http://www.w3.org/1998/Math/MathML" xmlns:xlink="http://www.w3.org/1999/xlink">
<front><journal-meta><journal-title-group><journal-title>Example</journal-title>
</journal-title-group></journal-meta><article-meta><title-group>
<article-title>Al<sub>2</sub>O<sub>3</sub> experiment</article-title></title-group></article-meta></front>
<body><sec id="methods"><title>Methods</title><p>Bond at 250 °C for 0.5 h.
PRBS <inline-formula><mml:math><mml:msup><mml:mn>2</mml:mn><mml:mn>31</mml:mn>
</mml:msup><mml:mo>−</mml:mo><mml:mn>1</mml:mn></mml:math></inline-formula>.</p></sec>
<sec id="conclusion"><title>Conclusion</title><p>Specimen-specific observation.</p></sec></body>
<floats-group><table-wrap id="table1"><label>Table 1</label><caption><p>250 °C for 0.5 h.</p></caption>
<table><thead><tr><th>Thickness µm</th><th>Bonded fraction %</th></tr></thead>
<tbody><tr><td>0.8</td><td>31.24</td></tr></tbody></table></table-wrap>
<fig id="figure1"><label>Figure 1</label><caption><p>Cross section.</p></caption>
<graphic xlink:href="https://example.invalid/never-fetch.png"/></fig></floats-group>
</article></metadata></record></OAI-PMH>"""


async def convert(raw, tmp_path):
    env = _parser_environment()
    env.update(USERPROFILE=str(tmp_path), HF_HOME=str(tmp_path / "hf"))
    return await run_bounded_python(str(RUNTIME), "knowledge.integrations.docling_jats",
        [str(MODELS), "--max-characters", "24680"], input_bytes=raw, env=env, timeout_seconds=60, cpu_seconds=60,
        memory_bytes=4 * 1024**3, max_output_bytes=4 * 1024**2)


@pytest.mark.asyncio
async def test_jats_original_hash_float_table_math_and_exact_offsets(tmp_path):
    raw = ARTICLE.encode()
    result = json.loads(await convert(raw, tmp_path))
    assert result["title"] == "Al2O3 experiment"
    assert result["metadata"]["sourceSha256"] == hashlib.sha256(raw).hexdigest()
    assert result["metadata"]["parserInputSha256"] == hashlib.sha256(result["normalizedXml"].encode()).hexdigest()
    assert result["metadata"]["relocatedFloatElements"] == 2
    assert result["metadata"]["parserProfile"]["maxCharacters"] == 24680
    assert result["metadata"]["tableCount"] == result["metadata"]["pictureCount"] == 1
    assert "{2}^{31}−1" in re.sub(r"\s", "", result["content"])
    table = next(p for p in result["preparedPassages"] if "31.24" in p["text"])
    assert "250 °C" in table["text"] and "0.5 h" in table["text"]
    assert "Conclusion" not in table["locator"]
    for passage in result["preparedPassages"]:
        assert result["content"][passage["start_offset"]:passage["end_offset"]] == passage["text"]
        assert passage["input_hash"] == hashlib.sha256(passage["embedding_text"].encode()).hexdigest()
    assert result["readScope"] == "partial"


@pytest.mark.asyncio
async def test_titled_notes_survive_and_identical_short_paragraphs_link_by_parent(tmp_path):
    from knowledge.documents.runtime_preprocessing import prepare_conversion
    notes = ('<back><notes><title>Ethics review</title><p>Not applicable.</p></notes>'
             '<notes><title>Consent statement</title><p>Not applicable.</p></notes></back>')
    raw = ARTICLE.replace('</article>', notes + '</article>').encode()
    converted = json.loads(await convert(raw, tmp_path))
    prepared = prepare_conversion(converted, raw, jats=True)
    assert converted['metadata']['titledNotesConverted'] == 2
    for heading, index in [('Ethics review', 1), ('Consent statement', 2)]:
        matches = [(p, s) for p, s in zip(prepared['preparedPassages'], prepared['sourceMap']) if heading in p['text']]
        assert len(matches) == 1 and 'Not applicable.' in matches[0][0]['text']
        assert any(loc.get('matchMethod') == 'unique_titled_note' and f"/*[local-name()='notes'][{index}]" in loc['xpath'] for loc in matches[0][1].get('rawXmlLocations', []))


@pytest.mark.asyncio
async def test_jats_preserves_math_text_and_holds_unsupported_semantics(tmp_path):
    from knowledge.documents.runtime_preprocessing import prepare_conversion
    body = ('<inline-formula><mml:math><mml:mrow><mml:mi>a</mml:mi> + <mml:mi>b</mml:mi></mml:mrow></mml:math></inline-formula>'
            '<inline-formula><mml:math><mml:semantics><mml:mi>x</mml:mi><mml:annotation>source</mml:annotation></mml:semantics></mml:math></inline-formula>'
            '<inline-formula><mml:math><mml:msub><mml:mi>a</mml:mi><mml:mi>b</mml:mi><mml:mi>c</mml:mi></mml:msub></mml:math></inline-formula>')
    raw = ARTICLE.replace('Specimen-specific observation.', body).encode()
    result = json.loads(await convert(raw, tmp_path))
    assert 'a + b' in result['normalizedXml']
    assert result['metadata']['mathmlPreservedAsXml'] == 2
    assert 'annotation' in result['normalizedXml'] and 'msub' in result['normalizedXml']
    prepared = prepare_conversion(result, raw, jats=True)
    assert prepared['metadata']['preprocessingQuality']['heldPassages'] == len(prepared['preparedPassages'])


@pytest.mark.asyncio
async def test_jats_fences_and_overmarks_keep_structure_and_unsupported_layout_is_held(tmp_path):
    body = ('<inline-formula><mml:math id="fenced"><mml:mfenced open="[" close="]"><mml:mi>x</mml:mi></mml:mfenced></mml:math></inline-formula>'
            '<inline-formula><mml:math id="over"><mml:mover accent="true"><mml:mi>y</mml:mi><mml:mo>^</mml:mo></mml:mover></mml:math></inline-formula>'
            '<inline-formula><mml:math id="rows"><mml:mtable columnalign="left"><mml:mtr><mml:mtd><mml:mi>x</mml:mi></mml:mtd></mml:mtr><mml:mtr><mml:mtd><mml:mi>y</mml:mi></mml:mtd></mml:mtr></mml:mtable></mml:math></inline-formula>'
            '<inline-formula><mml:math id="sum"><mml:munderover><mml:mo>∑</mml:mo><mml:mi>i</mml:mi><mml:mi>n</mml:mi></mml:munderover></mml:math></inline-formula>'
            '<inline-formula><mml:math id="unknown"><mml:mtable><mml:mtr><mml:mtd><mml:mi>x</mml:mi></mml:mtd><mml:mtd><mml:mi>y</mml:mi></mml:mtd></mml:mtr></mml:mtable></mml:math></inline-formula>'
            '<inline-formula><mml:math id="multi"><mml:mfenced><mml:mi>x</mml:mi><mml:mi>y</mml:mi></mml:mfenced></mml:math></inline-formula>'
            '<inline-formula><mml:math id="nested"><mml:mi><mml:mglyph alt="x"/></mml:mi></mml:math></inline-formula>')
    raw = ARTICLE.replace('Specimen-specific observation.', body).encode()
    result = json.loads(await convert(raw, tmp_path))
    assert '[x]' in result['normalizedXml']
    assert r'\hat{y}' in result['normalizedXml']
    assert r'\begin{aligned}&x\\&y\end{aligned}' in result['content']
    assert r'\sum\limits_{i}^{n}' in result['normalizedXml']
    assert result['metadata']['mathmlPreservedAsXml'] == 3
    assert [x['xmlId'] for x in result['metadata']['mathmlFallbackDetails']] == ['unknown', 'multi', 'nested']


@pytest.mark.asyncio
@pytest.mark.parametrize("encoding", ["utf-8", "utf-16"])
async def test_jats_rejects_entity_declarations_including_utf16(tmp_path, encoding):
    malicious = '<!DOCTYPE article [<!ENTITY xxe SYSTEM "file:///never-read">]><article>&xxe;</article>'
    with pytest.raises(BoundedProcessError, match="process_failed"):
        await convert(malicious.encode(encoding), tmp_path)
