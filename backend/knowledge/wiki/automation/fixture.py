"""Explicit deterministic wiring fixture; NOT concept discovery or quality evaluation."""
def fixture_plan(data):
    source = data['source']
    matching = [c for c in data['candidates'] if source['title'].casefold() in
                [c['title'].casefold(), *[a.casefold() for a in c['aliases']]]]
    target = matching[0] if len(matching) == 1 else None
    return {'reason': 'fixture 연결 검증용 보강 기회입니다. 실제 의미 판단이 아닙니다.',
            'ideas': [{'mode': 'edit' if target else 'create', 'pageId': target['pageId'] if target else None,
                'title': target['title'] if target else source['title'][:300],
                'instruction': '제공된 문헌의 적용 조건을 최소 변경으로 보강하세요.',
                'evidenceIds': [source['passages'][0]['passageId']]}]}
