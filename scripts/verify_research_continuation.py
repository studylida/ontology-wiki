"""Memory-only adaptive research regression; external search/model calls are fixtures."""
import asyncio
from datetime import datetime, timedelta
from io import BytesIO
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from verify_research_discovery import (app, engine, Base, async_session_factory, fixtures,
    fixture_gateway, research_repo, research_discovery_agent, ResearchSessionModel, QUESTION)
import httpx
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from backend.app.services.research_content import html_content, pdf_content
from backend.app.services.research_evidence import assessment_hash, report_signature
from backend.app.services.comparison_service import comparison_service
from backend.app.models.entities import ConceptModel, ComparisonSessionModel, EvidenceSourceModel
from backend.app.schemas.comparison import ResearchEnrichmentRequest, ExportReviewRequest


def pdf_bytes(title):
    writer = PdfWriter()
    page = writer.add_blank_page(width=600, height=800)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
    stream = DecodedStreamObject()
    text = title + '. ' + 'Particles and copper planarity cause non-bonded regions in hybrid bonding. ' * 5
    stream.set_data(('BT /F1 10 Tf 30 700 Td (' + text + ') Tj ET').encode())
    page[NameObject('/Contents')] = writer._add_object(stream)
    output = BytesIO(); writer.write(output)
    return output.getvalue()


