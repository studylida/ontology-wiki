from typing import Literal

from pydantic import Field, model_validator

from knowledge.core.dto import DTO


class WikiPatch(DTO):
    expected_version: int = Field(ge=1)
    title: str | None = Field(None, min_length=1, max_length=300)
    content: str | None = Field(None, min_length=1, max_length=100000)

    @model_validator(mode="after")
    def has_edit(self):
        if self.title is None and self.content is None:
            raise ValueError("title 또는 content가 필요합니다.")
        if any(value is not None and not value.strip() for value in (self.title, self.content)):
            raise ValueError("공백만으로 내용을 저장할 수 없습니다.")
        return self


class WikiUndo(DTO):
    expected_version: int = Field(ge=1)


class WikiSettingsPatch(DTO):
    auto_organize: bool


class OrganizeRequest(DTO):
    message_id: str = Field(min_length=1, max_length=80)
    explicit: bool = False


class OrganizationProposal(DTO):
    action: Literal["add", "merge", "correct", "skip"]
    title: str = Field(default="", max_length=300)
    topic: str = Field(default="", max_length=200)
    summary: str = Field(default="", max_length=2000)
    content: str = Field(default="", max_length=50000)
    conditions: list[str] = Field(default_factory=list, max_length=20)
    limitations: list[str] = Field(default_factory=list, max_length=20)
    citation_ids: list[str] = Field(default_factory=list, max_length=80)
    target_page_id: str | None = Field(None, max_length=80)
    reason: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def valid_action(self):
        if self.action != "skip" and not all(x.strip() for x in (self.title, self.topic, self.content)):
            raise ValueError("저장할 정리에는 제목·주제·본문이 필요합니다.")
        if self.action in ("merge", "correct") and not self.target_page_id:
            raise ValueError("병합·정정에는 기존 페이지가 필요합니다.")
        if self.action == "add" and self.target_page_id:
            raise ValueError("새 페이지 추가에는 기존 페이지를 지정할 수 없습니다.")
        if any(len(value) > 1000 for value in self.conditions + self.limitations):
            raise ValueError("조건·한계 항목이 너무 깁니다.")
        return self
