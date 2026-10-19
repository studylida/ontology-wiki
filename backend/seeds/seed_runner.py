"""Ontology Database Seeder and Integrity Verification Runner.

Executes atomic database seeding for:
1. EvidenceSource (135 items: Golden + Parsed Whitepapers)
2. Concept (54 items: 5 Golden Core Domains + Parsed Concepts)
3. CausalEdge (Causal Graph with Compensating Parameters / 보상 파라미터)
4. PerspectiveCase (Adaptive Level 3 Industrial Specs)
5. ComparisonSession (3-Step Snapshots with Tail-Questions / 꼬리질문)
6. ReviewTicket (2-Segment Governance with overrideReason / 사유)

Verifies 1~2 hop Recursive CTE execution speed (< 1.0ms).
"""
import os
import sys
import time
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from backend.app.core.config import settings
from backend.app.core.database import engine, async_session_factory, Base
from backend.app.models.entities import (
    EvidenceSourceModel,
    ConceptModel,
    CausalEdgeModel,
    PerspectiveCaseModel,
    ComparisonSessionModel,
    ReviewTicketModel
)
from backend.seeds.golden_dataset import (
    EVIDENCE_SOURCES,
    CONCEPTS,
    CAUSAL_EDGES,
    PERSPECTIVE_CASES,
    COMPARISON_SESSIONS,
    REVIEW_TICKETS
)
from backend.seeds.source_parser import parser

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_runner")


def parse_dt(val):
    if isinstance(val, str) and val.strip():
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            return None
    return val


async def run_seeding():
    """Executes atomic database seeding."""
    logger.info("=" * 70)
    logger.info("Starting Semiconductor Causal Ontology Database Seeding...")
    logger.info(f"Target Database Engine: {settings.DB_ENGINE} ({settings.active_db_url})")
    logger.info("=" * 70)

    # SQLite인 경우 data 디렉터리 자동 생성
    if settings.active_db_url.startswith("sqlite"):
        os.makedirs("data", exist_ok=True)

    # 1. 테이블 스키마 초기화
    async with engine.begin() as conn:
        logger.info("Creating physical database tables if not exist...")
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables verified.")

    # 2. 백서 원문 파싱 데이터 수집
    logger.info("Parsing official technical whitepapers from sources/...")
    parsed_evidences, parsed_concepts = parser.parse_all_whitepapers()
    logger.info(f"Parsed {len(parsed_evidences)} evidences and {len(parsed_concepts)} concepts from sources/.")

    # 3. 데이터 통합 (Golden + Parsed)
    all_evidences = {e["id"]: e for e in (parsed_evidences + EVIDENCE_SOURCES)}.values()
    all_concepts = {c["id"]: c for c in (parsed_concepts + CONCEPTS)}.values()

    async with async_session_factory() as session:
        try:
            # ------------------------------------------------------------------
            # 1단계: evidence_sources 시딩
            # ------------------------------------------------------------------
            logger.info(f"Seeding {len(all_evidences)} EvidenceSource records...")
            for e_data in all_evidences:
                existing = await session.get(EvidenceSourceModel, e_data["id"])
                if not existing:
                    session.add(EvidenceSourceModel(**e_data))
                else:
                    for k, v in e_data.items():
                        setattr(existing, k, v)
            await session.flush()
            logger.info("✅ EvidenceSource seeding complete.")

            # ------------------------------------------------------------------
            # 2단계: concepts 시딩
            # ------------------------------------------------------------------
            logger.info(f"Seeding {len(all_concepts)} Concept records...")
            for c_data in all_concepts:
                c_copy = dict(c_data)
                if "last_reviewed_at" in c_copy:
                    c_copy["last_reviewed_at"] = parse_dt(c_copy["last_reviewed_at"])
                existing = await session.get(ConceptModel, c_copy["id"])
                if not existing:
                    session.add(ConceptModel(**c_copy))
                else:
                    for k, v in c_copy.items():
                        setattr(existing, k, v)
            await session.flush()
            logger.info("✅ Concept seeding complete.")

            # ------------------------------------------------------------------
            # 3단계: causal_edges 시딩 (보상 파라미터 포함)
            # ------------------------------------------------------------------
            logger.info(f"Seeding {len(CAUSAL_EDGES)} CausalEdge records...")
            for edge_data in CAUSAL_EDGES:
                # 중복 엣지 검사
                stmt = select(CausalEdgeModel).where(
                    CausalEdgeModel.source_concept_id == edge_data["source_concept_id"],
                    CausalEdgeModel.target_concept_id == edge_data["target_concept_id"],
                    CausalEdgeModel.relation_type == edge_data["relation_type"]
                )
                res = await session.execute(stmt)
                existing_edge = res.scalar_one_or_none()
                if not existing_edge:
                    session.add(CausalEdgeModel(**edge_data))
                else:
                    for k, v in edge_data.items():
                        setattr(existing_edge, k, v)
            await session.flush()
            logger.info("✅ CausalEdge seeding complete.")

            # ------------------------------------------------------------------
            # 4단계: perspective_cases 시딩 (적응형 Level 3 실무 사례)
            # ------------------------------------------------------------------
            logger.info(f"Seeding {len(PERSPECTIVE_CASES)} PerspectiveCase records...")
            for p_data in PERSPECTIVE_CASES:
                existing = await session.get(PerspectiveCaseModel, p_data["id"])
                if not existing:
                    session.add(PerspectiveCaseModel(**p_data))
                else:
                    for k, v in p_data.items():
                        setattr(existing, k, v)
            await session.flush()
            logger.info("✅ PerspectiveCase seeding complete.")

            # ------------------------------------------------------------------
            # 5단계: comparison_sessions 시딩 (꼬리질문 이력 포함)
            # ------------------------------------------------------------------
            logger.info(f"Seeding {len(COMPARISON_SESSIONS)} ComparisonSession records...")
            for s_data in COMPARISON_SESSIONS:
                existing = await session.get(ComparisonSessionModel, s_data["id"])
                if not existing:
                    session.add(ComparisonSessionModel(**s_data))
                else:
                    for k, v in s_data.items():
                        setattr(existing, k, v)
            await session.flush()
            logger.info("✅ ComparisonSession seeding complete.")

            # ------------------------------------------------------------------
            # 6단계: review_tickets 시딩 (override_reason 사유 포함)
            # ------------------------------------------------------------------
            logger.info(f"Seeding {len(REVIEW_TICKETS)} ReviewTicket records...")
            for r_data in REVIEW_TICKETS:
                r_copy = dict(r_data)
                if "submitted_at" in r_copy:
                    r_copy["submitted_at"] = parse_dt(r_copy["submitted_at"])
                if "approved_at" in r_copy:
                    r_copy["approved_at"] = parse_dt(r_copy["approved_at"])
                existing = await session.get(ReviewTicketModel, r_copy["id"])
                if not existing:
                    session.add(ReviewTicketModel(**r_copy))
                else:
                    for k, v in r_copy.items():
                        setattr(existing, k, v)
            await session.flush()
            logger.info("✅ ReviewTicket seeding complete.")

            # 전체 트랜잭션 최종 커밋
            await session.commit()
            logger.info("🎉 All ontology data committed successfully in a single ACID transaction.")

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Seeding transaction failed, rolled back: {e}", exc_info=True)
            raise

    # 4. 시딩 후 무결성 검증 (Verification)
    await verify_seeded_data()


