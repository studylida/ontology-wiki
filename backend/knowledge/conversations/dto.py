from datetime import datetime
from typing import Literal
from pydantic import Field, field_validator
from knowledge.core.dto import DTO


def clean_text(value: str) -> str:
    value = value.strip()
    if not value or '\x00' in value:
        raise ValueError('A nonempty string without NUL characters is required')
    return value


class ConversationCreate(DTO):
    title: str = Field(default='새 대화', min_length=1, max_length=300)
    @field_validator('title')
    @classmethod
    def validate_title(cls, value):
        return clean_text(value)


class ConversationPatch(DTO):
    title: str = Field(min_length=1, max_length=300)
    @field_validator('title')
    @classmethod
    def validate_title(cls, value):
        return clean_text(value)


class MessageCreate(DTO):
    content: str = Field(min_length=1, max_length=30000)
    @field_validator('content')
    @classmethod
    def validate_content(cls, value):
        return clean_text(value)


class MessageView(DTO):
    id: str
    role: Literal['user', 'assistant']
    content: str
    created_at: datetime
    status: str = 'completed'
    run_id: str | None = None
    citations: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_unavailable: bool = False
    historical_sources: bool = False


class ConversationView(DTO):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationView):
    messages: list[MessageView] = Field(default_factory=list)


class ConversationList(DTO):
    items: list[ConversationView]
