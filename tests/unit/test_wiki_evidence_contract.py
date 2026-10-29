from knowledge.answers.citations import CitationNormalizer
from knowledge.answers.prompt import SYSTEM_POLICY, build_messages
from knowledge.rag.context import select_context, serialized_evidence
from knowledge.evidence.access import partition


def test_wiki_is_not_a_fake_original_or_independent_confirmation():
    hit = {'sourceKind': 'wiki', 'pageId': 'wpg_sample', 'sourceRevisionId': 'wrv_sample', 'passageId': 'wpsg_sample',
        'revisionNumber': 3, 'title': '조건', 'text': '직원의 경험', 'locator': '업무 사례', 'sourceNote': '회의 중 들은 이야기'}
    evidence = select_context([hit], 2000)
    normalizer = CitationNormalizer(evidence)
    text, citations = normalizer.feed('근거 [[C1]] 와 없는 근거 [[C9]]', final=True)
    assert len(citations) == 1 and citations[0]['pageId'] == 'wpg_sample'
    assert citations[0]['sourceRevisionId'] == 'wrv_sample' and 'documentId' not in citations[0]
    assert '[[wpsg_sample]]' in text and '출처 확인 불가' in text
    messages = build_messages('질문', [], evidence, 64000)
    assert 'sourceKind' in messages[1]['content'] and '회의 중 들은 이야기' in messages[1]['content']
    assert '독립적인 검증 두 건으로 세거나' in SYSTEM_POLICY
    assert '검증된 문헌 인용이 아닙니다' in SYSTEM_POLICY
    assert len(serialized_evidence(evidence)) <= 2000


def test_bounded_context_drops_whole_evidence_and_never_invents_identifiers():
    hit = {'sourceKind': 'wiki', 'pageId': 'wpg_page', 'sourceRevisionId': 'wrv_page', 'passageId': 'wpsg_p',
           'text': 'x'*4000, 'sourceNote': 'n'*5000}
    assert select_context([hit], 3000) == []
    docs, wiki = partition(['rev_doc', 'wrv_page', 'unknown'])
    assert docs == {'rev_doc', 'unknown'} and wiki == {'wrv_page'}
