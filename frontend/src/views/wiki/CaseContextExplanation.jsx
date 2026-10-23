import React from 'react';

export function CaseContextExplanation({perspective, isPreview = false, canGenerate = false, request = {}, onGenerate}) {
  const state = perspective.contextExplanationState || 'missing';
  if (state === 'restricted') return null;
  const content = state === 'ready' ? perspective.contextExplanation?.content : null;
  const busy = request.loading || state === 'generating';
  return <section aria-label="쉽게 이해하기" aria-busy={busy} style={{marginTop: '16px', padding: '16px', border: '1px solid var(--border-color)', borderRadius: '8px', background: 'var(--bg-surface)', overflowWrap: 'anywhere'}}>
    <h4 style={{margin: '0 0 10px', color: 'var(--accent-primary)'}}>쉽게 이해하기 · AI 해설</h4>
    {content?.explanation ? <>
      <p style={{whiteSpace: 'pre-wrap', lineHeight: 1.8, margin: 0}}>{content.explanation}</p>
      {content.background && <div style={{marginTop: '12px'}}><strong>용어·배경 설명</strong><p style={{whiteSpace: 'pre-wrap', lineHeight: 1.7, margin: '6px 0 0', color: 'var(--text-secondary)'}}>{content.background}</p></div>}
    </> : <p role="status" style={{margin: 0, color: 'var(--text-secondary)', lineHeight: 1.6}}>
      {isPreview ? '적용 후 해설이 생성됩니다.' : busy ? '이 사례의 쉬운 해설을 준비하고 있습니다.' : state === 'stale' ? '사례 내용이 바뀌어 쉬운 해설을 갱신해야 합니다.' : '이 사례의 쉬운 해설은 아직 준비되지 않았습니다.'}
    </p>}
    {request.error && <p role="alert" style={{color: 'var(--accent-danger)', marginBottom: 0}}>{request.error}</p>}
    {!isPreview && canGenerate && !content?.explanation && <button type="button" disabled={busy} onClick={onGenerate} style={{marginTop: '12px', padding: '7px 12px', borderRadius: '6px', border: '1px solid var(--accent-primary)', background: 'var(--accent-primary-light)', color: 'var(--accent-primary)', cursor: busy ? 'wait' : 'pointer'}}>
      {busy ? '해설 준비 중' : request.error ? '해설 다시 시도' : state === 'stale' ? '해설 갱신' : '쉬운 해설 준비'}
    </button>}
  </section>;
}
