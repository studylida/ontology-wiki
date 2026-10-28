"""Retrieval is an internal answer capability, not a separate user mode."""
from typing import Literal
from pydantic import Field
from knowledge.core.dto import DTO


class RetrievalSummary(DTO):
    status: Literal['found', 'no_evidence']
    source_revision_ids: list[str] = Field(default_factory=list)
    context_characters: int = 0
    warnings: list[str] = Field(default_factory=list)
