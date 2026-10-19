"""System and Health Check Schemas.

Supports 3-tier status indicators:
🟢 healthy: 정상 가동 (모든 서비스 & AI 게이트웨이 정상)
🟡 degraded: 성능 저하 모드 (AI 오프라인, 온톨로지 정적 룰베이스 폴백 가동 중)
⚫ maintenance: 계획된 점검 및 안전 정지 (불안감을 유발하는 빨간색 대신 차분한 검은색)
"""
from typing import List, Optional, Dict, Literal, Any
from pydantic import BaseModel, Field, ConfigDict


class HealthServicesStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    database: str = "connected"
    redisCache: str = Field("connected", alias="redis_cache")
    llmGateway: str = Field("ready", alias="llm_gateway")


class HealthResponse(BaseModel):
    """3단계 시스템 가동 상태 인디케이터 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True)

    status: Literal["healthy", "degraded", "maintenance"]
    timestamp: str
    services: HealthServicesStatus
    message: str
    activeFallbacks: Optional[List[str]] = Field(default_factory=list, alias="active_fallbacks")


class VersionResponse(BaseModel):
    """시스템 판본 및 표준 메타데이터 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True)

    activeVersion: str = Field("v1.2", alias="active_version")
    latestVersion: str = Field("v1.3", alias="latest_version")
    isUpdateAvailable: bool = Field(False, alias="is_update_available")
    publishedAt: str = Field(..., alias="published_at")
    totalConcepts: int = Field(0, alias="total_concepts")
    totalEvidences: int = Field(0, alias="total_evidences")
    schemaHash: str = Field(..., alias="schema_hash")
    systemConfig: Dict[str, Any] = Field(default_factory=dict, alias="system_config")
