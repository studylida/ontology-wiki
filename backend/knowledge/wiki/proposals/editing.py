"""Bounded, non-overlapping minimal edits. This does NOT certify semantic truth."""
from collections import Counter
import difflib
import re
from ...core.errors import AppError
from .dto import GeneratedProposal


def invalid(message):
    raise AppError(422, 'proposal_invalid', message)


def materialize(base, generated: GeneratedProposal, mode, candidates, evidence):
    allowed_evidence = {item['passageId']: item for item in evidence}
    used = set(generated.evidence_ids)
    if mode == 'create':
        if generated.patches or not generated.title.strip() or not generated.markdown.strip():
            invalid('새 초안에 제목과 본문이 필요합니다.')
        title, markdown = generated.title.strip(), generated.markdown
    else:
        title, markdown = base['title'], base['markdown']
        if generated.markdown or (generated.title and generated.title != title):
            invalid('기존 문서는 전체 재작성 대신 부분 변경을 제안해야 합니다.')
        if mode == 'links' and generated.patches:
            invalid('링크 요청에서는 문장을 변경할 수 없습니다.')
        edits = []
        for patch in generated.patches:
            if markdown.count(patch.old) != 1:
                invalid('수정 위치가 불명확합니다. 변경 범위를 줄여 다시 요청해 주세요.')
            start = markdown.index(patch.old)
            edits.append((start, start + len(patch.old), patch.new))
            used.update(patch.evidence_ids)
        edits.sort()
        if any(a[1] > b[0] for a, b in zip(edits, edits[1:])):
            invalid('겹치는 수정안은 자동 적용하지 않습니다.')
        if len(markdown) > 800 and sum(end-start for start, end, _ in edits) > len(markdown) * .45:
            invalid('본문의 너무 큰 부분을 다시 쓰는 제안입니다. 수정 요청을 좁혀 주세요.')
        for start, end, value in reversed(edits):
            markdown = markdown[:start] + value + markdown[end:]
    if not used <= allowed_evidence.keys():
        invalid('실제 전달한 근거에 없는 출처가 포함되어 있습니다.')
    # New links must use the separate candidate/identity/readability decision path.
    link_pattern = r'!?\[[^\]\n]*\]\([^\n)]*\)|<https?://[^>]+>'
    if Counter(re.findall(link_pattern, markdown)) - Counter(re.findall(link_pattern, base.get('markdown', ''))):
        invalid('본문에 직접 추가한 링크 대신 검토 가능한 링크 제안 목록을 사용해야 합니다.')
    # Link decisions are model-reviewed and then conservatively checked mechanically.
    accepted, warnings = [], []
    for link in generated.links:
        target = candidates.get(link.page_id)
        if not target or not link.same_concept or not link.important:
            continue
        if any(item['pageId'] == link.page_id for item in accepted):
            continue
        anchor = link.anchor
        if any(c in anchor for c in '[]()<>`\n\r') or markdown.count(anchor) != 1:
            warnings.append('중복되거나 모호한 표현의 링크는 생략했습니다.'); continue
        start = markdown.index(anchor); end = start + len(anchor)
        if ((start and markdown[start-1].isalnum()) or (end < len(markdown) and markdown[end].isalnum())):
            continue
        line = markdown[markdown.rfind('\n', 0, start)+1:markdown.find('\n', end) if '\n' in markdown[end:] else len(markdown)]
        before = markdown[:start]
        if any(c in line for c in '[]`<>') or before.count('```') % 2 or before.count('~~~') % 2:
            warnings.append('코드·기존 링크와 겹칠 수 있는 연결은 생략했습니다.'); continue
        markdown = markdown[:start] + f'[{anchor}](/wiki/{link.page_id})' + markdown[end:]
        accepted.append({'anchor': anchor, 'pageId': link.page_id, 'revisionId': target['revisionId'], 'reason': link.reason})
    if not markdown.strip():
        invalid('빈 본문은 제안할 수 없습니다.')
    diff = '\n'.join(difflib.unified_diff(base.get('markdown', '').splitlines(), markdown.splitlines(),
                                         fromfile='현재 본문', tofile='제안 본문', lineterm=''))
    return {'title': title, 'markdown': markdown, 'reason': generated.reason, 'diff': diff,
            'patches': [patch.public() for patch in generated.patches], 'links': accepted,
            'evidence': [allowed_evidence[key] for key in sorted(used)], 'warnings': warnings}
