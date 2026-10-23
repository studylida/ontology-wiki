"""Build a NEW SQLite wiki from reviewed source artifacts, without external model calls.

Uses the product source preview/apply and case explanation services; existing DBs are refused.
"""
import argparse
import asyncio
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys


async def build(seed_dir, database, sources_dir, report_dir):
    # Configure isolation before importing product settings, engines, or service singletons.
    if database.exists():
        raise FileExistsError('Target database already exists; choose a new file. Nothing was changed.')
    if not database.parent.is_dir():
        raise FileNotFoundError('Create the target parent directory explicitly first.')
    os.environ.update(DB_ENGINE='sqlite', SQLITE_DATABASE_URL='sqlite+aiosqlite:///'+database.as_posix(),
                      USE_IN_MEMORY_REDIS='true')
    from backend.app.core.database import Base, engine, async_session_factory
    from backend.app.core.cache import cache_manager
    from backend.app.core.llm_gateway import llm_gateway
    from backend.app.models.entities import SourceDocumentModel, ConceptModel, PerspectiveCaseModel, CausalEdgeModel, EvidenceSourceModel
    from backend.app.repositories.source_repo import source_repo
    from backend.app.repositories.concept_repo import concept_repo
    from backend.app.services.source_service import source_service
    from backend.app.services.case_explanation_service import case_explanation_service
    from backend.app.agents.explainer_agent import explainer_agent
    from backend.app.schemas.source_ingestion import ExtractedConceptDiffDTO
    from backend.app.schemas.ontology import CaseContextContentDTO
    from sqlalchemy import select, func, text

    if Path(engine.url.database).resolve()!=database:
        raise RuntimeError('Application engine does not point at the explicitly selected new database.')
    manifest=json.loads((seed_dir/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('generationMethod')!='codex-offline-source-review' or manifest.get('externalModelCalls')!=0:
        raise ValueError('Reviewed offline seed provenance is required.')
    source_repo.sources_dir=sources_dir
    records=[];seen_paths=set();concept_ids=set()
    for info in manifest['documents']:
        path=(sources_dir/info['filePath']).resolve()
        if not path.is_relative_to(sources_dir):
            raise ValueError('Source path escapes the selected source directory.')
        data=path.read_bytes()
        record=json.loads((seed_dir/'documents'/f"{info['index']:03d}.json").read_text(encoding='utf-8'))
        if info['filePath'] in seen_paths:
            raise ValueError('Duplicate document in manifest.')
        seen_paths.add(info['filePath'])
        if record['filePath']!=info['filePath'] or record['sourceHash']!=hashlib.sha256(data).hexdigest() or record['sourceHash']!=info['sourceHash']:
            raise ValueError('Source hash or document identity changed: '+info['filePath'])
        review=record['review']
        if review.get('wholeDocumentRead') is not True or review.get('rawCharactersRead')!=len(path.read_text(encoding='utf-8')):
            raise ValueError('Whole-document review is not recorded: '+info['filePath'])
        if record['index']!=info['index']:
            raise ValueError('Seed document index mismatch.')
        for item in record['concepts']:
            if not item['summary'].strip():
                raise ValueError('A proposed concept has no definition.')
            ExtractedConceptDiffDTO(**item)
            concept_ids.add(item['conceptId'])
        records.append((info,record))
    if set(manifest['conceptMetadata'])!=concept_ids:
        raise ValueError('Canonical classification metadata is incomplete.')
    for concept_id,aliases in manifest.get('conceptAliases',{}).items():
        if concept_id not in concept_ids or not isinstance(aliases,list) or any(not isinstance(name,str) or not name.strip() for name in aliases):
            raise ValueError('Reviewed alias metadata is invalid.')
    if set(path.relative_to(sources_dir).as_posix() for path in sources_dir.rglob('*.md'))!=seen_paths:
        raise ValueError('The source document inventory changed; regenerate/review the manifest.')
    order=manifest.get('applicationOrder',[info['index'] for info,_ in records])
    if len(order)!=len(records) or set(order)!={info['index'] for info,_ in records}:
        raise ValueError('Application order must contain every reviewed document exactly once.')
    records.sort(key=lambda pair:order.index(pair[0]['index']))

    calls=0
    async def forbidden_call(*args,**kwargs):
        nonlocal calls
        calls+=1
        raise RuntimeError('External model calls are disabled in offline seed creation.')
    explanations={}
    async def offline_explanation(public_input,session_id,**keys):
        case_id=public_input['case']['id']
        if case_id not in explanations:
            raise ValueError('No authored explanation for this case: '+case_id)
        return CaseContextContentDTO.model_validate(explanations[case_id])
    original_gateway=llm_gateway.generate_text
    original_explainer=explainer_agent.explain_case_context
    llm_gateway.generate_text=forbidden_call
    explainer_agent.explain_case_context=offline_explanation
    report=dict(generationMethod=manifest['generationMethod'],database=str(database),operationalWrites=False,
                externalModelCalls=0,documents=[],warnings=[],caseExplanations={})
    try:
        await cache_manager.init()
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        for info,record in records:
            relative=info['filePath'];path=sources_dir/relative
            raw_text=path.read_text(encoding='utf-8');cleaned=source_service.clean_web_noise(raw_text)
            parts=source_service.document_parts(cleaned)
            coverage=dict(complete=True,totalParts=len(parts),processedParts=len(parts),
                          totalCharacters=len(cleaned),processedCharacters=len(cleaned),sourceHash=info['sourceHash'])
            authored={}
            payload=[]
            for raw in record['concepts']:
                item=deepcopy(raw)
                item['_seedProvenance']=dict(generationMethod=manifest['generationMethod'],review=record['review'],sourceHash=info['sourceHash'])
                for case in item.get('perspectiveCases') or []:
                    explanation=case.pop('seedExplanation',None)
                    if explanation:
                        CaseContextContentDTO.model_validate(explanation)
                        authored[(item['conceptId'],case['perspectiveTitle'],case['narrative'])]=explanation
                item['sourceCoverage']=coverage
                item['sourceDocumentTitle']=info['title']
                item['sourceUrl']=info.get('sourceUrl')
                dto=ExtractedConceptDiffDTO(**item)
                payload.append({**dto.model_dump(by_alias=True),'_seedProvenance':item['_seedProvenance']})
            now=datetime.utcnow()
            doc=SourceDocumentModel(doc_id=info['docId'],file_path=relative,title=info['title'],publisher=info['publisher'],
                file_hash=info['sourceHash'],attempt_status='success' if payload else 'reviewed_empty',
                last_attempted_at=now,last_succeeded_at=now if payload else None,
                last_succeeded_hash=info['sourceHash'] if payload else None,last_preview_payload=payload,
                extracted_concepts_count=len(payload),extracted_relations_count=sum(len(item.get(k) or []) for item in payload
                    for k in ('previousSteps','nextSteps','alternatives','partOf','isA')),is_applied=False)
            async with async_session_factory() as db:
                db.add(doc);await db.commit()
                if payload:
                    prepared=await source_service.prepare_preview(db,doc,payload)
                    blockers=[dict(conceptId=item['conceptId'],reasons=item['applyBlockers']) for item in prepared if item['applyBlockers']]
                    if blockers:
                        raise ValueError('Preview blocks application: '+json.dumps(blockers,ensure_ascii=False))
                    for item in prepared:
                        for case in item['_caseUpdates']:
                            key=(item['conceptId'],case['perspectiveTitle'],case['narrative'])
                            if key in authored:explanations[case['id']]=authored[key]
                    applied=await source_service.apply_extractions_to_wiki(db,[doc.doc_id],reviewed_by='Codex offline seed source review',
                        concept_metadata={cid:value for cid,value in manifest['conceptMetadata'].items() if cid in {item['conceptId'] for item in payload}})
                    if applied.applied_count!=1:
                        raise ValueError('Expected one applied document.')
                    # The same service preserves idempotency and never reapplies a completed source.
                    repeated=await source_service.apply_extractions_to_wiki(db,[doc.doc_id],reviewed_by='Codex offline seed source review')
                    if repeated.applied_count!=0:
                        raise ValueError('Source application is not idempotent.')
                    report['warnings'].extend(dict(filePath=relative,conceptId=item['conceptId'],messages=item.get('validationWarnings',[]))
                        for item in prepared if item.get('validationWarnings'))
                entry=dict(index=info['index'],filePath=relative,conceptContributions=len(payload),
                           status='applied' if payload else 'reviewed_no_technical_content',review=record['review'])
                report['documents'].append(entry)
                print(json.dumps(dict(index=info['index'],status=entry['status'],contributions=len(payload)),ensure_ascii=True),flush=True)
        async with async_session_factory() as db:
            for concept_id,aliases in manifest.get('conceptAliases',{}).items():
                await concept_repo.merge_aliases(db,concept_id,aliases)
            await db.flush()
            await concept_repo.reconcile_relation_edges(db)
            await db.commit()
            ids=(await db.execute(select(PerspectiveCaseModel.concept_id,PerspectiveCaseModel.id))).all()
        for concept_id,case_id in ids:
            try:
                fields=await case_explanation_service.generate(concept_id,case_id)
                report['caseExplanations'][case_id]=fields['contextExplanationState']
            except PermissionError:
                report['caseExplanations'][case_id]='restricted'
        async with async_session_factory() as db:
            report['counts']={model.__tablename__:await db.scalar(select(func.count()).select_from(model))
                for model in (ConceptModel,PerspectiveCaseModel,CausalEdgeModel,EvidenceSourceModel,SourceDocumentModel)}
            report['foreignKeyViolations']=[list(row) for row in (await db.execute(text('PRAGMA foreign_key_check'))).all()]
            report['integrityCheck']=await db.scalar(text('PRAGMA integrity_check'))
            if report['foreignKeyViolations'] or report['integrityCheck']!='ok':
                raise ValueError('SQLite integrity verification failed.')
            applied_ids=(await db.execute(select(SourceDocumentModel.doc_id).where(SourceDocumentModel.is_applied.is_(True)))).all()
            if len(applied_ids)!=sum(bool(r['concepts']) for _,r in records):
                raise ValueError('Applied document count differs from reviewed contributions.')
            persisted=(await db.execute(select(ConceptModel))).scalars().all()
            if {c.id for c in persisted}!=concept_ids:
                raise ValueError('Applied concept identities differ from the reviewed registry.')
            for concept in persisted:
                if not set(manifest.get('conceptAliases',{}).get(concept.id,[]))<=set(concept.aliases or []):
                    raise ValueError('Reviewed aliases were not preserved.')
            report['unregisteredReferences']=[dict(conceptId=c.id,relationType=kind,targetId=link.get('id') or link.get('targetId'),name=link.get('name'))
                for c in persisted for kind,links in (c.relations or {}).items() for link in concept_repo.relation_items(links)
                if (link.get('id') or link.get('targetId')) not in concept_ids]
        if calls:
            raise RuntimeError('An external model call was attempted.')
        report['complete']=True
    except Exception as error:
        report['complete']=False;report['error']=str(error)
        raise
    finally:
        llm_gateway.generate_text=original_gateway
        explainer_agent.explain_case_context=original_explainer
        report['externalModelCalls']=calls
        report_dir.mkdir(parents=True,exist_ok=True)
        (report_dir/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        await engine.dispose()
    print(json.dumps(dict(complete=True,counts=report['counts'],externalModelCalls=calls),ensure_ascii=True),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed-dir',type=Path,required=True)
    parser.add_argument('--database',type=Path,required=True)
    parser.add_argument('--sources-dir',type=Path,default=Path(__file__).resolve().parents[1]/'sources')
    parser.add_argument('--report-dir',type=Path,required=True)
    args=parser.parse_args()
    repo=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(repo))
    asyncio.run(build(args.seed_dir.resolve(),args.database.resolve(),args.sources_dir.resolve(),args.report_dir.resolve()))


if __name__=='__main__':main()
