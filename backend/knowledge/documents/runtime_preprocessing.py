"""Apply source-preserving preprocessing before a Docling result is stored or transferred."""
from __future__ import annotations

import copy
import xml.etree.ElementTree as ET

from knowledge.documents.parsing import prepared_passages
from knowledge.documents.preprocessing import assemble, docling_blocks, link_xml, repair_jats, sha, table_reprocessing_candidates


def prepare_conversion(result: dict, raw: bytes, *, jats: bool = False) -> dict:
    result = copy.deepcopy(result)
    if result["metadata"]["sourceSha256"] != sha(raw):
        raise ValueError("Docling source hash mismatch")
    records, sources = result["preparedPassages"], result["sourceMap"]
    prepared_passages(result["content"], records)
    if len(records) != len(sources):
        raise ValueError("Docling source map length mismatch")
    for record, source in zip(records, sources, strict=True):
        if (record["start_offset"], record["end_offset"]) != (source["startOffset"], source["endOffset"]):
            raise ValueError("Docling source map differs from passage offsets")

    document = result["structuredDocument"]
    captions = {item["self_ref"]: item.get("text", "") for item in document.get("texts", [])}
    tables = {item["self_ref"]: item for item in document.get("tables", []) if "self_ref" in item}
    changed = False
    for record, source in zip(records, sources, strict=True):
        for ref in source.get("documentRefs", []):
            for caption_ref in tables.get(ref, {}).get("captions", []):
                caption = captions.get(caption_ref.get("$ref"), "").strip()
                if caption and caption not in record["text"]:
                    record["text"] = caption + "\n\n" + record["text"]
                    changed = True

    edits, unresolved, mapping = [], [], {}
    if jats:
        result, edits, unresolved = repair_jats(result, raw)
        changed |= bool(edits)
        sources = result["sourceMap"]
    blocks = docling_blocks(result)
    if jats:
        mapping = link_xml(blocks, result, raw)
        for block in blocks:
            locations = block.get("rawXmlLocations", [])
            if len(locations) == 1:
                location = locations[0]
                block["locator"] += " · XML " + (location.get("xmlId") or location["xpath"])
            elif locations:
                block["locator"] += f" · XML 원문 위치 {len(locations)}곳 (sourceMap)"

    if changed:
        content, updated = assemble(blocks, result.get("title", ""), {"inputSha256": sha(raw)})
        result["content"] = content
        result["preparedPassages"] = [{key: p[key] for key in (
            "text", "locator", "start_offset", "end_offset", "embedding_text", "input_hash")} for p in updated]
    else:
        for record, block in zip(result["preparedPassages"], blocks, strict=True):
            record["locator"] = block["locator"]

    for source, record, block in zip(sources, result["preparedPassages"], blocks, strict=True):
        source.update(startOffset=record["start_offset"], endOffset=record["end_offset"], locator=record["locator"])
        if block.get("rawXmlLocations"):
            source["rawXmlLocations"] = block["rawXmlLocations"]
        if block.get("xmlReferenceTargets"):
            source["xmlReferenceTargets"] = block["xmlReferenceTargets"]
        if block.get("relatedOrdinals"):
            source["relatedOrdinals"] = block.get("relatedOrdinals", [])

    issues = table_reprocessing_candidates(result)
    all_refs = {ref for source in sources for ref in source.get("documentRefs", [])}
    document_hold = bool(jats and (unresolved or result["metadata"].get("mathmlPreservedAsXml", 0)))
    if any(issue["documentRef"] not in all_refs for issue in issues):
        document_hold = True
    if unresolved:
        issues.append({"reason": "jats_caption_requires_review", "locations": unresolved})
    if jats and result["metadata"].get("mathmlPreservedAsXml", 0):
        issues.append({"reason": "complex_mathml_requires_review", "count": result["metadata"]["mathmlPreservedAsXml"]})
    if jats and result['metadata'].get('unresolvedTitledNotes'):
        document_hold = True
        issues.append({'reason': 'jats_notes_title_requires_review', 'locations': result['metadata']['unresolvedTitledNotes']})
    display_holds = set()
    if jats and (result.get('normalizedXml') or result['metadata'].get('mathmlNotationConverted', 0)):
        normalized = result.get('normalizedXml', '')
        if not normalized or sha(normalized.encode('utf8')) != result['metadata'].get('parserInputSha256'):
            document_hold = True
            issues.append({'reason': 'normalized_math_source_unavailable'})
        else:
            root = ET.fromstring(normalized)
            formulas = {''.join(node.itertext()).strip() for node in root.iter() if node.tag.rsplit('}', 1)[-1] == 'tex-math'}
            risky = {formula for formula in formulas if formula and any(char in formula for char in '\\_^{}')}
            for ordinal, record in enumerate(result['preparedPassages']):
                if '$$' in record['text'] or any(formula in record['text'] for formula in risky):
                    display_holds.add(ordinal)
            if any(formula and not any(formula in record['text'] for record in result['preparedPassages']) for formula in formulas):
                document_hold = True
                issues.append({'reason': 'converted_math_missing_from_extraction'})
            if display_holds:
                issues.append({'reason': 'math_display_requires_review', 'passageOrdinals': sorted(display_holds)})
    for ordinal, (record, source) in enumerate(zip(result["preparedPassages"], sources, strict=True)):
        if document_hold or ordinal in display_holds or any(issue.get("documentRef") in source.get("documentRefs", []) for issue in issues):
            record["qualityHold"] = "전처리 구조 또는 수식 확인 필요"
    result["metadata"]["preprocessingQuality"] = {"version": 2, "issues": issues,
        "heldPassages": sum(bool(record.get("qualityHold")) for record in result["preparedPassages"]),
        "unmatchedXmlParagraphs": len(mapping.get("unmatchedParagraphs", [])), "captionCorrections": edits}
    if issues:
        result["readScope"] = "partial"
        result["limitations"].append("추출 구조, 원문 제목 또는 수식 표시에 검토가 필요한 구간이 있어 검색에서 보류합니다.")
    prepared_passages(result["content"], result["preparedPassages"])
    return result
