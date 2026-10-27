"""Combine independently ranked searches without changing their source evidence."""


def merge_candidates(pools: list[list[dict]]) -> list[dict]:
    combined = {}
    for pool in pools:
        seen = set()
        for rank, hit in enumerate(pool, 1):
            passage_id = hit["passageId"]
            if passage_id in seen:
                continue
            seen.add(passage_id)
            current = combined.setdefault(passage_id, {**hit, "fusionScore": 0.0,
                "methods": list(hit.get("methods", []))})
            current["fusionScore"] += 1 / (60 + rank)
            current["methods"] = list(dict.fromkeys(current["methods"] + hit.get("methods", [])))
    return sorted(combined.values(), key=lambda hit: (-hit["fusionScore"], hit["passageId"]))
