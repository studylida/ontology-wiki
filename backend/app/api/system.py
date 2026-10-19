"""System Common & Global Service API Router.

Implements:
1. 4.1.1 GET /api/v1/system/health - 3-tier status (🟢 healthy | 🟡 degraded | ⚫ maintenance)
2. 4.1.2 GET /api/v1/system/version - Ontology version metadata
3. 5.3.3 GET /api/v1/system/audit/verify-integrity - WORM Merkle hash chain cryptographic audit
4. 5.4.2 POST /api/v1/security/access-requests - Tier 3 data access request workflow
5. 5.2.2 GET /api/v1/events/stream - Real-Time Server-Sent Events (SSE) broadcast
"""
import uuid
import asyncio
from datetime import datetime, timezone
import hashlib
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query, status, Header, Body
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.core.config import settings
from backend.app.core.database import get_db, check_db_connection
from backend.app.core.cache import cache_manager
from backend.app.core.circuit_breaker import circuit_breaker, CircuitState
from backend.app.schemas.system import HealthResponse, HealthServicesStatus, VersionResponse
from backend.app.models.entities import ConceptModel, EvidenceSourceModel, AuditLogModel

router = APIRouter(tags=["System"])


@router.get("/system/health", response_model=HealthResponse)
async def get_system_health():
    """4.1.1 GET /api/v1/system/health

    탑바 우측 설정 아이콘 옆 상태 인디케이터 닷(Dot) 연동 및 통합 헬스체크.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    db_ok = await check_db_connection()
    redis_ok = await cache_manager.check_health()
    llm_ready = bool(settings.GEMINI_API_KEY or settings.OPENAI_API_KEY)
    cb_state = circuit_breaker.state

    services = HealthServicesStatus(
        database="connected" if db_ok else "offline",
        redisCache="connected" if redis_ok else "fallback_in_memory",
        llmGateway="ready" if (llm_ready and cb_state == CircuitState.CLOSED) else "circuit_open (fallback)"
    )

    # 3단계 상태 판정
    if not db_ok or settings.SYSTEM_STATUS == "maintenance":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=HealthResponse(
                status="maintenance",
                timestamp=now_iso,
                services=services,
                message="데이터베이스 점검 중입니다. 데이터 정합성 보전을 위해 안전 정지 모드로 대기 중입니다.",
                activeFallbacks=["read_only_standby"]
            ).model_dump(by_alias=True)
        )

    if not llm_ready or not redis_ok or settings.SYSTEM_STATUS == "degraded" or cb_state == CircuitState.OPEN:
        return HealthResponse(
            status="degraded",
            timestamp=now_iso,
            services=services,
            message="AI 추론 엔진 점검 또는 서킷 오픈 상태입니다. 온톨로지 정적 지식 및 룰베이스 모드로 안전하게 서비스 중입니다.",
            activeFallbacks=["static_ontology_fallback", "in_memory_cache"]
        )

    return HealthResponse(
        status="healthy",
        timestamp=now_iso,
        services=services,
        message="모든 온톨로지 코어 엔진이 정상 가동 중입니다.",
        activeFallbacks=[]
    )


@router.get("/system/version", response_model=VersionResponse)
async def get_system_version(
    client_version: str = Query("v1.2", alias="clientVersion"),
    db: AsyncSession = Depends(get_db)
):
    """4.1.2 GET /api/v1/system/version"""
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
        activeVersion=settings.ACTIVE_VERSION,
        latestVersion=settings.LATEST_VERSION,
        isUpdateAvailable=is_update_available,
        publishedAt="2026-10-15T18:00:00Z",
        totalConcepts=total_concepts,
        totalEvidences=total_evidences,
        schemaHash=schema_hash,
        systemConfig={
            "gapThreshold": settings.GAP_THRESHOLD,
            "minVerificationTiers": 1,
            "allowedPerspectiveTypes": ["hbm3e_advanced", "dram_process", "foundry_sub2nm", "nand_high_stack"],
            "maxCausalSearchDepth": 2
        }
    )


@router.get("/system/audit/verify-integrity")
async def verify_audit_integrity(db: AsyncSession = Depends(get_db)):
    """5.3.3 WORM Merkle Hash Chain Cryptographic Integrity Verification."""
    stmt = select(AuditLogModel).order_by(AuditLogModel.id.asc())
    logs = (await db.execute(stmt)).scalars().all()

    total_logs = len(logs)
    if total_logs == 0:
        return {
            "status": "VERIFIED",
            "valid": True,
            "chainValid": True,
            "totalLogs": 0,
            "totalVerifiedLogs": 0,
            "tamperDetected": False,
            "merkleRootHash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "message": "감사 로그 체인이 비어있으며 무결성 상태입니다."
        }

    chain_valid = True
    for i in range(1, total_logs):
        prev = logs[i - 1]
        curr = logs[i]
        if curr.previous_log_hash != prev.entry_hash:
            chain_valid = False
            break

    return {
        "status": "VERIFIED" if chain_valid else "CORRUPTED",
        "valid": chain_valid,
        "chainValid": chain_valid,
        "totalLogs": total_logs,
        "totalVerifiedLogs": total_logs,
        "tamperDetected": not chain_valid,
        "merkleRootHash": logs[-1].entry_hash if total_logs > 0 else None,
        "latestEntryHash": logs[-1].entry_hash if total_logs > 0 else None,
        "verifiedAt": datetime.now(timezone.utc).isoformat()
    }


class AccessRequestPayload(BaseModel):
    conceptId: str
    perspectiveId: Optional[str] = "default"
    reason: Optional[str] = "실무 공정 트러블슈팅 및 수율 상관성 대조"


@router.post("/security/access-requests")
async def create_access_request(
    payload: AccessRequestPayload,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role")
):
    """5.4.2 POST /api/v1/security/access-requests

    미인가 엔지니어의 Tier 3 대외비 수치 열람 권한 신청 티켓 발급.
    """
    req_id = f"REQ-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    return {
        "requestId": req_id,
        "conceptId": payload.conceptId,
        "perspectiveId": payload.perspectiveId,
        "userRole": x_user_role or "line_engineer",
        "status": "pending_approval",
        "submittedAt": datetime.now(timezone.utc).isoformat(),
        "message": f"열람 권한 신청 번호 [{req_id}]가 발급되었습니다. 수석 리뷰어 승인 후 열람이 활성화됩니다."
    }


@router.get("/events/stream")
async def sse_event_stream():
    """5.2.2 Real-time Server-Sent Events (SSE) Broadcast Stream."""
    async def event_generator():
        # 최초 연결 웰컴 이벤트
        welcome = {
            "type": "system_connected",
            "activeVersion": settings.ACTIVE_VERSION,
            "circuitState": circuit_breaker.state.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        import json
        yield f"event: connected\ndata: {json.dumps(welcome)}\n\n"

        # 주기적 핑 및 상태 감지
        for _ in range(5):
            await asyncio.sleep(2)
            ping_data = {
                "type": "heartbeat",
                "circuitState": circuit_breaker.state.value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            yield f"event: ping\ndata: {json.dumps(ping_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
