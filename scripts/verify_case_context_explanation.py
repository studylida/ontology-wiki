"""Stored case explanation regression checks: isolated memory DB, mocked model only."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

os.environ.update(DB_ENGINE="sqlite", SQLITE_DATABASE_URL="sqlite+aiosqlite:///:memory:", USE_IN_MEMORY_REDIS="true")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import BackgroundTasks, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from backend.app.api import admin_sources, concepts
from backend.app.core.database import Base, get_db
from backend.app.core.security import get_current_active_user, get_current_user_optional
from backend.app.models.entities import ConceptModel, EvidenceSourceModel, PerspectiveCaseModel
from backend.app.repositories.concept_repo import concept_repo
from backend.app.repositories.source_repo import source_repo
from backend.app.schemas.source_ingestion import ApplyExtractionRequestDTO, ApplyExtractionResponseDTO
from backend.app.services.case_explanation_service import CaseExplanationService, CaseExplanationChanged, CaseExplanationUnavailable


async def checks():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    service = CaseExplanationService(factory)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    spec = {"parameter": "측정 폭", "value": "약 25", "unit": "µm", "isConfidential": False,
            "role": "공개 측정 결과", "evidenceIds": ["public-source"]}
    async with factory() as db:
        db.add(ConceptModel(id="concept", title="공개 기술", eng_name="Public technology", domain_facet="unit_process",
            process_category="검증", scale_level=3, summary="공개 원문의 정의", purpose="측정 맥락 이해"))
        db.add(EvidenceSourceModel(id="public-source", source_name="공개 자료", source_type="source_document", publisher="fixture",
            quote="검증 상황에서 약 25 µm로 측정했다.", external_url="https://example.invalid/public", url_label="공개 원문", credibility_tier="공개 원문"))
        db.add(EvidenceSourceModel(id="internal-source", source_name="제한 자료", source_type="source_document", publisher="fixture",
            quote="제한 맥락", external_url="", url_label="내부", credibility_tier="internal"))
        for case_id, specifications, evidence in (("public", [spec], "public-source"),
            ("restricted", [{**spec, "value": "SECRET-987654", "isConfidential": True}], None),
            ("legacy", [], None), ("mixed", [spec, {"parameter": "제한", "value": "SECRET-987654"}], "public-source")):
            db.add(PerspectiveCaseModel(id=case_id, concept_id="concept", perspective_id=case_id, perspective_title=case_id,
                perspective_badge="검증", context_narrative="공개 실험 상황" if case_id == "public" else "제한 맥락 SECRET-987654",
                specifications=specifications, caution="이 상황의 결과", evidence_id=evidence, updated_at=datetime(2020, 1, 1)))
        await db.commit()

    async def fields(case_id="public"):
        async with factory() as db:
            concept = await concept_repo.get_by_id(db, "concept")
            case = await concept_repo.get_case(db, "concept", case_id)
            return await service.fields(db, concept, case)

    async def change(**values):
        async with factory() as db:
            case = await concept_repo.get_case(db, "concept", "public")
            values["updated_at"] = max(datetime.utcnow(), case.updated_at + timedelta(microseconds=1))
            await db.execute(update(PerspectiveCaseModel).where(PerspectiveCaseModel.id == "public").values(**values))
            await db.commit()

    response_json = json.dumps({"explanation": "이 값은 특정 실험 상황에서 측정한 폭을 뜻합니다."}, ensure_ascii=False)
    gateway = AsyncMock(return_value=response_json)
    user = SimpleNamespace(level=3, name="격리 검토관", id="isolated-user")
    async def session_dependency():
        async with factory() as db:
            yield db
    app = FastAPI()
    app.include_router(concepts.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = session_dependency
    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[get_current_user_optional] = lambda: None

    try:
        with patch("backend.app.agents.explainer_agent.llm_gateway.generate_text", gateway), \
             patch.object(concepts, "case_explanation_service", service), \
             patch("backend.app.services.concept_service.case_explanation_service", service), \
             patch.object(admin_sources, "case_explanation_service", service):
            assert (await fields())["contextExplanationState"] == "missing"
            result = await service.generate("concept", "public")
            assert result["contextExplanationState"] == "ready" and result["contextExplanation"]["content"]["background"] is None
            initial_count = gateway.call_count
            assert (await service.generate("concept", "public")) == result
            assert (await fields()) == result and gateway.call_count == initial_count
            for case_id in ("restricted", "legacy", "mixed"):
                assert (await fields(case_id))["contextExplanationState"] == "restricted"
                try:
                    await service.generate("concept", case_id)
                    raise AssertionError("restricted case generated")
                except PermissionError:
                    pass
            assert gateway.call_count == initial_count
            assert all("SECRET-987654" not in call.kwargs["prompt"] for call in gateway.call_args_list)

            # Reapplying the same source fields preserves the stored derived column.
            raw_case = {"id": "public", "perspectiveTitle": "public", "perspectiveBadge": "검증", "narrative": "공개 실험 상황",
                        "specifications": [spec], "caution": "이 상황의 결과", "evidenceId": "public-source"}
            async with factory() as db:
                await source_repo.save_perspective_cases(db, "concept", [raw_case])
                await db.commit()
            await service.generate("concept", "public")
            assert gateway.call_count == initial_count

            # Preview enriches only its response and never mutates source state/history.
            state = {"summary": "공개 원문의 정의", "purpose": "측정 맥락 이해", "perspectiveCases": [deepcopy(raw_case)]}
            before = deepcopy(state)
            async with factory() as db:
                preview = await service.preview_fields(db, "concept", "공개 기술", state)
                assert preview["public"]["contextExplanationState"] == "ready" and state == before
                state["perspectiveCases"][0]["caution"] = "변경 제안"
                changed_preview = await service.preview_fields(db, "concept", "공개 기술", state)
                assert changed_preview["public"]["contextExplanation"] is None
                draft = deepcopy(state)
                draft_case = draft["perspectiveCases"][0]
                draft_case.update(id="new-draft", evidenceId="not-yet-persisted")
                draft_case["specifications"] = [{**spec, "evidenceIds": ["not-yet-persisted"]}]
                untouched = deepcopy(draft)
                new_preview = await service.preview_fields(db, "new-concept", "새 공개 기술", draft)
                assert new_preview["new-draft"]["contextExplanationState"] == "missing"
                assert new_preview["new-draft"]["contextExplanation"] is None and draft == untouched
                draft_case["specifications"][0]["isConfidential"] = True
                restricted_preview = await service.preview_fields(db, "new-concept", "새 기술", draft)
                assert restricted_preview["new-draft"]["contextExplanationState"] == "restricted"
                draft_case.update(evidenceId="internal-source", specifications=[{**spec, "evidenceIds": ["internal-source"]}])
                internal_preview = await service.preview_fields(db, "new-concept", "새 기술", draft)
                assert internal_preview["new-draft"]["contextExplanationState"] == "restricted"
                draft_case.update(evidenceId=None, specifications=[{**spec, "evidenceIds": []}])
                unknown_preview = await service.preview_fields(db, "new-concept", "새 기술", draft)
                assert unknown_preview["new-draft"]["contextExplanationState"] == "restricted"
            assert gateway.call_count == initial_count

            await change(caution="특정 실험 조건에서만 유효")
            assert (await fields())["contextExplanationState"] == "stale" and (await fields())["contextExplanation"] is None
            await service.generate("concept", "public")
            assert gateway.call_count == initial_count + 1
            await change(specifications=[{**spec, "isConfidential": True}])
            assert (await fields())["contextExplanationState"] == "restricted" and (await fields())["contextExplanation"] is None
            await change(specifications=[spec], caution="수정 후 공개 사례")

            # Bad JSON fails only the auxiliary request; original data and prior saved explanation survive.
            gateway.return_value = "not JSON"
            async with factory() as db:
                old_saved = deepcopy((await concept_repo.get_case(db, "concept", "public")).context_explanation)
            try:
                await service.generate("concept", "public")
                raise AssertionError("invalid model result accepted")
            except CaseExplanationUnavailable:
                pass
            async with factory() as db:
                case = await concept_repo.get_case(db, "concept", "public")
                assert case.caution == "수정 후 공개 사례" and case.context_explanation == old_saved

            gateway.return_value = response_json
            entered, release = asyncio.Event(), asyncio.Event()
            async def delayed(**kwargs):
                entered.set()
                await release.wait()
                return response_json
            gateway.side_effect = delayed
            first = asyncio.create_task(service.generate("concept", "public"))
            await entered.wait()
            second = asyncio.create_task(service.generate("concept", "public"))
            await asyncio.sleep(0)
            concurrent_count = gateway.call_count
            release.set()
            assert (await first) == (await second) and gateway.call_count == concurrent_count

            # A disconnected caller must not leave a completed task marked as generating.
            await change(caution="연결 종료")
            entered.clear(); release.clear()
            disconnected = asyncio.create_task(service.generate("concept", "public"))
            await entered.wait()
            disconnected.cancel()
            try:
                await disconnected
            except asyncio.CancelledError:
                pass
            running = list(service.inflight.values())
            release.set()
            await asyncio.gather(*running)
            await asyncio.sleep(0)
            assert not service.inflight

            # Content mutation while a model call is pending prevents stale storage.
            await change(caution="판본 A")
            entered.clear(); release.clear()
            pending = asyncio.create_task(service.generate("concept", "public"))
            await entered.wait()
            await change(caution="판본 B")
            release.set()
            try:
                await pending
                raise AssertionError("outdated explanation stored")
            except CaseExplanationChanged:
                pass
            gateway.side_effect = None

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://isolated") as client:
                endpoint = "/api/v1/concepts/concept/perspectives/public/context-explanation"
                user.level = 2
                assert (await client.post(endpoint)).status_code == 403
                user.level = 3
                assert (await client.post(endpoint.replace("/concept/perspectives", "/other/perspectives"))).status_code == 404
                assert (await client.post(endpoint)).status_code == 200
                count = gateway.call_count
                assert (await client.get("/api/v1/concepts/concept")).status_code == 200
                assert gateway.call_count == count
                await change(caution="API 모델 실패 검증")
                gateway.return_value = "broken JSON"
                assert (await client.post(endpoint)).status_code == 502
            gateway.return_value = response_json

            # The admin controller schedules only after the source service has committed.
            async def committed_apply(**kwargs):
                await change(caution="커밋 완료 후 자동 생성")
                return ApplyExtractionResponseDTO(appliedCount=1, updatedConcepts=["concept"], message="isolated")
            tasks = BackgroundTasks()
            with patch.object(admin_sources.source_service, "apply_extractions_to_wiki", committed_apply):
                async with factory() as db:
                    count = gateway.call_count
                    await admin_sources.apply_extractions_to_wiki(ApplyExtractionRequestDTO(docIds=["isolated-document"]), tasks,
                        x_gemini_key=None, x_openai_key=None, current_user=SimpleNamespace(name="검토관"), db=db)
                    assert gateway.call_count == count and service.scheduled["concept"] == 1
                assert (await fields())["contextExplanationState"] == "generating"
                await tasks()
                assert (await fields())["contextExplanationState"] == "ready" and not service.scheduled

            # Deletion while generating is a version conflict, not a recreated case.
            await change(caution="삭제 경합")
            entered.clear(); release.clear(); gateway.side_effect = delayed
            pending = asyncio.create_task(service.generate("concept", "public"))
            await entered.wait()
            async with factory() as db:
                await db.execute(delete(PerspectiveCaseModel).where(PerspectiveCaseModel.id == "public"))
                await db.commit()
            release.set()
            try:
                await pending
                raise AssertionError("deleted case regenerated")
            except CaseExplanationChanged:
                pass
            assert not service.inflight
        print("PASS: persisted reuse, qualifiers/stale, restricted isolation, source reapply, preview purity, model failure, coalescing, mutation/deletion conflict, API permissions, admin post-commit scheduling")
        print("Not checked here: full review approval transaction, live PostgreSQL, real model or browser UI.")
    finally:
        await engine.dispose()


async def public_source_checks():
    from backend.app.models.entities import SourceDocumentModel, ReviewTicketModel
    from backend.app.services.concept_service import ConceptService
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    factory = async_sessionmaker(engine, expire_on_commit=False)
    service = CaseExplanationService(factory)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    content = dict(perspectiveTitle='수치 없는 공개 사례', perspectiveBadge='발행사', narrative='공개된 작동 방식', caution='적용 맥락', specifications=[])
    async with factory() as db:
        db.add(ConceptModel(id='source-concept', title='공개 기술', eng_name='', domain_facet='unit_process', process_category='검증', scale_level=3, summary='정의', purpose='목적'))
        db.add(EvidenceSourceModel(id='source-proof', source_name='공개 원문', source_type='source_document', publisher='발행사', quote='공개된 작동 방식', section_context='public.md', external_url='', url_label='로컬 원문', credibility_tier='원문 자료'))
        for cid in ('from-source', 'unrecorded'):
            db.add(PerspectiveCaseModel(id=cid,concept_id='source-concept',perspective_id=cid,perspective_title=content['perspectiveTitle'],perspective_badge=content['perspectiveBadge'],context_narrative=content['narrative'],caution=content['caution'],specifications=[],evidence_id='source-proof'))
        db.add(SourceDocumentModel(doc_id='public-doc',file_path='public.md',publisher='발행사',title='문헌',file_hash='hash',is_applied=False,last_applied_at=datetime.utcnow(),last_preview_payload=[dict(conceptId='source-concept',_appliedCases={'from-source':content})]))
        await db.commit()
    try:
        async with factory() as db:
            concept=await concept_repo.get_by_id(db,'source-concept')
            case=await concept_repo.get_case(db,'source-concept','from-source')
            assert (await service.fields(db,concept,case))['contextExplanationState']=='missing'
            assert (await service.public_input(db,concept,case))['case']['specifications']==[]
            unknown=await concept_repo.get_case(db,'source-concept','unrecorded')
            assert await service.public_input(db,concept,unknown) is None
            for attr in ('perspective_title','perspective_badge','context_narrative','caution'):
                original=getattr(case,attr);setattr(case,attr,'PRIVATE-CONTENT')
                assert await service.public_input(db,concept,case) is None,attr
                setattr(case,attr,original)
            case.specifications=[dict(parameter='秘密',value='SECRET',isConfidential=True)]
            assert await service.public_input(db,concept,case) is None
            case.specifications=[]
            evidence=await db.get(EvidenceSourceModel,'source-proof');evidence.credibility_tier='internal'
            assert await service.public_input(db,concept,case) is None
            evidence.credibility_tier='원문 자료'
            await db.rollback()
        gateway=AsyncMock(return_value=json.dumps(dict(explanation='수치가 없어도 작동 방식과 적용 맥락을 풀어 설명합니다.'),ensure_ascii=False))
        with patch('backend.app.agents.explainer_agent.llm_gateway.generate_text',gateway):
            assert (await service.generate('source-concept','from-source'))['contextExplanationState']=='ready'
            assert gateway.call_count==1
        async with factory() as db:
            db.add(ReviewTicketModel(id='private-override',concept_id='source-concept',concept_title='공개 기술',title='비공개 전환',review_type='revision',author='검토관',status='approved',current_content='',ai_merged_draft='',integrity_report={},approved_at=datetime.utcnow(),structured_patches=[dict(path='/workingDraft',value=dict(state=dict(perspectiveCases=[dict(id='from-source',isPublic=False,**content)])))]))
            await db.commit()
        async with factory() as db:
            concept=await concept_repo.get_by_id(db,'source-concept');case=await concept_repo.get_case(db,'source-concept','from-source')
            assert await service.public_input(db,concept,case) is None
        nodes=[SimpleNamespace(id=cid,title=cid,summary=cid,scale_level=scale,scale_name=None,relations=relations) for cid,scale,relations in (
            ('a',1,{'part_of':[{'id':'b','reason':'원문 구성 근거'}]}),('b',2,{'is_a':[{'id':'c','reason':'원문 분류 근거'}]}),
            ('c',3,{'next_step':[{'id':'d','reason':'원문 후속 근거'}]}),('d',4,{}),('unrelated',5,{}))]
        ladder=ConceptService.build_scale_ladder(nodes[0],nodes,[])
        assert {node.entityId for node in ladder}=={'a','b','c'}
        assert {node.entityId:node.hops for node in ladder}=={'a':0,'b':1,'c':2}
        assert {(edge.source,edge.target,edge.relationType) for node in ladder for edge in node.connections}=={('a','b','part_of'),('b','c','is_a')}
        assert ConceptService.build_scale_ladder(nodes[-1],nodes,[])==[]
        print('PASS: number-free applied public source explanation, full-content provenance, reextraction history, private/legacy/override isolation, typed two-hop scale neighborhood')
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(checks())
    asyncio.run(public_source_checks())
