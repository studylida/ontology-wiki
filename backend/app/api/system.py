"""System Common & Global Service API Router.

Implements 4.1.1 GET /api/v1/system/health and 4.1.2 GET /api/v1/system/version.
Strictly complies with 3-tier status indicators:
🟢 healthy: 정상 가동 (모든 서비스 & AI 게이트웨이 정상)
🟡 degraded: 성능 저하 모드 (AI 오프라인, L1/L2 캐시 및 온톨로지 정적 룰베이스 폴백 가동 중)
⚫ maintenance: 계획된 점검 및 안전 정지 (차분한 검은색)
"""
from datetime import datetime, timezone
import hashlib
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.core.config import settings
from backend.app.core.database import get_db, check_db_connection
from backend.app.core.cache import cache_manager
from backend.app.schemas.system import HealthResponse, HealthServicesStatus, VersionResponse
from backend.app.models.entities import ConceptModel, EvidenceSourceModel

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health", response_model=HealthResponse)
async def get_system_health():
    """4.1.1 GET /api/v1/system/health

    탑바 우측 설정 아이콘 옆 상태 인디케이터 닷(Dot) 연동 및 통합 헬스체크.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    db_ok = await check_db_connection()
    redis_ok = await cache_manager.check_health()
    llm_ready = bool(settings.GEMINI_API_KEY)

    services = HealthServicesStatus(
        database="connected" if db_ok else "offline",
        redis_cache="connected" if redis_ok else "fallback_in_memory",
        llm_gateway="ready" if llm_ready else "offline (circuit_open)"
    )

    # 3단계 상태 판정
    if not db_ok or settings.SYSTEM_STATUS == "maintenance":
        # ⚫ 계획된 점검 및 안전 정지 상태
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=HealthResponse(
                status="maintenance",
                timestamp=now_iso,
                services=services,
                message="데이터베이스 점검 중입니다. 데이터 정합성 보전을 위해 안전 정지 모드로 대기 중입니다.",
                active_fallbacks=["read_only_standby"]
            ).model_dump(by_alias=True)
        )

    if not llm_ready or not redis_ok or settings.SYSTEM_STATUS == "degraded":
        # 🟡 성능 저하 폴백 모드 (AI 오프라인 또는 캐시 폴백)
        return HealthResponse(
            status="degraded",
            timestamp=now_iso,
            services=services,
            message="AI 추론 엔진 점검 중입니다. 온톨로지 정적 지식 및 룰베이스 모드로 안전하게 서비스 중입니다.",
            active_fallbacks=["static_ontology_fallback", "in_memory_cache"]
        )

    # 🟢 정상 가동
    return HealthResponse(
        status="healthy",
        timestamp=now_iso,
        services=services,
        message="모든 온톨로지 코어 엔진이 정상 가동 중입니다.",
        active_fallbacks=[]
    )


@router.get("/version", response_model=VersionResponse)
async def get_system_version(
    client_version: str = Query("v1.2", alias="clientVersion"),
    db: AsyncSession = Depends(get_db)
):
    """4.1.2 GET /api/v1/system/version

    시스템 설정 팝업창 상단 온톨로지 판본, 메타데이터 및 사내 표준 정책(0.35) 확인.
    """
    total_concepts = 0
    total_evidences = 0
    try:
        concept_count_stmt = select(func.count(ConceptModel.id))
        evidence_count_stmt = select(func.count(EvidenceSourceModel.id))
        total_concepts = (await db.execute(concept_count_stmt)).scalar() or 0
        total_evidences = (await db.execute(evidence_count_stmt)).scalar() or 0
    except Exception:
        pass

    schema_raw = f"{settings.ACTIVE_VERSION}:{total_concepts}:{total_evidences}"
    schema_hash = f"sha256:{hashlib.sha256(schema_raw.encode()).hexdigest()}"

    is_update_available = client_version != settings.ACTIVE_VERSION

    return VersionResponse(
        active_version=settings.ACTIVE_VERSION,
        latest_version=settings.LATEST_VERSION,
        is_update_available=is_update_available,
        published_at="2026-10-15T18:00:00Z",
        total_concepts=total_concepts,
        total_evidences=total_evidences,
        schema_hash=schema_hash,
        system_config={
            "gapThreshold": settings.GAP_THRESHOLD,
            "minVerificationTiers": 1,
            "allowedPerspectiveTypes": ["hbm3e_advanced", "dram_process", "foundry_sub2nm", "nand_high_stack"],
            "maxCausalSearchDepth": 2
        }
    )
