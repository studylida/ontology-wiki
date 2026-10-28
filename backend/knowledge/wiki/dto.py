from datetime import datetime
from pydantic import Field, field_validator
from ..core.dto import DTO


class MutationRequest(DTO):
    request_id: str = Field(min_length=8, max_length=128, pattern=r'^[A-Za-z0-9_.:-]+$')


class PageCreate(MutationRequest):
    title: str = Field(min_length=1, max_length=300)
    markdown: str = Field(min_length=1, max_length=100000)
    source_note: str = Field(default='', max_length=10000)
    change_summary: str = Field(default='', max_length=500)

    @field_validator('title')
    @classmethod
    def title_text(cls, value):
        value = value.strip()
        if not value or any(ord(c) < 32 for c in value):
            raise ValueError('Use a nonempty single-line title')
        return value

    @field_validator('markdown', 'source_note', 'change_summary')
    @classmethod
    def preserve_text(cls, value, info):
        if '\x00' in value or (info.field_name == 'markdown' and not value.strip()):
            raise ValueError('Invalid text')
        # Keep Markdown indentation, trailing spaces and newlines exactly as written.
        return value


class PageEdit(PageCreate):
    base_version: int = Field(ge=1, strict=True)


class PageRestore(MutationRequest):
    base_version: int = Field(ge=1, strict=True)
    revision_id: str = Field(min_length=1, max_length=80)


class PageProtection(MutationRequest):
    base_version: int = Field(ge=1, strict=True)
    locked: bool = Field(strict=True)


class AuthorView(DTO):
    id: str
    username: str


class RevisionSummary(DTO):
    id: str
    page_id: str
    number: int
    title: str
    change_summary: str
    editor: AuthorView
    created_at: datetime
    restored_from_id: str | None = None


class RevisionView(RevisionSummary):
    markdown: str
    source_note: str


class PageView(DTO):
    id: str
    title: str
    current_revision_id: str
    revision_number: int
    version: int
    locked: bool
    can_edit: bool
    can_protect: bool
    creator: AuthorView
    editor: AuthorView
    created_at: datetime
    updated_at: datetime


class PageDetail(PageView):
    revision: RevisionView


class PageList(DTO):
    items: list[PageView]
    total: int
    offset: int
    limit: int


class RevisionList(DTO):
    items: list[RevisionSummary]
    total: int
    offset: int
    limit: int


class MutationResult(DTO):
    page_id: str
    revision_id: str
    version: int
    replayed: bool = False


class RevisionComparison(DTO):
    before: RevisionView
    after: RevisionView
    diff: str
