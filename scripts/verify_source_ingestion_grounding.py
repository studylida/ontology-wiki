"""Bounded source-ingestion regressions: no external model calls or operational DB writes."""
import asyncio
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.app.api import admin_sources, concepts
from backend.app.core.database import Base, get_db
from backend.app.core.dlp_tokenizer import RegimeAwareTokenizer
from backend.app.core.security import get_current_active_user, get_current_user_optional
from backend.app.models.entities import SourceDocumentModel, ConceptModel, EvidenceSourceModel
from sqlalchemy import select
from backend.app.repositories.source_repo import source_repo
from backend.app.services.source_service import SourceExtractionService, source_service

TEXT='알파 본딩은 칩을 연결하는 공정이다.\n## 회사 A 제품 X\n압력은 100 MPa이다.\n## 회사 B 제품 Y\n압력은 80 MPa이다.\n일반 공정의 두께 감소는 20% 이상이다.'
LINES=dict(enumerate(TEXT.splitlines(),1))
DOC=SimpleNamespace(file_path='synthetic-grounding.md')

def case(title,quote,specs):
    return {'perspectiveTitle':title,'perspectiveBadge':title,'narrative':title+'의 알파 본딩 적용','caution':'',
            'evidenceQuote':quote,'evidenceVerified':True,'specifications':specs}

def spec(value,quote,unit='MPa'):
    return {'parameter':'압력' if unit=='MPa' else '두께 감소','value':value,'unit':unit,'safetyMargin':None,
            'evidenceQuote':quote,'evidenceVerified':True,'fieldEvidenceQuotes':{}}

def case_items():
    return [{'conceptId':'alpha','title':'알파 본딩','perspectiveCases':[
        case('회사 A 제품 X',LINES[3],[spec('100',LINES[3]),spec('20 이상',LINES[6],'%')]),
        case('회사 B 제품 Y',LINES[5],[spec('80',LINES[5])]),
        case('없는 회사 Z',LINES[3],[])]}]

def case_decisions():
    return {'decisions':[
        {'caseIndex':0,'supported':True,'scopeMention':'회사 A 제품 X','scopeEvidenceLine':2,'reason':'앞 소제목이 실제 적용 조건을 명시',
         'specifications':[{'specIndex':0,'supported':True,'scopeMention':'제품 X','scopeEvidenceLine':2,'evidenceLine':3,'reason':'제품 X 조건의 실제 압력'},
                           {'specIndex':1,'supported':False,'reason':'일반 기술 수치를 특정 회사로 귀속할 수 없음'}]},
        {'caseIndex':1,'supported':True,'scopeMention':'회사 B 제품 Y','scopeEvidenceLine':4,'reason':'회사 B의 적용 조건',
         'specifications':[{'specIndex':0,'supported':True,'scopeMention':'제품 Y','scopeEvidenceLine':4,'evidenceLine':5,'reason':'별도 제품 Y의 압력'}]},
        {'caseIndex':2,'supported':False,'scopeMention':'없는 회사 Z','scopeEvidenceLine':2,'reason':'원문에 없는 회사 사례','specifications':[]}]}

