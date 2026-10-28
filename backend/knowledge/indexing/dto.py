"""Internal input boundary, not a speculative extracted-knowledge table."""
from dataclasses import dataclass


@dataclass(frozen=True)
class IndexUnit:
    passage_id: str
    source_revision_id: str
    text: str
    input_hash: str
    kind: str = 'source_passage'
