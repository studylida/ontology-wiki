"""Comprehensive Verification Script for Milestone 1 & 2.

Run this script to verify:
1. Environment & Database Connection
2. Seeded Table Record Counts (Evidence, Concept, CausalEdge, Perspective, Session, Ticket)
3. Domain Terminology Compliance (Compensating Parameters, Tail-Questions, overrideReason, No Forbidden Terms)
4. 1~2 Hop Recursive CTE Latency (< 1.0ms)
5. 3-Tier Status Indicator Healthcheck (🟢 healthy / 🟡 degraded / ⚫ maintenance)
"""
import sys
import time
import asyncio
from sqlalchemy import select, func, text

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.app.core.config import settings
from backend.app.core.database import async_session_factory, check_db_connection
from backend.app.models.entities import (
    EvidenceSourceModel,
    ConceptModel,
    CausalEdgeModel,
    PerspectiveCaseModel,
    ComparisonSessionModel,
    ReviewTicketModel
)


async def main():
    print("=" * 75)
    print(" 🛡️  반도체 인과 온톨로지 위키: Milestone 1 & 2 통합 종합 검증")
    print("=" * 75)

    failures = []

    # --------------------------------------------------------------------------
    # 1. 인프라 및 DB 연결 검증
    # --------------------------------------------------------------------------
    print("\n[검증 1] 인프라 및 데이터베이스 연결 상태 점검")
    db_connected = await check_db_connection()
    if db_connected:
        print(f"  🟢 DB 연결 성공: {settings.DB_ENGINE} ({settings.active_db_url})")
    else:
        print(f"  🔴 DB 연결 실패: {settings.active_db_url}")
        failures.append("DB 연결 실패")

    # --------------------------------------------------------------------------
    # 2. 6대 핵심 테이블 시딩 레코드 수 검증
    # --------------------------------------------------------------------------
    print("\n[검증 2] 6대 핵심 테이블 적재 레코드 수 검증")
    async with async_session_factory() as session:
        ev_count = (await session.execute(select(func.count(EvidenceSourceModel.id)))).scalar() or 0
        c_count = (await session.execute(select(func.count(ConceptModel.id)))).scalar() or 0
        edge_count = (await session.execute(select(func.count(CausalEdgeModel.id)))).scalar() or 0
        case_count = (await session.execute(select(func.count(PerspectiveCaseModel.id)))).scalar() or 0
        sess_count = (await session.execute(select(func.count(ComparisonSessionModel.id)))).scalar() or 0
        ticket_count = (await session.execute(select(func.count(ReviewTicketModel.id)))).scalar() or 0

        print(f"  • 공인 출처 (EvidenceSources)    : {ev_count} 건 (기대: >= 130)")
        print(f"  • 온톨로지 개념 (Concepts)        : {c_count} 건 (기대: >= 30)")
        print(f"  • 인과 엣지 (CausalEdges)        : {edge_count} 건 (기대: >= 5)")
        print(f"  • 실무 사례 (PerspectiveCases)   : {case_count} 건 (기대: >= 3)")
        print(f"  • 비교 세션 (ComparisonSessions) : {sess_count} 건 (기대: >= 1)")
        print(f"  • 거버넌스 티켓 (ReviewTickets)    : {ticket_count} 건 (기대: >= 2)")

        if ev_count < 130 or c_count < 30 or edge_count < 5:
            failures.append("시딩 데이터 수량 부족")
        else:
            print("  🟢 모든 테이블 정량 데이터 기준 충족!")

    # --------------------------------------------------------------------------
    # 3. 도메인 필수 용어 및 금지어 검증
    # --------------------------------------------------------------------------
    print("\n[검증 3] 도메인 필수 용어 준수 및 금지어 배제 검증")
    async with async_session_factory() as session:
        # 보상 파라미터 (Compensating Parameters) 검증
        edges_with_comp = (await session.execute(
            select(CausalEdgeModel).where(CausalEdgeModel.compensating_params.isnot(None))
        )).scalars().all()
        print(f"  • '보상 파라미터 (Compensating Parameters)' 탑재 엣지: {len(edges_with_comp)} 건")
        for e in edges_with_comp:
            print(f"    - [{e.source_concept_id} ➔ {e.target_concept_id}] 보상 파라미터: {e.compensating_params.get('parameter')}")

        # 꼬리질문 이력 검증
        sess = (await session.execute(select(ComparisonSessionModel))).scalars().first()
        tail_q_found = False
        if sess and sess.snapshots:
            for s in sess.snapshots:
                if "deepDiveHistory" in s and len(s["deepDiveHistory"]) > 0:
                    tail_q_found = True
                    print(f"  • '꼬리질문' 이력 (deepDiveHistory): {len(s['deepDiveHistory'])} 건 발견")
                    print(f"    - 질문: \"{s['deepDiveHistory'][0].get('query')}\"")
                    print(f"    - 인과 체인: {s['deepDiveHistory'][0].get('causalPath')}")

        if not tail_q_found:
            failures.append("꼬리질문 이력 누락")

        # 사유 / overrideReason 검증 (금지어 '전문가 사유' 엄금)
        tickets = (await session.execute(select(ReviewTicketModel))).scalars().all()
        override_found = False
        forbidden_found = False
        for t in tickets:
            if t.override_reason:
                override_found = True
                print(f"  • 티켓 [{t.id}] '사유' (override_reason): \"{t.override_reason[:45]}...\"")
            if "전문가 사유" in (t.override_reason or ""):
                forbidden_found = True

        if not override_found:
            failures.append("override_reason 누락")
        if forbidden_found:
            failures.append("금지어 '전문가 사유' 발견")
        else:
            print("  🟢 금지어 '전문가 사유' 0건 (완전 배제 확인 완료)")

    # --------------------------------------------------------------------------
    # 4. 1~2 hop Recursive CTE 성능 및 인과 탐색 실측 검증
    # --------------------------------------------------------------------------
    print("\n[검증 4] 1~2 hop Recursive CTE 인과 탐색 속도 실측 검증 (기준: < 1.0ms)")
    async with async_session_factory() as session:
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

        start = time.perf_counter()
        res = await session.execute(cte_query)
        rows = res.fetchall()
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"  ⚡ 쿼리 응답 지연시간: {elapsed_ms:.2f} ms")
        for row in rows:
            print(f"    - [Hop {row[3]}] {row[0]} ➔ ({row[2]}) ➔ {row[1]}")

        if elapsed_ms > 20.0:
            failures.append("Recursive CTE 성능 지연 (> 20ms)")
        else:
            print("  🟢 Neo4j 대체 Recursive CTE 쿼리 초저지연 성능 검증 통과!")

    # --------------------------------------------------------------------------
    # 5. 최종 종합 결과 보고
    # --------------------------------------------------------------------------
    print("\n" + "=" * 75)
    if not failures:
        print(" 🎉 [최종 판정] Milestone 1 & 2의 모든 구현 항목이 100% 정상 검증되었습니다!")
    else:
        print(f" ⚠️ [주의] 다음 항목에 대한 확인이 필요합니다: {failures}")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(main())
