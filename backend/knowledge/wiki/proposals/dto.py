from typing import Literal
from pydantic import Field, field_validator, model_validator
from ...core.dto import DTO
from ..dto import MutationRequest, PageCreate


class ChatSelection(DTO):
    conversation_id: str = Field(min_length=1, max_length=80)
    message_id: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1, max_length=6000)


class ProposalRequest(MutationRequest):
    mode: Literal['create', 'edit', 'links']
    page_id: str | None = Field(default=None, max_length=80)
    instruction: str = Field(min_length=1, max_length=3000)
    context_text: str = Field(default='', max_length=6000)
    selection: ChatSelection | None = None

    @field_validator('instruction', 'context_text')
    @classmethod
    def text_valid(cls, value):
        if '\x00' in value:
            raise ValueError('Invalid text')
        return value

    @model_validator(mode='after')
    def target(self):
        if not self.instruction.strip() or ((self.mode == 'create') != (self.page_id is None)):
            raise ValueError('Create has no target; edit and links need a page')
        if self.selection and self.context_text:
            raise ValueError('Provide employee context OR a selected chat excerpt')
        return self


class ProposalApply(PageCreate):
    # Content is explicitly reviewed; baseVersion comes only from the stored proposal.
    pass


class Patch(DTO):
    old: str = Field(min_length=1, max_length=20000)
    new: str = Field(max_length=20000)
    reason: str = Field(min_length=1, max_length=1000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=12)


class LinkSuggestion(DTO):
    anchor: str = Field(min_length=2, max_length=160)
    page_id: str = Field(min_length=1, max_length=80)
    same_concept: bool = Field(strict=True)
    important: bool = Field(strict=True)
    reason: str = Field(min_length=1, max_length=500)


class GeneratedProposal(DTO):
    title: str = Field(default='', max_length=300)
    markdown: str = Field(default='', max_length=30000)
    patches: list[Patch] = Field(default_factory=list, max_length=5)
    links: list[LinkSuggestion] = Field(default_factory=list, max_length=3)
    reason: str = Field(min_length=1, max_length=1500)
    evidence_ids: list[str] = Field(default_factory=list, max_length=12)
