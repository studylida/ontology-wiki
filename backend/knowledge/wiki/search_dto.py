"""Navigation/search contracts keep stored Markdown and computed results distinct."""
from pydantic import Field, field_validator
from ..core.dto import DTO
from .dto import PageView


class SearchQuery(DTO):
    query: str = Field(min_length=1, max_length=4000)
    limit: int = Field(default=12, ge=1, le=50)
    exclude_page_id: str | None = Field(default=None, max_length=80)

    @field_validator('query')
    @classmethod
    def query_text(cls, value):
        if not value.strip() or '\x00' in value:
            raise ValueError('A nonempty search query is required')
        return value.strip()


class SimilarQuery(DTO):
    title: str = Field(min_length=1, max_length=300)
    markdown: str = Field(default='', max_length=100000)
    exclude_page_id: str | None = Field(default=None, max_length=80)

    @field_validator('title', 'markdown')
    @classmethod
    def plain_text(cls, value):
        if '\x00' in value:
            raise ValueError('Invalid query text')
        return value


class WikiSearchHit(DTO):
    page: PageView
    revision_id: str
    passage_id: str | None = None
    locator: str
    excerpt: str
    methods: list[str]
    score: float
    name_match: bool = False


class SearchResult(DTO):
    items: list[WikiSearchHit]
    warnings: list[str]
    semantic_status: str
    embedding_profile: str
    reranking: dict


class NameAlternative(DTO):
    page: PageView
    matched_names: list[str]


class IndexRetry(DTO):
    base_version: int = Field(ge=1, strict=True)


class IndexStatus(DTO):
    status: str
    current_revision_id: str
    indexed_revision_id: str | None
    embedding_profile: str | None
    requested_profile: str
    job: dict | None
    held_passages: list[dict]
    can_retry: bool