async def checks():
    from backend.app.services.case_explanation_service import case_explanation_service
    tokenizer=RegimeAwareTokenizer()
    physical='0.33 NA(NXE), 0.55 NA(EXE); 150N, 145N, 180N.'
    protected,_=tokenizer.tokenize(physical,session_id='isolated-na-check')
    assert '0.33 NA' in protected and '0.55 NA' in protected
    assert protected.count('[FORCE_REGIME_LOAD:')==3 and '150N' not in protected
    assert tokenizer.detokenize(protected,session_id='isolated-na-check')==physical
    print('PASS numerical aperture NA stays distinct; real N force units remain protected and restore exactly')
    assert source_service.judgment_examples('extract','비해')==''
    with_examples=SourceExtractionService(use_examples=True)
    assert with_examples.judgment_examples('extract','---\ntitle: alpha\npublisher: beta\n---\n중립 문서')==''
    assert '현재 입력의 지식·근거가 아님' in with_examples.judgment_examples('relations','방식 A에 비해 방식 B가 빠르다.')
    for publisher in ('Samsung','SK hynix','ASML','Lam Research','unknown'):
        assert source_service.build_publisher_prompt(publisher)==source_service.build_publisher_prompt('unknown')
    instruction=source_service.build_publisher_prompt('unknown')
    assert '0.33' not in instruction and '0.55' not in instruction and '포토공정' not in instruction
    book=json.loads((ROOT/'backend/app/services/source_extraction_examples.json').read_text(encoding='utf-8'))
    for example in book['examples']:
        path=(source_repo.sources_dir/example['sourcePath']).resolve()
        assert path.is_relative_to(source_repo.sources_dir)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==example['sourceSha256']
        lines=path.read_text(encoding='utf-8').splitlines()
        assert example['excerpt']=='\n'.join(f'{i}: {lines[n-1]}' for i,n in enumerate(example['sourceLines'],1))

    footer='circle-arrow2circle-arrow2facebookgooglehandshake2plant2searchtwitteryoutube'
    raw='---\ntitle: 288nm\n---\n# 본문\n압력은 100 MPa이다.\n## Related blog posts\n뒤쪽 기술 본문에는 80 MPa가 있다.\n'+footer
    cleaned=source_service.clean_web_noise(raw)
    assert '288nm' not in cleaned and footer not in cleaned
    assert '100 MPa' in cleaned and '뒤쪽 기술 본문에는 80 MPa' in cleaned
    assert source_service.clean_web_noise('기술 문장에 인쇄하기라는 단어가 있다.')=='기술 문장에 인쇄하기라는 단어가 있다.'
    horizontal='---\n실제 본문에는 압력이 100 MPa이다.\n---\n뒤쪽 기술 본문'
    assert '100 MPa' in source_service.clean_web_noise(horizontal)
    for path in ('samsung/samsung_glossary_bandochat_summary.md','samsung/glossary/mwc-2014-돋보기-4-cmos-이미지센서cis-아이소셀isocell.md'):
        article=(source_repo.sources_dir/path).read_text(encoding='utf-8')
        clean=source_service.clean_web_noise(article)
        assert '메뉴 열기' not in clean and clean.startswith('#')
        assert '반도Chat 모아보기' in clean if 'bandochat' in path else '[MWC 2014 돋보기]' in clean
    bad={'perspectiveCases':[case('웹 푸터',footer,[spec('2s',footer,None)])]}
    checked=source_service.validate_quotes(bad,raw)
    assert checked['perspectiveCases'][0]['specifications'][0]['value']=='2s'
    # Source punctuation and paraphrased units must not erase a grounded value.
    for quote,value,unit in [('DUV(ArF 액침, 193nm)', '193','nm'),
            ('- 20~30kW급 레이저', '20~30','kW'), ('시야, 26mm', '26','mm'),
            ('처리량, 150~220wph', '150~220','wph')]:
        got=source_service.validate_quotes({'perspectiveCases':[case('조건',quote,[spec(value,quote,unit)])]},quote)
        assert got['perspectiveCases'][0]['specifications'][0]['value']==value
    missing=source_service.validate_quotes({'perspectiveCases':[case('조건',LINES[3],[spec('100','원문에 없는 인용')])]},TEXT)
    assert missing['perspectiveCases'][0]['specifications'][0]['value']=='100'
    print('PASS citation spelling/location do not discard candidates; punctuation does not erase numbers; web cleaning retained')

    # The semantic review, rather than literal substring matching, rejects invented or dequalified values.
    text='## 대역폭 조건\n대역폭은 2 TB/s 돌파이다.\n서술용 abc2search 문자열'
    values=[{'conceptId':'bandwidth','title':'대역폭','perspectiveCases':[
        case('속도 조건',text.splitlines()[1],[spec('2',text.splitlines()[1],'TB/s'),spec('2 돌파',text.splitlines()[1],'TB/s'),spec('2s',text.splitlines()[2],None)])]}]
    decision={'decisions':[{'caseIndex':0,'supported':True,'scopeEvidenceLine':1,'reason':'같은 대역폭 조건의 표현',
        'specifications':[{'specIndex':0,'supported':False,'reason':'돌파 한정어 손실'},
            {'specIndex':1,'supported':True,'scopeEvidenceLine':1,'evidenceLine':2,'reason':'실제 조건과 한정어 보존'},
            {'specIndex':2,'supported':False,'reason':'문자열 식별자는 실제 수치가 아님'}]}]}
    with patch('backend.app.services.source_service.llm_gateway.generate_text',new=AsyncMock(return_value=json.dumps(decision))) as gateway:
        await source_service.review_perspective_cases(DOC,values,text)
    assert gateway.call_count==1 and [s['value'] for s in values[0]['perspectiveCases'][0]['specifications']]==['2 돌파']

    text='신뢰성은 품질보증의 평가 기준이다.\n공정 A는 장비 B를 사용한다.\n펌프 C는 장비 B의 실제 내부 구성요소이다.\n소자 D는 소자 E의 한 종류이다.'
    names={'reliability':'신뢰성','process-a':'공정 A','pump-c':'펌프 C','device-d':'소자 D'}
    items=[{'conceptId':cid,'title':title,**{f:[] for f in ('previousSteps','nextSteps','alternatives','partOf','isA')}} for cid,title in names.items()]
    for i,field,target,name in [(0,'isA','qa','품질보증'),(1,'partOf','equipment-b','장비 B'),(2,'partOf','equipment-b','장비 B'),(3,'isA','device-e','소자 E')]:
        items[i][field]=[{'id':target,'name':name,'reason':'원문 검토','evidenceQuote':text.splitlines()[i],'evidenceVerified':True}]
    response={'decisions':[{'candidateIndex':0,'supported':False,'reason':'기준은 종류가 아님'},
        {'candidateIndex':1,'supported':False,'reason':'사용은 소속이 아님'},
        {'candidateIndex':2,'supported':True,'ownerId':'pump-c','targetId':'equipment-b','ownerMention':'펌프 C','targetMention':'장비 B','evidenceLine':3},
        {'candidateIndex':3,'supported':True,'ownerId':'device-d','targetId':'device-e','ownerMention':'소자 D','targetMention':'소자 E','evidenceLine':4}]}
    with patch('backend.app.services.source_service.llm_gateway.generate_text',new=AsyncMock(return_value=json.dumps(response))):
        await source_service.review_relation_subjects(DOC,items,text)
    assert not items[0]['isA'] and not items[1]['partOf']
    assert items[2]['partOf'][0]['id']=='equipment-b' and items[3]['isA'][0]['id']=='device-e'
    cross_line=[{'conceptId':'pump-c','title':'펌프 C','partOf':[{'id':'equipment-b','name':'장비 B','reason':'문서 소제목과 설명', 'evidenceQuote':'앞 문단을 요약한 표현','evidenceVerified':True}]}]
    cross_decision={'decisions':[{'candidateIndex':0,'supported':True,'ownerId':'pump-c','targetId':'equipment-b','reason':'장비 소제목 아래 내부 구성요소 설명'}]}
    with patch('backend.app.services.source_service.llm_gateway.generate_text',new=AsyncMock(return_value=json.dumps(cross_decision))) as gateway:
        await source_service.review_relation_subjects(DOC,cross_line,'## 장비 B\n내부에 펌프 C가 설치된다.')
    assert gateway.call_count==1 and cross_line[0]['partOf'][0]['id']=='equipment-b'
    for target in (None,'','   '):
        broken=[{'conceptId':'pump-c','title':'펌프 C','partOf':[{'id':target,'name':'장비 B','evidenceQuote':text.splitlines()[2],'evidenceVerified':True}]}]
        decision={'decisions':[{'candidateIndex':0,'supported':True,'ownerId':'pump-c','targetId':target,'ownerMention':'펌프 C','targetMention':'장비 B','evidenceLine':3}]}
        with patch('backend.app.services.source_service.llm_gateway.generate_text',new=AsyncMock(return_value=json.dumps(decision))):
            await source_service.review_relation_subjects(DOC,broken,text)
        assert not broken[0]['partOf'] and broken[0]['validationWarnings']
    print('PASS evaluation criterion/use not isA/partOf; real kinds/components and unregistered targets retained')

    values=case_items()
    with patch('backend.app.services.source_service.llm_gateway.generate_text',new=AsyncMock(return_value=json.dumps(case_decisions()))):
        await source_service.review_perspective_cases(DOC,values,TEXT)
    cases=values[0]['perspectiveCases']
    assert len(cases)==2 and [c['specifications'][0]['value'] for c in cases]==['100','80']
    assert len(cases[0]['specifications'])==1 and cases[0]['narrative']=='회사 A 제품 X의 알파 본딩 적용'
    assert any('일반 기술 수치' in warning for warning in values[0]['validationWarnings'])
    paraphrased=case_items();paraphrased[0]['perspectiveCases'][0].update(perspectiveTitle='첫 번째 적용 조건',perspectiveBadge='실무',narrative='앞서 소개한 제품의 본딩 압력')
    with patch('backend.app.services.source_service.llm_gateway.generate_text',new=AsyncMock(return_value=json.dumps(case_decisions()))) as gateway:
        await source_service.review_perspective_cases(DOC,paraphrased,TEXT)
    assert gateway.call_count==1 and paraphrased[0]['perspectiveCases'][0]['specifications'][0]['value']=='100'
    no_locations=case_decisions()
    for decision in no_locations['decisions']:
        decision.pop('scopeEvidenceLine',None)
        for review in decision['specifications']:
            review['scopeEvidenceLine']=99999
            review['evidenceLine']=99999
    accepted=case_items()
    with patch('backend.app.services.source_service.llm_gateway.generate_text',new=AsyncMock(return_value=json.dumps(no_locations))) as gateway:
        await source_service.review_perspective_cases(DOC,accepted,TEXT)
    assert gateway.call_count==1 and len(accepted[0]['perspectiveCases'])==2
    for decision in ({'decisions':[]},{'decisions':[case_decisions()['decisions'][0]]}):
        unchanged=case_items();before=copy.deepcopy(unchanged)
        with patch('backend.app.services.source_service.llm_gateway.generate_text',new=AsyncMock(return_value=json.dumps(decision))) as gateway:
            try:await source_service.review_perspective_cases(DOC,unchanged,TEXT)
            except RuntimeError:pass
            else:raise AssertionError('Incomplete reviews must fail')
        assert unchanged==before and gateway.call_count==2
    print('PASS company/spec binding, heading+value context, preserve true narrative, fabricated scope rejected, incomplete reviews cannot partially mutate')

    engine=create_async_engine('sqlite+aiosqlite:///:memory:')
    factory=async_sessionmaker(engine,expire_on_commit=False)
    explanation_factory=case_explanation_service.session_factory
    case_explanation_service.session_factory=factory
    async with engine.begin() as conn:await conn.run_sync(Base.metadata.create_all)
    app=FastAPI()
    for router in (admin_sources.router,concepts.router):app.include_router(router,prefix='/api/v1')
    async def db():
        async with factory() as session:yield session
    level=4
    async def admin():return SimpleNamespace(id='synthetic-check',name='검증 관리자',level=level,is_active=True)
    app.dependency_overrides.update({get_db:db,get_current_active_user:admin,get_current_user_optional:admin})
    original_dir=source_repo.sources_dir
    original_factory=source_service.session_factory
    source_service.session_factory=factory
    try:
        with tempfile.TemporaryDirectory(prefix='source-grounding-') as temporary:
            source_repo.sources_dir=Path(temporary).resolve()
            # More than one real document part must merge the same quote-free concept.
            general_definition='검증용 광학 모델은 빔의 길이와 보정 상수를 설명한다.'
            general_quantities='기준 길이는 407 mm이며 보정 상수의 이론 한계는 0.14, 도달 수준은 0.22에 근접한다.'
            long_text=TEXT+'\n칩 연결을 위해 압력을 조절한다.\n'+general_definition+general_quantities+'\n'+('알파 본딩은 압력을 조절한다.\n'*280)
            file=source_repo.sources_dir/'synthetic.md';file.write_text(long_text,encoding='utf-8')
            part_count=len(source_service.document_parts(source_service.clean_web_noise(long_text)))
            assert part_count>=2
            async with factory() as session:
                session.add(SourceDocumentModel(doc_id='synthetic',file_path=file.name,title='명시된 검증 fixture',publisher='synthetic',file_hash=source_repo.compute_file_hash(file)))
                await session.commit()
            payload={'id':'alpha','title':'알파 본딩','engName':'Alpha bonding','domainFacet':'unit_process','category':'본딩','scaleLevel':3,
                'summary':LINES[1],'summaryEvidenceLine':99999,'purpose':'칩 연결을 위해 압력을 조절한다.','purposeEvidenceLine':99999,
                'perspectiveCases':case_items()[0]['perspectiveCases']}
            extraction_calls=0
            mixed_quotes=False
            async def gateway(**kwargs):
                nonlocal extraction_calls
                assert kwargs['model_override']=='gemini-3.8-flash' and kwargs['preferred_provider']=='gemini' and kwargs['reasoning_effort']=='medium'
                assert kwargs['allow_fallback'] is False and kwargs['tier']=='tier2_reasoning'
                if '사례·수치 귀속 검토' in kwargs['prompt']:return json.dumps(no_locations)
                if '사례·파라미터 검토' in kwargs['prompt']:return '{"concepts":[]}'
                extraction_calls+=1
                value=copy.deepcopy(payload)
                if extraction_calls>1:
                    value['summary']='알파 본딩은 압력을 조절한다.'
                    value['perspectiveCases']=[]
                if mixed_quotes and extraction_calls==1:
                    value.update(summaryEvidenceQuote=LINES[1],purposeEvidenceQuote='칩 연결을 위해 압력을 조절한다.')
                for c in value['perspectiveCases']:
                    c.pop('evidenceQuote',None);c['evidenceLine']=99999
                    for s in c['specifications']:
                        s.pop('evidenceQuote',None);s['evidenceLine']=99999
                general={'id':'general-model','title':'검증용 광학 모델','engName':'Fixture optical model',
                    'domainFacet':'unit_process','category':'검증','scaleLevel':1,
                    'summary':general_definition+(general_quantities if not mixed_quotes else ''),'perspectiveCases':[]}
                return json.dumps({'concepts':[value,general]})
            async with AsyncClient(transport=ASGITransport(app=app),base_url='http://memory') as client:
                level=3
                assert (await client.post('/api/v1/admin/sources/extract',json={'docIds':['synthetic']})).status_code==403
                assert (await client.get('/api/v1/admin/sources/synthetic/preview')).status_code==403
                assert (await client.post('/api/v1/admin/sources/apply',json={'docIds':['synthetic']})).status_code==403
                level=4
                assert (await client.post('/api/v1/admin/sources/extract',json={'docIds':[]})).status_code==400
                assert (await client.post('/api/v1/admin/sources/extract',json={'docIds':'synthetic'})).status_code==422
                assert (await client.get('/api/v1/admin/sources/missing/preview')).status_code==404
                for mixed_quotes in (False,True):
                    extraction_calls=0
                    with patch('backend.app.services.source_service.llm_gateway.generate_text',new=gateway):
                        r=await client.post('/api/v1/admin/sources/extract',json={'docIds':['synthetic'],'forceReextract':True})
                    r.raise_for_status()
                    assert '"totalSucceeded": 1' in r.text,r.text
                    assert extraction_calls==part_count
                    response=await client.get('/api/v1/admin/sources/synthetic/preview');response.raise_for_status()
                    items=response.json()['preview']
                    preview=next(item for item in items if item['conceptId']=='alpha')
                    general=next(item for item in items if item['conceptId']=='general-model')
                    assert general['summary']==general_definition+(general_quantities if not mixed_quotes else '')
                    assert not general['perspectiveCases'] and not general['applyBlockers']
                    assert len(items)==2  # Optional numeric omissions must not discard either useful concept.
                    coverage=preview['sourceCoverage']
                    assert coverage['complete'] and coverage['processedParts']==coverage['totalParts']==part_count
                    assert coverage['processedCharacters']==coverage['totalCharacters']
                    assert preview['summary']==LINES[1]+'\n\n알파 본딩은 압력을 조절한다.'
                    assert preview['purpose']==payload['purpose']
                    for field,quote in [('summary',LINES[1]),('purpose',payload['purpose'])]:
                        assert preview[field+'EvidenceQuotes']==([quote] if mixed_quotes else [])
                    assert len(preview['perspectiveCases'])==2 and len(preview['perspectiveCases'][0]['specifications'])==1
                    assert not preview['applyBlockers']
                    # An invalid document in the batch must prevent all writes.
                    assert (await client.post('/api/v1/admin/sources/apply',json={'docIds':['synthetic','missing']})).status_code==404
                    async with factory() as session:
                        doc=await session.get(SourceDocumentModel,'synthetic')
                        assert not doc.is_applied
                        if not mixed_quotes:assert await session.get(ConceptModel,'alpha') is None
                    if not mixed_quotes:
                        async with factory() as session:
                            doc=await session.get(SourceDocumentModel,'synthetic')
                            saved=copy.deepcopy(doc.last_preview_payload)
                            for guard in ('classificationConflict','sourceCoverage'):
                                changed=copy.deepcopy(saved)
                                if guard=='classificationConflict':changed[0][guard]=True
                                else:changed[0][guard]['complete']=False
                                doc.last_preview_payload=changed
                                await session.commit()
                                assert (await client.post('/api/v1/admin/sources/apply',json={'docIds':['synthetic']})).status_code==409
                            doc.last_preview_payload=saved
                            await session.commit()
                        # Fail after the concept flush to verify the actual write transaction rolls back.
                        with patch.object(source_repo,'save_perspective_cases',new=AsyncMock(side_effect=RuntimeError('fixture write failure'))):
                            async with factory() as session:
                                try:await source_service.apply_extractions_to_wiki(session,['synthetic'])
                                except RuntimeError as error:assert str(error)=='fixture write failure'
                                else:raise AssertionError('Write failure must abort apply')
                        async with factory() as session:
                            assert await session.get(ConceptModel,'alpha') is None
                            assert not (await session.get(SourceDocumentModel,'synthetic')).is_applied
                    r=await client.post('/api/v1/admin/sources/apply',json={'docIds':['synthetic']});r.raise_for_status()
                    detail_response=await client.get('/api/v1/concepts/alpha');detail_response.raise_for_status()
                    detail=detail_response.json()
                    assert detail['summary']==preview['mergedPreview']['summary'] and detail['purpose']==payload['purpose']
                    assert len(detail['perspectives'])==2
                    assert {s['value'] for c in detail['perspectives'] for s in c['specifications']}=={'100','80'}
                    async with factory() as session:
                        quotes=list((await session.scalars(select(EvidenceSourceModel.quote))).all())
                        assert set(quotes)==({LINES[1],payload['purpose']} if mixed_quotes else set())
                    repeat=await client.post('/api/v1/admin/sources/apply',json={'docIds':['synthetic']});repeat.raise_for_status()
                    assert repeat.json()['appliedCount']==0
            print('PASS general quantitative definitions without cases, and useful candidates with optional numeric omissions retained')
            print('PASS quote-free and mixed-citation multi-part extraction -> preview -> apply -> detail; no fabricated citations; permissions/format/batch rollback/idempotency retained')
    finally:
        source_repo.sources_dir=original_dir
        source_service.session_factory=original_factory
        case_explanation_service.session_factory=explanation_factory
        await engine.dispose()

if __name__=='__main__':asyncio.run(checks())
