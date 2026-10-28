from typing import Literal
from pydantic import Field, field_validator
from ..core.dto import DTO


class SourceMetadata(DTO):
    author: str | None = Field(None, max_length=500)
    publisher: str | None = Field(None, max_length=500)
    published_at: str | None = Field(None, max_length=100)
    source_type: Literal['internal','external','unknown'] = 'unknown'
    document_form: Literal['original','editorial_summary','edited_derivative','text_extraction','unknown'] = 'unknown'

    @field_validator('author','publisher','published_at')
    @classmethod
    def valid_text(cls, value):
        if value is not None and '\x00' in value:
            raise ValueError('NUL characters are not allowed')
        return value.strip() or None if value is not None else None


class UploadInfo(DTO):
    title: str = Field(min_length=1, max_length=500)
    metadata: SourceMetadata = Field(default_factory=SourceMetadata)

    @field_validator('title')
    @classmethod
    def valid_title(cls, value):
        if not value.strip() or '\x00' in value:
            raise ValueError('A non-empty title without NUL is required')
        return value.strip()
