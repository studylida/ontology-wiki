"""Preserved structure checks and converter routing; not a live Docling evaluation."""
import asyncio
import pytest
from knowledge.core.errors import AppError
from knowledge.documents.parsing import prepared_passages
from knowledge.documents.preprocessing import sha
from knowledge.documents.runtime_preprocessing import prepare_conversion
from knowledge.integrations import document_parser
from knowledge.integrations.bounded_process import BoundedProcessError


def converted_fixture(raw, damaged=True):
    table = '| Chip | Current (mA) |\n| 0 283.8 240.9 |\n| 1 254.5 250.6 |' if damaged else '| Chip | Current (mA) |\n| 0 | 283.8 |\n| 1 | 254.5 |'
    content = table + '\n\nExperiment: 250 C for 30 min.'
    offset = content.index('Experiment:')
    records = [dict(text=table,locator='페이지 20 · 표',start_offset=0,end_offset=len(table),embedding_text=table),
               dict(text=content[offset:],locator='페이지 20 · 본문',start_offset=offset,end_offset=len(content),embedding_text=content[offset:])]
    sources = [dict(startOffset=r['start_offset'],endOffset=r['end_offset'],locator=r['locator'],
                    documentRefs=['#/tables/0'] if i == 0 else ['#/texts/1'],
                    label='table' if i == 0 else 'text',pageNumbers=[20],provenance=[]) for i,r in enumerate(records)]
    cells = ['0 283.8 240.9','1 254.5 250.6'] if damaged else ['283.8','254.5']
    return {'title':'Experiment','content':content,'readScope':'full','limitations':[],
        'metadata':{'sourceSha256':sha(raw),'parserProfile':{'version':'2.143.0'}},
        'structuredDocument':{'texts':[{'self_ref':'#/texts/0','text':'Table 1: Current at 250 C (mA)'}],
            'tables':[{'self_ref':'#/tables/0','prov':[{'page_no':20}],'captions':[{'$ref':'#/texts/0'}],
                       'data':{'table_cells':[{'text':v,'start_row_offset_idx':i} for i,v in enumerate(cells)]}}]},
        'sourceMap':sources,'preparedPassages':records}


@pytest.mark.parametrize('damaged',[True,False])
def test_preserved_table_gate_keeps_clean_context_and_exact_offsets(damaged):
    raw = b'explicit synthetic conversion fixture'
    result = prepare_conversion(converted_fixture(raw,damaged),raw)
    passages = prepared_passages(result['content'],result['preparedPassages'])
    assert passages[0].excluded is damaged and not passages[1].excluded
    assert 'Table 1: Current at 250 C (mA)' in passages[0].text
    assert all(result['content'][p.start_offset:p.end_offset] == p.text for p in passages)
    assert all(source['pageNumbers'] == [20] for source in result['sourceMap'])


def test_conversion_does_not_accept_different_original():
    with pytest.raises(ValueError,match='source hash mismatch'):
        prepare_conversion(converted_fixture(b'original'),b'different')


def test_jats_doctype_routes_to_existing_offline_converter_without_credentials(tmp_path,monkeypatch):
    models = tmp_path/'models'
    models.mkdir()
    (models/'fixture').write_bytes(b'not actual model weights')
    seen = {}
    async def fake_converter(executable,module,args,**kwargs):
        seen.update(executable=executable,module=module,args=args,**kwargs)
        raise BoundedProcessError('explicit_test_boundary')
    monkeypatch.setattr(document_parser,'run_bounded_python',fake_converter)
    monkeypatch.setenv('OPENAI_API_KEY','must-not-enter-parser')
    raw = b'<!DOCTYPE article SYSTEM "https://example.invalid/jats.dtd"><article><body><p>test</p></body></article>'
    with pytest.raises(AppError) as failure:
        asyncio.run(document_parser.parse_file(raw,'application/xml',parser='docling',
                    python_executable='fixture-python',artifacts_path=str(models)))
    assert failure.value.code == 'source_parse_failed'
    assert seen['module'] == 'knowledge.integrations.docling_jats'
    assert seen['input_bytes'] == raw
    assert 'OPENAI_API_KEY' not in seen['env'] and seen['env']['HF_HUB_OFFLINE'] == '1'


def test_jats_entity_declaration_is_not_executed(monkeypatch):
    async def forbidden(*args,**kwargs):
        raise AssertionError('An unsafe entity must not start a converter')
    monkeypatch.setattr(document_parser,'run_bounded_python',forbidden)
    raw = b'<!DOCTYPE article [<!ENTITY x SYSTEM "file:///secret">]><article>&x;</article>'
    with pytest.raises(AppError) as failure:
        asyncio.run(document_parser.parse_file(raw,'application/xml',parser='docling',
                    python_executable='fixture-python',artifacts_path='/unused'))
    assert failure.value.code == 'unsafe_xml'
