from typing import Literal
from pydantic import Field, field_validator, model_validator
from ..core.dto import DTO


class SourceGroup(DTO):
    group_id: str = Field(min_length=1, max_length=80)
    publisher_id: str | None = None
    source_type: str | None = None


class RetrievalRequest(DTO):
    message: str = Field(min_length=1, max_length=30000)
    concept_ids: list[str] = Field(default_factory=list, max_length=50)
    source_revision_ids: list[str] = Field(default_factory=list, max_length=1000)
    source_groups: list[SourceGroup] = Field(default_factory=list, max_length=12)
    aspect: str | None = Field(None, max_length=120)
    extended: bool = False
    attachment_ids: list[str] = Field(default_factory=list, max_length=50)
    document_context_ids: list[str] = Field(default_factory=list, max_length=50)
    conversation_id: str | None = None

    @field_validator("message")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("질문을 입력해 주세요.")
        return value.strip()

    @model_validator(mode="after")
    def unique_groups(self):
        ids = [g.group_id for g in self.source_groups]
        if len(ids) != len(set(ids)):
            raise ValueError("sourceGroups groupId must be unique")
        return self


class AnswerRequest(RetrievalRequest):
    client_request_id: str = Field(min_length=1, max_length=128)
    response_mode: Literal["wiki", "analysis"] = "wiki"
    retry_of_run_id: str | None = None
