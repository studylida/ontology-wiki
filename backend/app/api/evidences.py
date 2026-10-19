"""Evidence Source API Router.

Provides /api/v1/evidences/{id} for slide-in drawer [D-01] on evidence chip clicks.
"""
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.core.cache import cache_manager
from backend.app.models.entities import EvidenceSourceModel, ConceptModel, CausalEdgeModel
from backend.app.schemas.ontology import EvidenceSourceDTO

logger = logging.getLogger("ontology_wiki.evidences")

router = APIRouter(prefix="/evidences", tags=["Evidence Sources"])


@router.get(
    "/{evidence_id}",
    response_model=EvidenceSourceDTO,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    summary="공인 출처 원문 상세 조회 API",
    description="본문/비교 매트릭스 내 [E-01] 칩 클릭 시 우측 슬라이드인 열람을 위한 원문 인용구 및 공인 출처 상세를 서빙합니다."
)
async def get_evidence_detail(
    evidence_id: str,
    db: AsyncSession = Depends(get_db)
):
    cache_key = f"evidence:detail:{evidence_id}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return EvidenceSourceDTO(**cached)

    evidence = await db.get(EvidenceSourceModel, evidence_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"출처 '{evidence_id}' 상세 정보를 불러올 수 없습니다."
        )

    # 참조된 개념 목록 보강 (JSON 필드가 비어있을 경우 인과 엣지 및 실무 사례에서 역탐색)
    ref_concepts = list(evidence.referenced_concepts or [])
    if not ref_concepts:
        found_cids = set()

        # 1. causal_edges에서 역탐색
        edge_stmt = select(CausalEdgeModel).where(CausalEdgeModel.evidence_id == evidence_id)
        edges = (await db.execute(edge_stmt)).scalars().all()
        for e in edges:
            found_cids.add(e.source_concept_id)
            found_cids.add(e.target_concept_id)

        # 2. concepts 테이블에서 limitations 내 evidenceIds 검색
        stmt = select(ConceptModel)
        concepts = (await db.execute(stmt)).scalars().all()
        for c in concepts:
            limits = c.limitations if isinstance(c.limitations, list) else []
            for lim in limits:
                if isinstance(lim, dict) and evidence_id in lim.get("evidenceIds", []):
                    found_cids.add(c.id)

        for c in concepts:
            if c.id in found_cids:
                ref_concepts.append({"conceptId": c.id, "name": c.title})


    response_dto = EvidenceSourceDTO(
        id=evidence.id,
        source_name=evidence.source_name,
        source_type=evidence.source_type,
        publisher=evidence.publisher,
        published_date=evidence.published_date,
        quote=evidence.quote,
        section_context=evidence.section_context,
        relevance_score=float(evidence.relevance_score or 1.0),
        external_url=evidence.external_url,
        url_label=evidence.url_label,
        credibility_tier=evidence.credibility_tier,
        referenced_concepts=ref_concepts
    )

    await cache_manager.set(cache_key, response_dto.model_dump(by_alias=True), ttl_seconds=300)
    return response_dto
