"""Shared acquisition and discovery-selection rules; no I/O."""
from hashlib import sha256
import json


def assessment_hash(item, topic):
    return sha256(json.dumps([topic, assessment_segments(item)], sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def assessment_segments(item):
    selected, size = [], 0
    for segment in reversed(item.get("readSegments", [])):
        if size + len(segment["text"]) > 6000:
            continue
        selected.append(segment)
        size += len(segment["text"])
    return list(reversed(selected))


def report_signature(feed, ids):
    pool = {e["id"]: e for e in feed}
    return sha256(json.dumps([[eid, pool.get(eid, {}).get("assessmentInputHash"),
        pool.get(eid, {}).get("assessment"), pool.get(eid, {}).get("assessmentCurrent", True)]
        for eid in sorted(ids)], sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def usable_research_evidence(item):
    acquired = bool(item.get("quote", "").strip()) and item.get("retrievalStatus") in {
        "registered_excerpt", "source_excerpt", "abstract", "external_excerpt"}
    if "readSegments" not in item and not item.get("assessment"):
        return acquired  # Historical sessions remain explicitly selectable.
    return acquired and item.get("assessmentCurrent", True) and (item.get("assessment") or {}).get("decision") == "included"


def evidence_content(item, *, for_model=False):
    result = {key: item[key] for key in ("id", "sourceName", "sourceType", "publisher", "publishedDate", "quote", "sectionContext", "externalUrl", "urlLabel", "credibilityTier", "retrievalStatus") if key in item}
    if for_model and item.get("assessmentInputHash"):
        result["quote"] = "\n\n".join(s["text"] for s in assessment_segments(item))
    return result
