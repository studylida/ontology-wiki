"""Apply source-preserving preprocessing before a Docling result is stored or transferred."""
from __future__ import annotations

import copy

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
    for record, source in zip(result["preparedPassages"], sources, strict=True):
        if document_hold or any(issue.get("documentRef") in source.get("documentRefs", []) for issue in issues):
            record["qualityHold"] = "전처리 구조 또는 수식 확인 필요"
    result["metadata"]["preprocessingQuality"] = {"version": 2, "issues": issues,
        "heldPassages": sum(bool(record.get("qualityHold")) for record in result["preparedPassages"]),
        "unmatchedXmlParagraphs": len(mapping.get("unmatchedParagraphs", [])), "captionCorrections": edits}
    if issues:
        result["readScope"] = "partial"
        result["limitations"].append("표 구조 또는 수식에 검토가 필요한 구간이 있어 검색에서 보류합니다.")
    prepared_passages(result["content"], result["preparedPassages"])
    return result
