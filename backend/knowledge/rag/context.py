import re


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
              "publisherId", "author", "attributedTo", "attributionBasis", "sourceType", "url", "publishedAt",
              "readScope", "metadataVersion", "contextTruncated")
    return {key: hit[key] for key in fields if key in hit}
