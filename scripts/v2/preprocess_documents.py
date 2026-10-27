"""Prepare a fresh offline review bundle. No database, providers or indexing."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from knowledge.documents.preprocessing import (
    apply_table_repairs, assemble, docling_blocks, group_markdown, link_xml,
    markdown_blocks, repair_jats, sha, table_reprocessing_candidates,
)
from knowledge.documents.parsing import prepared_passages


def dump(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def checked(descriptor):
    path = Path(descriptor["path"]).resolve(strict=True)
    if not path.is_file() or sha(path.read_bytes()) != descriptor["sha256"]:
        raise ValueError(f"Input hash mismatch: {path.name}")
    return path


def prepare(manifest_path: Path, output: Path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = manifest["documents"]
    if not records or len({r["id"] for r in records}) != len(records):
        raise ValueError("Document IDs must be unique and nonempty")
    if any(not r["id"].replace("-", "").replace("_", "").isalnum() for r in records):
        raise ValueError("Invalid document ID")
    # Verify every pinned input before creating any output.
    inputs = [(checked(r["original"]), checked(r["input"])) for r in records]
    output = output.resolve()
    if output.exists() or any(p.is_relative_to(output) for pair in inputs for p in pair):
        raise ValueError("Output must be a new directory separate from inputs")
    output.mkdir(parents=True)
    shutil.copyfile(manifest_path, output / "input-manifest.json")
    summary = []
    all_passages = []
    for record, (original, source) in zip(records, inputs):
        folder = output / record["id"]
        folder.mkdir()
        original_copy = folder / ("original" + original.suffix)
        input_copy = folder / ("input" + source.suffix)
        shutil.copyfile(original, original_copy)
        shutil.copyfile(source, input_copy)
        if sha(original_copy.read_bytes()) != record["original"]["sha256"] or sha(input_copy.read_bytes()) != record["input"]["sha256"]:
            raise ValueError("Input changed during preservation")
        raw = original_copy.read_bytes()
        notes, corrections, unresolved, mapping, reprocessing = [], [], [], {}, []
        if record["format"] == "markdown":
            extraction = input_copy.read_bytes().decode("utf-8-sig")
            blocks, notes = markdown_blocks(extraction)
            blocks = group_markdown(blocks, maximum=1400)
        elif record["format"] == "docling":
            result = json.loads(input_copy.read_text(encoding="utf-8"))
            if result["metadata"]["sourceSha256"] != sha(raw):
                raise ValueError("Docling source hash differs from original")
            prepared_passages(result["content"], result["preparedPassages"])
            for passage, source_map in zip(result["preparedPassages"], result["sourceMap"], strict=True):
                if (passage["start_offset"] != source_map["startOffset"]
                        or passage["end_offset"] != source_map["endOffset"]):
                    raise ValueError("Docling source map differs from extraction offsets")
            repaired_refs = {repair["documentRef"] for repair in record.get("tableRepairs", [])}
            reprocessing = [item for item in table_reprocessing_candidates(result)
                            if item["documentRef"] not in repaired_refs]
            if record.get("tableRepairs"):
                result, changes = apply_table_repairs(result, record["tableRepairs"])
                corrections.extend(changes)
            if original.suffix.lower() in {".xml", ".nxml"}:
                result, changes, unresolved = repair_jats(result, raw)
                corrections.extend(changes)
            blocks = docling_blocks(result)
            if original.suffix.lower() in {".xml", ".nxml"}:
                mapping = link_xml(blocks, result, raw)
            extraction = result["content"]
        else:
            raise ValueError("Unsupported offline input format")
        lineage = {"documentId": record["id"], "lineageKey": record["lineageKey"],
                   "originalSha256": sha(raw), "inputSha256": record["input"]["sha256"],
                   "originalPath": str(original_copy), "inputPath": str(input_copy),
                   "sourceTitle": record["title"], "editionSha256": record["input"]["sha256"],
                   "sourceSpanUnit": "Unicode codepoints in input text" if record["format"] == "markdown" else "Unicode codepoints in input JSON content field",
                   "documentForm": record["documentForm"], "sourceUrl": record.get("sourceUrl"),
                   "previousRevisions": record.get("previousRevisions", []),
                   "serviceActivated": False}
        content, passages = assemble(blocks, record["title"], lineage)
        for passage in passages:
            holds = [hold for hold in record.get("qualityHolds", [])
                     if hold["documentRef"] in passage.get("documentRefs", [])]
            holds.extend(item for item in reprocessing if item["documentRef"] in passage.get("documentRefs", []))
            passage["indexingDisposition"] = "hold" if holds else "candidate_for_index_review"
            passage["qualityHolds"] = holds
        (folder / "extracted.md").write_bytes(extraction.encode("utf-8"))
        (folder / "clean.md").write_bytes(content.encode("utf-8"))
        (folder / "editorial-notes.md").write_bytes("\n\n".join(n["text"] for n in notes).encode("utf-8"))
        dump(folder / "passages.json", passages)
        dump(folder / "source-map.json", [{k: v for k, v in p.items() if k not in {"text", "embedding_text"}} for p in passages])
        dump(folder / "corrections.json", corrections)
        dump(folder / "reprocessing-queue.json", reprocessing)
        dump(folder / "editorial-map.json", notes)
        dump(folder / "xml-mapping-review.json", {**mapping, "unresolvedCaptions": unresolved})
        provenance = {**record, "originalCopy": str(original_copy), "inputCopy": str(input_copy),
                      "cleanSha256": sha(content.encode()), "runManifestSha256": sha(manifest_path.read_bytes()),
                      "contentCorrections": "Prior reviewed editorial candidate reused; no new factual correction",
                      "preparationStatus": "offline_review_candidate", "approvalInherited": False,
                      "processingScope": record.get("processingScope", "Partial source QA; not scientific validation"),
                      "unresolvedCaptionCount": len(unresolved),
                      "unmatchedXmlParagraphCount": len(mapping.get("unmatchedParagraphs", [])),
                      "chunksAbove1400Characters": sum(len(p["text"]) > 1400 for p in passages),
                      "serviceActivated": False}
        dump(folder / "provenance.json", provenance)
        all_passages.extend(passages)
        summary.append({"id": record["id"], "title": record["title"], "format": record["format"],
                        "priorDecision": record.get("priorDecision"), "passages": len(passages),
                        "editorialBlocksSeparated": len(notes), "extractionCorrections": len(corrections),
                        "heldPassages": sum(p["indexingDisposition"] == "hold" for p in passages),
                        "unresolvedCaptionCount": len(unresolved), "unmatchedXmlParagraphCount": provenance["unmatchedXmlParagraphCount"],
                        "folder": str(folder), "status": "offline_review_candidate"})
    (output / "prepared-passages.jsonl").write_bytes("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in all_passages).encode("utf-8"))
    (output / "index-candidates.jsonl").write_bytes("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in all_passages
        if p["indexingDisposition"] != "hold").encode("utf-8"))
    dump(output / "run-ledger.json", {"createdAtUtc": datetime.now(timezone.utc).isoformat(),
         "manifestSha256": sha(manifest_path.read_bytes()), "documents": summary,
         "preservedExclusions": manifest.get("exclusions", []), "serviceActivated": False,
         "providerCalls": 0, "embeddingCalls": 0, "graphBuilds": 0,
         "validation": "All emitted passages exactly match clean text offsets; partial original review is separate."})
    dump(output / "artifact-hashes.json", {str(p.relative_to(output)): sha(p.read_bytes())
         for p in sorted(output.rglob("*")) if p.is_file()})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.manifest.resolve(strict=True), args.output)
    print(json.dumps({"documents": len(result), "passages": sum(x["passages"] for x in result), "output": str(args.output.resolve())}))
