"""Search API Schemas for Spotlight and Full-Text Search.

Supports Cmd+K spotlight search modal with camelCase serialization.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class SpotlightSearchResult(BaseModel):
    """단일 검색 결과 DTO (프론트엔드 Spotlight 모달 호환)."""
    model_config = ConfigDict(populate_by_name=True, from_attributes=True, serialize_by_alias=True)

    id: str = Field(..., description="개념 ID")
    title: str = Field(..., description="개념명 (국문)")
    engName: str = Field(..., alias="eng_name", serialization_alias="engName", description="영문 개념명")
    aliases: List[str] = Field(default_factory=list, description="동의어/약어 리스트")
    processCategory: str = Field(..., alias="process_category", serialization_alias="processCategory", description="공정 분류")
    processName: str = Field(..., alias="process_name", serialization_alias="processName", description="프론트엔드 호환용 공정명")
    domainFacet: str = Field(..., alias="domain_facet", serialization_alias="domainFacet", description="도메인 패싯 (unit_process, device, operations, materials_infra)")
    scaleLevel: int = Field(..., alias="scale_level", serialization_alias="scaleLevel", description="물리 규모 레벨 (1~5)")
    scaleName: Optional[str] = Field(None, alias="scale_name", serialization_alias="scaleName", description="규모 명칭")
    summary: str = Field(..., description="개념 요약")
    matchType: Literal["title", "alias", "eng_name", "category", "summary", "default"] = Field(
        "default", alias="match_type", serialization_alias="matchType", description="검색 매칭 축"
    )
    score: float = Field(..., description="매칭 관련도 점수")
    highlight: Optional[str] = Field(None, description="하이라이트 스니펫")


class SpotlightSearchResponse(BaseModel):
    """전역 Spotlight 검색 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    query: str = Field(..., description="요청 검색어")
    totalIndexed: int = Field(..., alias="total_indexed", serialization_alias="totalIndexed", description="인덱싱된 총 온톨로지 개념 수")
    totalMatches: int = Field(..., alias="total_matches", serialization_alias="totalMatches", description="검색 매칭 건수")
    results: List[SpotlightSearchResult] = Field(default_factory=list, description="매칭된 개념 목록")