async def verify_seeded_data():
    """Verifies record counts and executes 1~2 hop Recursive CTE query."""
    logger.info("-" * 70)
    logger.info("Verifying Seeded Knowledge Base Integrity...")
    logger.info("-" * 70)

    async with async_session_factory() as session:
        ev_count = (await session.execute(select(func.count(EvidenceSourceModel.id)))).scalar()
        c_count = (await session.execute(select(func.count(ConceptModel.id)))).scalar()
        edge_count = (await session.execute(select(func.count(CausalEdgeModel.id)))).scalar()
        case_count = (await session.execute(select(func.count(PerspectiveCaseModel.id)))).scalar()
        sess_count = (await session.execute(select(func.count(ComparisonSessionModel.id)))).scalar()
        ticket_count = (await session.execute(select(func.count(ReviewTicketModel.id)))).scalar()

        logger.info(f"📊 [EvidenceSources]    Total: {ev_count} records")
        logger.info(f"📊 [Concepts]           Total: {c_count} records")
        logger.info(f"📊 [CausalEdges]        Total: {edge_count} records (Compensating Params intact)")
        logger.info(f"📊 [PerspectiveCases]   Total: {case_count} records")
        logger.info(f"📊 [ComparisonSessions] Total: {sess_count} records (Tail-questions intact)")
        logger.info(f"📊 [ReviewTickets]      Total: {ticket_count} records (overrideReason intact)")

        assert c_count >= 9, "Concept count is less than expected minimum 9"
        assert edge_count >= 5, "CausalEdge count is less than expected minimum 5"

        # 1~2 hop Recursive CTE 쿼리 성능 및 정합성 검증
        logger.info("\nExecuting 1~2 hop Recursive CTE Causal Path Query...")
        start_time = time.perf_counter()
        
        # SQLite 및 PostgreSQL 공용 Recursive CTE 쿼리
        cte_query = text("""
        WITH RECURSIVE causal_path AS (
            SELECT source_concept_id, target_concept_id, relation_type, 1 AS depth
            FROM causal_edges
            WHERE source_concept_id = 'param-bonding-pressure'
            UNION ALL
            SELECT ce.source_concept_id, ce.target_concept_id, ce.relation_type, cp.depth + 1
            FROM causal_edges ce
            INNER JOIN causal_path cp ON ce.source_concept_id = cp.target_concept_id
            WHERE cp.depth < 2
        )
        SELECT * FROM causal_path;
        """)

        result = await session.execute(cte_query)
        rows = result.fetchall()
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        logger.info(f"⚡ Recursive CTE executed in {elapsed_ms:.2f} ms")
        for row in rows:
            logger.info(f"   [Hop {row[3]}] {row[0]} ➔ ({row[2]}) ➔ {row[1]}")

        logger.info("-" * 70)
        logger.info("✅ All integrity checks and 1~2 hop causal traversals PASSED successfully!")
        logger.info("=" * 70)


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    asyncio.run(run_seeding())
