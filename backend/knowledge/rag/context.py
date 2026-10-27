import re


_EXPERIMENT = re.compile(r"(?i)experiment|result|measure|specimen|sample|bonding process|실험|시편|측정|결과")
_CONDITIONS = re.compile(r"(?im)materials?\s+(?:and|&)\s+methods|experimental\s+(?:details|methods|setup|procedure)|sample\s+(?:preparation|fabrication)|specimen\s+(?:preparation|fabrication)|시편.{0,12}(?:제작|준비|조건)|실험\s*(?:방법|조건)|^\s*2\.\d+\.\s+.{2,80}")
_CONFLICT_NOTE = re.compile(r"(?i)원문\s*내부.{0,15}차이|불일치|상충|모순|inconsisten(?:t|cy)|contradict(?:ion|ory)|discrepanc(?:y|ies)")
_MEASURED_UNIT = re.compile(r"(?i)(?:sccm|mTorr|°\s*[CF]|[µμ]m|Å\s*/\s*cycle|pJ\s*/\s*bit|\d\s*%|\b(?:nm|MPa|kPa|Pa|mW|W|mV|V)\b)")


def numeric_conflict_note(hit: dict) -> bool:
    text = hit.get("locator", "") + "\n" + hit.get("text", "")[:1200]
    # shortcut: notes without recognized measurement units are not prioritized; expand when new document formats require it.
    return bool(_CONFLICT_NOTE.search(text) and _MEASURED_UNIT.search(text))


def experiment_companions(ranked: list[dict], selected: list[dict]) -> list[dict]:
    """Find a methods/specimen passage from the same verified source as a result."""
    seen_ids = {h["passageId"] for h in selected}
    seen_sources, companions = set(), []
    for hit in selected:
        source = hit.get("lineageKey") or hit.get("sourceRevisionId")
        if not source or source in seen_sources or not _EXPERIMENT.search(hit.get("locator", "") + "\n" + hit.get("text", "")[:1200]):
            continue
        seen_sources.add(source)
        matches = [candidate for candidate in ranked if candidate["passageId"] not in seen_ids
            and (candidate.get("lineageKey") or candidate.get("sourceRevisionId")) == source
            and _CONDITIONS.search(candidate.get("locator", "") + "\n" + candidate.get("text", "")[:1200])]
        if matches:
            # Prefer an actual extraction when the same study has an editorial summary.
            companion = min(matches, key=lambda h: h.get("documentForm") not in ("original", "text_extraction"))
            companions.append({**companion, "methods": list(dict.fromkeys([*companion.get("methods", []), "experiment_companion"]))})
            seen_ids.add(companion["passageId"])
    return companions


def prioritize_conflict_notes(hits: list[dict]) -> list[dict]:
    """Give source-provided discrepancy notes priority without deciding if they are true."""
    return sorted(hits, key=lambda h: not numeric_conflict_note(h))


def conflict_companions(ranked: list[dict], selected: list[dict]) -> list[dict]:
    """Keep explicit discrepancy notes for selected source lineages, not inferred conflicts."""
    sources = {h.get("lineageKey") or h.get("sourceRevisionId") for h in selected}
    seen_ids, seen_sources = {h["passageId"] for h in selected}, set()
    result = []
    for hit in ranked:
        source = hit.get("lineageKey") or hit.get("sourceRevisionId")
        if (source and source in sources and source not in seen_sources and hit["passageId"] not in seen_ids
                and numeric_conflict_note(hit)):
            result.append({**hit, "methods": list(dict.fromkeys([*hit.get("methods", []), "source_discrepancy_note"]))})
            seen_sources.add(source)
    return result


def select_context(hits: list[dict], max_characters: int) -> list[dict]:
    """Preserve each occurrence identity; bounded excerpts do not claim full reading."""
    selected, seen, used = [], set(), 0
    for hit in hits:
        identity = hit.get("passageId", hit.get("id"))
        if identity in seen:
            continue
        text = hit.get("text", hit.get("excerpt", ""))
        if not text or used >= max_characters:
            continue
        remaining = max_characters - used
        kept = text[:remaining]
        selected.append({**hit, "text": kept, "excerpt": kept,
                         "contextTruncated": len(kept) < len(text)})
        used += len(kept)
        seen.add(identity)
    return selected


def additional_queries(message: str, aspect: str | None, limit: int) -> list[str]:
    # Bounded, inspectable internal queries. No invented named entities or web loop.
    candidates = []
    if aspect:
        candidates.append(f"{message}\n확인할 측면: {aspect}")
    parts = [p.strip() for p in re.split(r"[?？;；\n]|\s+(?:vs\.?|versus)\s+", message, flags=re.I) if p.strip()]
    candidates.extend(p for p in parts if p != message and len(p) > 2)
    return list(dict.fromkeys(candidates))[:limit]


def group_matches(hit: dict, group: dict) -> bool:
    return all(hit.get(key) == group[key] for key in ("publisherId", "sourceType") if group.get(key))


def citation(hit: dict) -> dict:
    fields = ("id", "passageId", "sourceRevisionId", "title", "locator", "excerpt", "publisher",
              "publisherId", "author", "attributedTo", "attributionBasis", "sourceType", "documentForm", "url", "publishedAt",
              "readScope", "metadataVersion", "contextTruncated", "lineageKey")
    return {key: hit[key] for key in fields if key in hit}
