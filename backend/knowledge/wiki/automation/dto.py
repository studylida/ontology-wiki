from typing import Literal
from pydantic import Field
from ...core.dto import DTO


class ChangeIdea(DTO):
    mode: Literal['create', 'edit']
    page_id: str | None = Field(default=None, max_length=80)
    title: str = Field(default='', max_length=300)
    instruction: str = Field(min_length=1, max_length=1000)
    evidence_ids: list[str] = Field(min_length=1, max_length=6)


class ChangePlan(DTO):
    reason: str = Field(min_length=1, max_length=1000)
    ideas: list[ChangeIdea] = Field(default_factory=list, max_length=3)
