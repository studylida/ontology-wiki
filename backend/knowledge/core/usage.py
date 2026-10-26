"""Aggregate observed provider usage without converting unknown charges to zero."""


def summarize_usage(parts: list[dict]) -> dict:
    calls = sum(p.get("calls", 1) for p in parts)
    unknown = sum(p.get("calls", 1) for p in parts if p.get("costUsd") is None)
    missing_cost = any(p.get("costUsd") is None for p in parts)
    result = {"calls": calls, "fixtureCalls": sum(p.get("fixtureCalls", 0) for p in parts),
              "costUsd": None if missing_cost else sum(p.get("costUsd", 0) for p in parts),
              "knownCostUsd": sum(p["costUsd"] for p in parts if p.get("costUsd") is not None),
              "unknownCostCalls": unknown, "components": parts}
    for field in ("inputTokens", "outputTokens", "totalTokens"):
        result[field] = None if any(p.get(field) is None for p in parts) else sum(p.get(field, 0) for p in parts)
    for field in ("provider", "model", "pricingDate", "source"):
        values = {p.get(field) for p in parts}
        result[field] = next(iter(values)) if len(values) == 1 else ("multiple" if values else None)
    # Generation-only configuration observations; embeddings have no effort/tier.
    # A missing returned value stays None even when the request selected a value.
    for field in ("requestedEffort", "effectiveEffort", "requestedServiceTier", "serviceTier"):
        values = {p[field] for p in parts if field in p}
        result[field] = next(iter(values)) if len(values) == 1 else ("multiple" if values else None)
    result["costStatus"] = "fixture" if parts and all(p.get("source") == "fixture" for p in parts) else "unknown" if missing_cost else "estimated"
    return result


def unknown_usage(operation: str, model=None, *, source="provider") -> dict:
    if model and model.startswith("fixture-"):
        source = "fixture"
    return {"operation": operation, "provider": None, "model": model, "inputTokens": None,
            "outputTokens": None, "totalTokens": None, "costUsd": None, "costStatus": "unknown",
            "calls": 0 if source == "fixture" else 1, "fixtureCalls": 1 if source == "fixture" else 0,
            "pricingDate": None, "source": source}
