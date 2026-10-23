"""Read-only verification of an offline seed DB through the original product GET APIs."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace


async def verify(database,seed_dir,sources_dir,report_path):
    os.environ.update(DB_ENGINE='sqlite',SQLITE_DATABASE_URL='sqlite+aiosqlite:///:memory:',USE_IN_MEMORY_REDIS='true')
    from fastapi import FastAPI
    from httpx import ASGITransport,AsyncClient
    from sqlalchemy import text,select
    from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
    from backend.app.api import concepts,admin_sources,search
    from backend.app.core.database import get_db
    from backend.app.core.cache import cache_manager
    from backend.app.core.security import get_current_active_user,get_current_user_optional
    from backend.app.core.llm_gateway import llm_gateway
    from backend.app.models.entities import ConceptModel,PerspectiveCaseModel,SourceDocumentModel
    from backend.app.repositories.source_repo import source_repo
    from backend.app.repositories.concept_repo import concept_repo
    manifest=json.loads((seed_dir/'manifest.json').read_text(encoding='utf-8'))
    assert database.is_file()
    engine=create_async_engine('sqlite+aiosqlite:///file:'+database.as_posix()+'?mode=ro&uri=true')
    factory=async_sessionmaker(engine,expire_on_commit=False)
    async def db_dependency():
        async with factory() as db:yield db
    app=FastAPI();app.include_router(concepts.router,prefix='/api/v1');app.include_router(admin_sources.router,prefix='/api/v1');app.include_router(search.router,prefix='/api/v1')
    app.dependency_overrides[get_db]=db_dependency
    app.dependency_overrides[get_current_user_optional]=lambda:None
    app.dependency_overrides[get_current_active_user]=lambda:SimpleNamespace(level=4,id='isolated-seed-verifier',name='Seed verifier')
    source_repo.sources_dir=sources_dir
    calls=0
    async def forbidden(*args,**kwargs):
        nonlocal calls
        calls+=1;raise AssertionError('A read-only seed check attempted a model call.')
    generate=llm_gateway.generate_text;llm_gateway.generate_text=forbidden
    try:
        await cache_manager.init()
        async with factory() as db:
            ids=(await db.execute(select(ConceptModel.id))).scalars().all()
            stored_cases=(await db.execute(select(PerspectiveCaseModel))).scalars().all()
            docs=(await db.execute(select(SourceDocumentModel))).scalars().all()
            assert set(ids)==set(manifest['conceptMetadata'])
            assert len(docs)==len(manifest['documents'])
            assert (await db.execute(text('PRAGMA integrity_check'))).scalar_one()=='ok'
            assert not (await db.execute(text('PRAGMA foreign_key_check'))).all()
            for doc in docs:
                assert 'seedExplanation' not in json.dumps(doc.last_preview_payload or [])
                for item in doc.last_preview_payload or []:
                    assert item['_seedProvenance']['generationMethod']=='codex-offline-source-review'
                    assert item['sourceCoverage']['complete']
            tables=('concepts','perspective_cases','causal_edges','evidence_sources','source_documents')
            async def fingerprint():
                result={name:[list(row) for row in (await db.execute(text('SELECT * FROM '+name+' ORDER BY 1'))).all()] for name in tables}
                return hashlib.sha256(json.dumps(result,sort_keys=True,default=str).encode()).hexdigest()
            before=await fingerprint()
        details={};case_states={};preview_count=0;scale_count=0;inverse_count=0;search_count=0;reviewed_count=0;reviewed_relations=0;reviewed_scales=0;changed_scales=0;scale_trees=0
        async with AsyncClient(transport=ASGITransport(app=app),base_url='http://isolated') as client:
            for concept_id in ids:
                response=await client.get('/api/v1/concepts/'+concept_id)
                assert response.status_code==200,(concept_id,response.text)
                detail=response.json();details[concept_id]=detail
                assert detail['summary'].strip()
                ladder=detail.get('scaleLadder') or []
                if ladder:
                    scale_count+=1
                    ids_in_ladder={node['entityId'] for node in ladder}
                    assert concept_id in ids_in_ladder
                    assert all(0<=node['hops']<=2 for node in ladder)
                    assert all(link['source'] in ids_in_ladder and link['target'] in ids_in_ladder for node in ladder for link in node['connections'])
                inverse_count+=bool(detail['enrichedRelations'].get('hasParts') or detail['enrichedRelations'].get('subtypes'))
                for case in detail['perspectives']:
                    case_states[case['id']]=case['contextExplanationState']
                    if case['contextExplanationState']=='ready':
                        assert case['contextExplanation']['content']['explanation'].strip()
                    else:
                        assert not case.get('contextExplanation')
            for info in manifest['documents']:
                assert hashlib.sha256((sources_dir/info['filePath']).read_bytes()).hexdigest()==info['sourceHash']
                response=await client.get('/api/v1/admin/sources/'+info['docId']+'/preview')
                assert response.status_code==200,(info['index'],response.text)
                preview_count+=1
            for query, expected_id in [('', None), *((detail['title'], cid) for cid, detail in details.items())]:
                response=await client.get('/api/v1/search/spotlight',params={'q':query})
                assert response.status_code==200,response.text
                result=response.json()
                assert result['totalIndexed']==len(ids)
                returned={row['id'] for row in result['results']}
                assert returned<=set(ids)
                assert all(row['scaleLevel']==details[row['id']]['scaleLevel'] for row in result['results'])
                if expected_id:assert expected_id in returned,(query,expected_id)
                search_count+=1
            for detail in details.values():
                assert detail['scaleLevel']==manifest['conceptMetadata'][detail['id']]['scaleLevel']
                for group in detail['enrichedRelations'].values():
                    for item in group:
                        if item['isRegistered']:
                            assert item['scaleLevel']==details[item['id']]['scaleLevel']
                for node in detail.get('scaleLadder') or []:
                    assert node['scaleLevel']==details[node['entityId']]['scaleLevel']
            for scale in range(1,6):
                response=await client.get('/api/v1/concepts/tree',params={'scale':scale})
                assert response.status_code==200,response.text
                result=response.json()
                children=[child for category in result['tree'] for child in category['children']]
                expected={cid for cid,detail in details.items() if detail['scaleLevel']==scale}
                assert {child['id'] for child in children}==expected
                assert len(children)==len(expected)==result['totalNodes']
                assert all(child['scaleLevel']==scale for child in children)
                scale_trees+=1
            scale_info=manifest.get('scaleReview')
            if scale_info:
                scale_review=json.loads((seed_dir/scale_info['file']).read_text(encoding='utf-8'))
                assert len(scale_review['concepts'])==len(ids)
                assert {row['conceptId'] for row in scale_review['concepts']}==set(ids)
                for row in scale_review['concepts']:
                    assert details[row['conceptId']]['scaleLevel']==row['newScale']
                    assert (row['oldScale']!=row['newScale'])==(row['decision']=='change')
                reviewed_scales=len(scale_review['concepts'])
                changed_scales=sum(row['decision']=='change' for row in scale_review['concepts'])
            review_info=manifest.get('relationReview')
            if review_info:
                review=json.loads((seed_dir/review_info['file']).read_text(encoding='utf-8'))
                assert {row['conceptId'] for row in review['concepts']}==set(review['targetConceptIds'])
                assert set(review['targetConceptIds'])<=set(ids)
                for relation in review['addedRelations']:
                    assert any(item['id']==relation['targetId'] and item['isRegistered'] for item in details[relation['conceptId']]['enrichedRelations'][relation['field']]),relation
                    reviewed_relations+=1
                reviewed_count=len(review['concepts'])
            for concept_id in ('cmp','hybrid-bonding','photolithography','hbm'):
                response=await client.get('/api/v1/concepts/'+concept_id+'/causal-subgraph')
                assert response.status_code==200,response.text
        async with factory() as db:
            after=await fingerprint()
            assert before==after,'GET changed stored knowledge.'
        assert len(case_states)==len(stored_cases)
        assert all(state in ('ready','restricted') for state in case_states.values())
        assert calls==0
        result=dict(verifiedConceptDetails=len(details),verifiedDocumentPreviews=preview_count,
            cases=len(case_states),ready=sum(s=='ready' for s in case_states.values()),restricted=sum(s=='restricted' for s in case_states.values()),
            conceptsWithScaleConnections=scale_count,conceptsWithInverseHierarchy=inverse_count,
            verifiedSearchQueries=search_count,reviewedUnconnectedConcepts=reviewed_count,verifiedAddedRelations=reviewed_relations,
            reviewedConceptScales=reviewed_scales,correctedConceptScales=changed_scales,verifiedScaleTrees=scale_trees,
            externalModelCalls=calls,readOnlyKnowledgeFingerprintUnchanged=True,sourceHashesUnchanged=True,integrity='ok',foreignKeyViolations=0)
        report_path.parent.mkdir(parents=True,exist_ok=True)
        report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False),flush=True)
    finally:
        llm_gateway.generate_text=generate
        await engine.dispose()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--seed-dir',type=Path,required=True)
    parser.add_argument('--sources-dir',type=Path,default=Path(__file__).resolve().parents[1]/'sources')
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    asyncio.run(verify(args.database.resolve(),args.seed_dir.resolve(),args.sources_dir.resolve(),args.report.resolve()))


if __name__=='__main__':main()
