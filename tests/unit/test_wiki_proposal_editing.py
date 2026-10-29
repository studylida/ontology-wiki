import pytest
from knowledge.core.errors import AppError
from knowledge.wiki.proposals.dto import GeneratedProposal, ProposalRequest
from knowledge.wiki.proposals.editing import materialize


def generate(**values):
    return GeneratedProposal(reason='부분 수정', **values)


def test_local_edit_keeps_untouched_whitespace_and_only_selected_links():
    text = '# RUL\r\n\r\n기존  설명입니다.  \r\n예지보전 분야에서 상태 모니터링을 활용합니다.\r\n'
    g = generate(patches=[{'old':'기존  설명입니다.', 'new':'기존  설명입니다. 적용 조건을 확인합니다.', 'reason':'조건 보강'}],
        links=[{'anchor':'예지보전', 'pageId':'p1','sameConcept':True,'important':True,'reason':'분야 개념'},
               {'anchor':'상태 모니터링','pageId':'p2','sameConcept':False,'important':True,'reason':'다른 뜻'}])
    result = materialize({'title':'RUL','markdown':text},g,'edit',{'p1':{'revisionId':'r1'},'p2':{'revisionId':'r2'}},[])
    expected = text.replace('기존  설명입니다.','기존  설명입니다. 적용 조건을 확인합니다.').replace('예지보전','[예지보전](/wiki/p1)')
    assert result['markdown'] == expected
    assert len(result['links']) == 1


def test_ambiguous_names_code_existing_links_and_repetitions_are_omitted():
    for text in ('CMP and CMP', '`CMP` expression', '[CMP](/wiki/existing)', '```text\nCMP\n```', 'CMProcessor'):
        g=generate(links=[{'anchor':'CMP','pageId':'p','sameConcept':True,'important':True,'reason':'candidate'}])
        result=materialize({'title':'test','markdown':text},g,'links',{'p':{'revisionId':'r'}},[])
        assert result['markdown'] == text
        assert result['links'] == []


def test_unknown_evidence_overlaps_and_full_rewrite_are_rejected():
    base={'title':'test','markdown':'Alpha beta gamma.'}
    with pytest.raises(AppError): materialize(base,generate(evidenceIds=['invented']), 'edit',{},[])
    with pytest.raises(AppError): materialize(base,generate(markdown='whole rewrite'), 'edit',{},[])
    with pytest.raises(AppError): materialize(base,generate(patches=[
        {'old':'Alpha beta','new':'x','reason':'x'}, {'old':'beta gamma','new':'y','reason':'y'}]),'edit',{},[])
    with pytest.raises(AppError): materialize(base,generate(patches=[{'old':'Alpha','new':'A','reason':'x'}]),'links',{},[])


def test_injection_cannot_add_publish_or_role_fields():
    from pydantic import ValidationError
    with pytest.raises(ValidationError): GeneratedProposal.model_validate({'reason':'x','publish':True})
    with pytest.raises(ValidationError): ProposalRequest(requestId='test-1234',mode='edit',instruction='x')
    with pytest.raises(ValidationError): ProposalRequest(requestId='test-1234',mode='create',pageId='p',instruction='x')


def test_generated_prose_cannot_bypass_candidate_link_review():
    with pytest.raises(AppError):
        materialize({},generate(title='x',markdown='[x](/wiki/unverified)'), 'create',{},[])
