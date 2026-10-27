from typing import Literal

from pydantic import Field

from knowledge.core.dto import DTO

DocumentForm = Literal["original", "editorial_summary", "edited_derivative", "text_extraction", "unknown"]


class NewDocument(DTO):
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1, max_length=2_000_000)
    format: Literal["markdown", "text"] = "markdown"
    url: str | None = Field(None, max_length=4000)
    publisher: str | None = Field(None, max_length=500)
    publisher_id: str | None = Field(None, max_length=100)
    author: str | None = Field(None, max_length=500)
    attributed_to: str | None = Field(None, max_length=500)
    attribution_basis: str = Field("unknown", max_length=500)
    source_type: str = Field("unknown", max_length=80)
    document_form: DocumentForm | None = None
    published_at: str | None = Field(None, max_length=40)
    visibility: Literal["private", "shared_candidate"] = "private"


class NewRevision(DTO):
    content: str = Field(min_length=1, max_length=2_000_000)
    format: Literal["markdown", "text"] = "markdown"


class MetadataPatch(DTO):
    lineage_key: str | None = Field(None, min_length=1, max_length=500)
    publisher: str | None = Field(None, max_length=500)
    publisher_id: str | None = Field(None, max_length=100)
    author: str | None = Field(None, max_length=500)
    attributed_to: str | None = Field(None, max_length=500)
    attribution_basis: str | None = Field(None, max_length=500)
    source_type: str | None = Field(None, max_length=80)
    document_form: DocumentForm | None = None
    published_at: str | None = Field(None, max_length=40)


class ReviewRequest(DTO):
    decision: Literal["approve", "reject", "hold", "withdraw"]
    reason: str = Field(min_length=1, max_length=4000)


class AttachRequest(DTO):
    conversation_id: str
