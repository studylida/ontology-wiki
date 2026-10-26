from typing import Annotated

from pydantic import Field, StringConstraints, field_validator
from knowledge.core.dto import DTO


class SearchRequest(DTO):
    query: str = Field(min_length=2, max_length=1500)
    conversation_id: str | None = None
    limit: int = Field(default=6, ge=1, le=10)


class FetchRequest(DTO):
    url: str = Field(min_length=8, max_length=4000)
    query: str = Field(default="", max_length=1500)
    conversation_id: str | None = None


class RelevanceAssessment(DTO):
    """A source-scoped generated explanation, distinct from content acquisition."""
    relevance: Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=10000)] | None
    limitations: list[Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=2000)]] = Field(max_length=5)

    @field_validator("limitations", mode="before")
    @classmethod
    def preserve_single_limitation_sentence(cls, value):
        # Some earlier model responses used one plain sentence. Preserve it as
        # one item; never iterate its characters or coerce objects/numbers.
        if isinstance(value, str):
            sentence = value.strip()
            if not sentence or "\n" in sentence or "\r" in sentence:
                raise ValueError("limitations must be a list of complete strings")
            return [sentence]
        return value


class ItemRef(DTO):
    id: str


class TransferRequest(DTO):
    conversation_id: str
    items: list[ItemRef] = Field(min_length=1, max_length=10)
    query: str = Field(max_length=1500)
    conditions: str | None = Field(None, max_length=4000)
