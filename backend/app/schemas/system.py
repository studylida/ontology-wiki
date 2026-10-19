"""System and Health Check Schemas.

Supports 3-tier status indicators:
🟢 healthy: 정상 가동 (모든 서비스 & AI 게이트웨이 정상)
🟡 degraded: 성능 저하 모드 (AI 오프라인, 온톨로지 정적 룰베이스 폴백 가동 중)
⚫ maintenance: 계획된 점검 및 안전 정지 (불안감을 유발하는 빨간색 대신 차분한 검은색)
"""
from typing import List, Optional, Dict, Literal, Any
from pydantic import BaseModel, Field, ConfigDict


class HealthServicesStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    database: str = "connected"
    redisCache: str = Field("connected", alias="redisCache", serialization_alias="redisCache")
    llmGateway: str = Field("ready", alias="llmGateway", serialization_alias="llmGateway")


class HealthResponse(BaseModel):
    """3단계 시스템 가동 상태 인디케이터 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    status: Literal["healthy", "degraded", "maintenance"]
    timestamp: str
    services: HealthServicesStatus
    message: str
    activeFallbacks: Optional[List[str]] = Field(default_factory=list, alias="activeFallbacks", serialization_alias="activeFallbacks")


class VersionResponse(BaseModel):
    """시스템 판본 및 표준 메타데이터 응답 DTO."""
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    activeVersion: str = Field("v1.2", alias="activeVersion", serialization_alias="activeVersion")
    latestVersion: str = Field("v1.3", alias="latestVersion", serialization_alias="latestVersion")
    isUpdateAvailable: bool = Field(False, alias="isUpdateAvailable", serialization_alias="isUpdateAvailable")
    publishedAt: str = Field(..., alias="publishedAt", serialization_alias="publishedAt")
    totalConcepts: int = Field(0, alias="totalConcepts", serialization_alias="totalConcepts")
    totalEvidences: int = Field(0, alias="totalEvidences", serialization_alias="totalEvidences")
    schemaHash: str = Field(..., alias="schemaHash", serialization_alias="schemaHash")
    systemConfig: Dict[str, Any] = Field(default_factory=dict, alias="systemConfig", serialization_alias="systemConfig")
