from datetime import datetime

from pydantic import Field, field_validator

from ..core.dto import DTO


def clean_text(value: str) -> str:
    value = value.strip()
    if not value or "\x00" in value:
        raise ValueError("비어 있거나 NUL 문자가 포함된 내용은 저장할 수 없습니다.")
    return value


class ConversationCreate(DTO):
    title: str | None = Field(None, min_length=1, max_length=300)

    @field_validator("title")
    @classmethod
    def valid_title(cls, value):
        return None if value is None else clean_text(value)


class ConversationPatch(DTO):
    title: str = Field(min_length=1, max_length=300)

    @field_validator("title")
    @classmethod
    def valid_title(cls, value):
        return clean_text(value)


class MessageCreate(DTO):
    # This endpoint stores a user's message, not an AI completion. The role is
    # assigned by the server, and DTO.extra='forbid' rejects spoofed roles/owners.
    content: str = Field(min_length=1, max_length=30000)

    @field_validator("content")
    @classmethod
    def valid_content(cls, value):
        return clean_text(value)


class MessageView(DTO):
    id: str
    role: str
    content: str
    created_at: datetime


class ConversationView(DTO):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationView):
    messages: list[MessageView]


class ConversationList(DTO):
    items: list[ConversationView]
