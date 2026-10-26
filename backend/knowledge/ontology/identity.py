"""Conservative identity rules, independent of source-specific explanations."""
from dataclasses import dataclass
from typing import Literal
import unicodedata


ConceptType = Literal["process", "device", "structure", "material", "equipment",
                      "property", "technology", "concept"]

# Deliberately finite compatibility names. Unknown legacy types are not guessed
# from substrings or vector similarity, and existing entity types are not rewritten.
_TYPE_LABELS = {
    "process": ("process", "공정", "칩 연결 방식"),
    "device": ("device", "메모리 제품", "메모리 반도체", "반도체 칩"),
    "structure": ("structure", "구조"),
    "material": ("material", "재료", "소재"),
    "equipment": ("equipment", "장비"),
    "property": ("property", "특성"),
    "technology": ("technology", "기술", "기술 범주", "패키지 기술"),
    "concept": ("concept", "개념"),
}


def normalize_label(value: str) -> str:
    """Only orthographic normalization; keep punctuation and token boundaries."""
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def canonical_type(value: str) -> str | None:
    label = normalize_label(value) if isinstance(value, str) else ""
    return next((kind for kind, labels in _TYPE_LABELS.items() if label in labels), None)


@dataclass(frozen=True)
class IdentityCandidate:
    id: str
    type: str
    labels: tuple[str, ...]


@dataclass(frozen=True)
class IdentityDecision:
    status: str  # new, reused, ambiguous, type_conflict, unknown_type
    concept_id: str | None = None
    candidate_ids: tuple[str, ...] = ()


class ConceptIdentityIndex:
    def __init__(self, candidates: list[IdentityCandidate]):
        self.types: dict[str, str | None] = {}
        self.labels: dict[str, set[str]] = {}
        for candidate in candidates:
            self.add(candidate)

    def add(self, candidate: IdentityCandidate):
        self.types[candidate.id] = canonical_type(candidate.type)
        for label in candidate.labels:
            if isinstance(label, str) and len(normalize_label(label)) >= 2:
                self.labels.setdefault(normalize_label(label), set()).add(candidate.id)

    def resolve(self, name: str, aliases: list[str], kind: str) -> IdentityDecision:
        ids = set()
        for label in (name, *aliases):
            ids.update(self.labels.get(normalize_label(label), set()))
        matches = tuple(sorted(ids))
        if not matches:
            return IdentityDecision("new")
        if len(matches) != 1:
            return IdentityDecision("ambiguous", candidate_ids=matches)
        candidate_id = matches[0]
        if self.types[candidate_id] is None:
            return IdentityDecision("unknown_type", candidate_ids=matches)
        if self.types[candidate_id] != canonical_type(kind):
            return IdentityDecision("type_conflict", candidate_ids=matches)
        return IdentityDecision("reused", candidate_id, matches)
