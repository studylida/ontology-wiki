"""One shared character budget for passages and one-hop relation/view evidence."""
import json
from .context import group_matches


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def project_hit(hit):
    keys = ("id", "passageId", "sourceRevisionId", "title", "locator", "text", "publisher", "publisherId",
            "author", "attributedTo", "attributionBasis", "sourceType", "readScope", "metadataVersion", "contextTruncated")
    return {key: hit[key] for key in keys if key in hit}


def project_card(card, *, relation):
    keys = ("id", "fromConceptId", "toConceptId", "fromName", "toName", "type", "summary", "conditions", "status") if relation else (
        "id", "conceptId", "sourceRevisionId", "publisher", "publisherId", "author", "attributedTo", "attributionBasis",
        "sourceType", "aspect", "summary", "conditions", "status", "metadataVersion")
    result = {key: card[key] for key in keys if key in card}
    result["evidenceRefs"] = [{"passageId": e["passageId"], "sourceRevisionId": e["sourceRevisionId"]}
                              for e in card.get("evidence", [])]
    return result


def compose_grounding(hits, relations, source_views, max_characters, *, groups=None):
    """Cards without all included source excerpts stay out of the generation prompt.

    Their complete stored/read-API cards are preserved. No truncation of a condition
    is used to manufacture a supported relation. Exact occurrence IDs deduplicate
    excerpts shared by direct, neighbor and one-hop graph retrieval.
    """
    full_relation_count, full_view_count = len(relations), len(source_views)
    groups = groups or []
    prioritized_views, seen_views = [], set()
    for group in groups:
        view = next((v for v in source_views if group_matches(v, group) and v["id"] not in seen_views), None)
        if view:
            prioritized_views.append(view)
            seen_views.add(view["id"])
    prioritized_views += [v for v in source_views if v["id"] not in seen_views]
    relations, source_views = relations[:8], prioritized_views[:12]
    graph_hits = []
    for method, cards in (("relation_evidence", relations), ("source_view_evidence", source_views)):
        for card in cards:
            for reference in card.get("evidence", []):
                graph_hits.append({**reference, "text": reference.get("excerpt", ""), "methods": [method], "score": None})
    candidates = []
    for group in groups:
        head = next((hit for hit in hits if group_matches(hit, group)), None)
        if head:
            candidates.append(head)
    # Ranked search evidence gets priority; related-concept evidence uses the remaining budget.
    candidates.extend(hits)
    candidates.extend(graph_hits)
    payload = {"passages": [], "relations": [], "sourceViews": [], "coverage": "retrieved_evidence_not_semantic_certification"}
    selected, seen = [], set()
    direct_ids = {hit["passageId"] for hit in hits}
    for hit in candidates:
        identifier = hit["passageId"]
        if identifier in seen or not hit.get("text", hit.get("excerpt", "")):
            continue
        copy = {**hit, "text": hit.get("text", hit.get("excerpt", ""))}
        proposed = project_hit(copy)
        passage_budget = max_characters - 100
        if identifier not in direct_ids and graph_hits and not groups:
            passage_budget = max(int(max_characters * .75), len(encoded(payload)))
        remaining = passage_budget - len(encoded({**payload, "passages": payload["passages"] + [proposed]}))
        if remaining < 0:
            # Omit rather than fill a tiny remaining slot with a misleading fragment.
            kept = len(copy["text"]) + remaining - 40
            if kept < 120:
                continue
            copy.update(text=copy["text"][:kept], excerpt=copy["text"][:kept], contextTruncated=True)
            proposed = project_hit(copy)
        if len(encoded({**payload, "passages": payload["passages"] + [proposed]})) > passage_budget:
            continue
        payload["passages"].append(proposed)
        copy["excerpt"] = copy["text"]
        selected.append(copy)
        seen.add(identifier)
    omitted = {"relations": full_relation_count - len(relations), "sourceViews": full_view_count - len(source_views)}
    for field, cards in (("relations", relations), ("sourceViews", source_views)):
        for card in cards:
            evidence = card.get("evidence", [])
            if not evidence or any(e["passageId"] not in seen for e in evidence):
                omitted[field] += 1
                continue
            proposed = project_card(card, relation=field == "relations")
            candidate = {**payload, field: payload[field] + [proposed]}
            if len(encoded(candidate)) > max_characters:
                omitted[field] += 1
                continue
            payload[field].append(proposed)
    assert len(encoded(payload)) <= max_characters
    return selected, payload, {**omitted, "oneHopEvidenceCandidates": len({h["passageId"] for h in graph_hits}),
                              "groundingCharacters": len(encoded(payload))}