async def checks():
    title, doi = 'Hybrid bonding particle yield defects', 'https://doi.org/10.fixture/particles'
    page = ('<meta name="citation_title" content="' + title + '"><meta name="citation_pdf_url" content="javascript:alert(1)">'
        '<meta name="citation_pdf_url" content="/paper.pdf"><p>' + 'Copper planarity and particles affect hybrid bonding yield. ' * 8 + '</p>').encode()
    text, links = html_content(page, 'https://example.org/article', title, doi)
    assert len(text) > 200 and links == ['https://example.org/paper.pdf']
    wrong = b'<title>Unrelated polymer adhesive study</title><p>' + b'Unrelated polymer mechanics. ' * 15 + doi.encode() + b'</p>'
    try:
        html_content(wrong, 'https://example.org/article', title, doi)
        raise AssertionError('Reference-only DOI must not identify a document')
    except ValueError as exc:
        assert str(exc) == 'document_identity_unverified'
    assert title in await pdf_content(pdf_bytes(title), title, doi)
    try:
        await pdf_content(pdf_bytes('Unrelated polymer adhesive study'), title, doi)
        raise AssertionError('Wrong PDF title must be rejected')
    except ValueError as exc:
        assert str(exc) == 'document_identity_unverified'
    with patch('asyncio.BaseEventLoop.getaddrinfo', new=AsyncMock(return_value=[(2, 1, 6, '', ('127.0.0.1', 443))])):
        try:
            await research_repo.fetch_public('https://example.org/paper')
            raise AssertionError('Private DNS address must be rejected')
        except ValueError as exc:
            assert str(exc) == 'unsafe_public_address'
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async def records(query):
        return [dict(title=[f'{title} {query} {i}'], DOI=f'10.fixture/{query}-{i}', publisher='fixture',
            abstract='Particles on die surfaces cause local non-bonded areas in hybrid bonding.') for i in range(8)]
    assessed = []
    async def gateway(**kwargs):
        payload = json.loads(kwargs['prompt'])
        if 'evidence' in payload and 'plan' in payload:
            assessed.extend(e['id'] for e in payload['evidence'])
        result = json.loads(await fixture_gateway(**kwargs))
        if 'evidence' in payload and 'plan' in payload:
            result['followUpQueries'] = [f'query{i}' for i in range(4, 7)]
        return json.dumps(result)
    from backend.app.core.llm_gateway import llm_gateway
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://fixture') as client:
        with fixtures(), patch.object(research_repo, 'crossref', new=records), patch.object(llm_gateway, 'generate_text', new=gateway):
            plan = dict(originalQuestion=QUESTION, interpretedQuestion=QUESTION, searchQueries=[f'query{i}' for i in range(4)], status='ready')
            first_response = await client.post('/api/v1/research/discover', json=dict(searchTopic=QUESTION, searchPlan=plan))
            assert first_response.status_code == 200, first_response.text
            first = first_response.json(); sid = first['sessionId']; path = f'/api/v1/research/sessions/{sid}'
            assert len(first['evidenceFeed']) == 32 and first['discoveryContext']['canContinue']
            first_ids = {e['id'] for e in first['evidenceFeed']}; assessed.clear()
            second_response = await client.post(path + '/continue', json=dict(expectedUpdatedAt=first['updatedAt']))
            assert second_response.status_code == 200, second_response.text
            second = second_response.json()
            assert second['sessionId'] == sid and len(second['evidenceFeed']) == 56
            assert not first_ids.intersection(assessed), 'Unchanged assessments must be reused'
            assert first_ids <= {e['id'] for e in second['evidenceFeed']}
            assert (await client.post(path + '/continue', json=dict(expectedUpdatedAt=first['updatedAt']))).status_code == 409
            chosen = second['evidenceFeed'][0]['id']
            synthesized = await client.post(path + '/synthesize', json=dict(selectedEvidenceIds=[chosen]))
            assert synthesized.status_code == 200, synthesized.text
            async with async_session_factory() as db:
                db.add(ConceptModel(id='adaptive-concept', title='격리 본딩', eng_name='Fixture Bonding', domain_facet='unit_process', process_category='본딩', scale_level=3, summary='격리 정의', purpose='검증'))
                db.add(ComparisonSessionModel(id='adaptive-comparison', user_id='fixture', title='격리 비교', query=QUESTION,
                    context_params=dict(targetA='adaptive-concept', targetB='adaptive-concept'), snapshots=[{}, {}, {'deepDiveHistory': []}]))
                original = EvidenceSourceModel(id='adaptive-long', source_name='Long registered study', source_type='academic_peer_reviewed', publisher='fixture',
                    quote='Particles cause hybrid bonding defects. ' * 250, external_url='https://example.org/long', url_label='원문', credibility_tier='공개', referenced_concepts=[])
                db.add(original)
                session = await db.get(ResearchSessionModel, sid)
                long_item = {**second['evidenceFeed'][0], 'id': original.id, 'sourceName': original.source_name, 'quote': original.quote, 'externalUrl': original.external_url, 'retrievalStatus': 'registered_excerpt'}
                session.evidence_feed = session.evidence_feed + [long_item]
                session.synthesis_report = {**session.synthesis_report, 'comparisonContext': {'comparisonSessionId': 'adaptive-comparison'}}
                await db.commit()
                with patch.object(comparison_service, 'refresh', new=AsyncMock()), patch.object(comparison_service, 'dto', return_value={}):
                    await comparison_service.enrich(db, 'adaptive-comparison', ResearchEnrichmentRequest(researchSessionId=sid, selectedEvidenceIds=[chosen, original.id]))
                comparison = await db.get(ComparisonSessionModel, 'adaptive-comparison')
                assert next(e['quote'] for e in comparison.context_params['researchEvidence'] if e['id'] == original.id) == original.quote
                ticket = await comparison_service.export(db, 'adaptive-comparison', ExportReviewRequest(conceptId='adaptive-concept', title='격리 검토', reviewType='enrichment', overrideReason='원문 보존 검증'),
                    SimpleNamespace(level=2, name='격리 검증', department='QA'))
                assert ticket['ticketId']
            async with async_session_factory() as db:
                session = await db.get(ResearchSessionModel, sid)
                session.synthesis_report = {**session.synthesis_report, 'researchRunningUntil': (datetime.utcnow() + timedelta(seconds=30)).isoformat()}
                await db.commit(); await db.refresh(session); stamp = session.updated_at.isoformat()
            assert (await client.post(path + '/continue', json=dict(expectedUpdatedAt=stamp))).status_code == 409
            assert (await client.post(path + '/synthesize', json=dict(selectedEvidenceIds=[chosen]))).status_code == 409
            e = second['evidenceFeed'][0]
            before = assessment_hash(e, QUESTION)
            e['assessmentInputHash'] = before
            signature = report_signature([e], [e['id']])
            e['readSegments'].append(dict(id='new', text='New measured particle failure data.'))
            assert before != assessment_hash(e, QUESTION)
            e['assessmentCurrent'] = False
            assert signature != report_signature([e], [e['id']])
        with fixtures(), patch.object(research_discovery_agent, 'plan', new=AsyncMock(return_value=None)):
            failed = (await client.post('/api/v1/research/discover', json=dict(searchTopic=QUESTION))).json()
            assert failed['discoveryContext']['generationStatus'] == 'source_only'
        with fixtures():
            recovered_response = await client.post(f"/api/v1/research/sessions/{failed['sessionId']}/continue", json=dict(expectedUpdatedAt=failed['updatedAt']))
            assert recovered_response.status_code == 200, recovered_response.text
            recovered = recovered_response.json()
            assert recovered['discoveryContext']['plan']['status'] == 'ready'
            assert any(e['assessmentCurrent'] and e['assessment']['decision'] == 'included' for e in recovered['evidenceFeed'])
        with fixtures(), patch.object(research_repo, 'crossref', new=AsyncMock(side_effect=ValueError('crossref_rate_limited'))):
            limited = (await client.post('/api/v1/research/discover', json=dict(searchTopic=QUESTION, searchPlan=plan))).json()
            assert limited['discoveryContext']['canContinue'] and limited['discoveryContext']['pendingQueries']
            assert not limited['discoveryContext']['queriesExecuted']
    await engine.dispose()
    print('PASS continuation beyond 30, unchanged reuse, stale version/leases, source-only recovery, retry checkpoint, HTML/PDF identity and unsafe URLs')


if __name__ == '__main__':
    asyncio.run(checks())
