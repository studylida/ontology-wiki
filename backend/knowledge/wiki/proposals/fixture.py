"""Contract-only output. Not a live editor or semantic link classifier."""
def fixture_proposal(data):
    base, mode = data['base'], data['mode']
    extra = data.get('employeeText') or data['instruction']
    result = {'title': base.get('title', '검증용 위키 초안'), 'markdown': '',
        'reason': '검증용 fixture입니다. 의미 검증이나 사실 확인을 수행하지 않았습니다.',
        'patches': [], 'links': [], 'evidenceIds': []}
    if mode == 'create':
        result['markdown'] = '# 검증용 초안\n\n직원이 반영을 요청한 내용:\n\n' + extra
    elif mode == 'edit':
        old = base['markdown'].splitlines()[-1] if base['markdown'].splitlines() else base['markdown']
        if not old or base['markdown'].count(old) != 1:
            return result
        result['patches'] = [{'old': old, 'new': old + '\n\n직원 입력 (fixture 정리): ' + extra,
                               'reason': '명시적으로 제공한 입력만 덧붙이는 계약 검사', 'evidenceIds': []}]
    return result
