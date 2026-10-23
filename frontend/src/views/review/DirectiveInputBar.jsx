import React, { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';
export function DirectiveInputBar({
  integrityReport,
  canUndo = false,
  directiveHistory = [],
  isActionLoading,
  isEditorDisabled,
  onApplyDirective,
  onUndoDirective
}) {
  const [scope, setScope] = useState('all');
  const [directiveText, setDirectiveText] = useState('');
  const [overrideReason, setOverrideReason] = useState('');
  const handleSubmit = async event => {
    event.preventDefault();
    if (!directiveText.trim() || isActionLoading) return;
    if (await onApplyDirective(directiveText.trim(), overrideReason.trim(), false, scope)) {
      setDirectiveText('');
      setOverrideReason('');
    }
  };
  const style = {
    padding: '10px',
    border: '1px solid var(--border-color)',
    borderRadius: '8px',
    background: 'var(--bg-surface)',
    color: 'var(--text-primary)'
  };
  return <div style={{
    ...style,
    padding: '16px 20px',
    marginBottom: '16px'
  }}>
    <p style={{
      margin: '0 0 10px',
      fontSize: '0.8rem',
      color: 'var(--text-muted)'
    }}>등록 자료의 관련 원문·발췌로 보강합니다. ‘근거 부족’은 이번 제안에서 근거를 확인하지 못했다는 뜻이며, 전체 자료에 없다는 판정은 아닙니다. 승인 전에는 위키를 변경하지 않습니다.</p>
    {integrityReport?.validationDetails && <p role="status" style={{
      fontSize: '0.8rem'
    }}>{integrityReport.validationDetails}</p>}
    {!!integrityReport?.warnings?.length && <details><summary>확인이 필요한 내용 ({integrityReport.warnings.length})</summary><ul>{integrityReport.warnings.map((warning, index) => <li key={index}>{warning}</li>)}</ul></details>}
    {!!integrityReport?.sources?.length && <details><summary>사용한 자료 ({integrityReport.sources.length})</summary><ul>{integrityReport.sources.map(source => <li key={source.id}>{source.sourceName}{/^https?:\/\//.test(source.externalUrl || '') && <> · <a href={source.externalUrl} target="_blank" rel="noreferrer">원문 출처</a></>}</li>)}</ul></details>}
    <form onSubmit={handleSubmit} style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
      marginTop: '12px'
    }}>
      <label htmlFor="review-directive" style={{
        display: 'flex',
        gap: '6px',
        alignItems: 'center'
      }}><Sparkles size={16} />자료 기반 AI 보강 지시</label>
      <div style={{
        display: 'flex',
        gap: '8px'
      }}>
        <select aria-label="보강 범위" value={scope} disabled={isActionLoading || isEditorDisabled} onChange={e=>setScope(e.target.value)}><option value="all">전체 목차</option><option value="current">현재 목차</option></select><input id="review-directive" value={directiveText} onChange={event => setDirectiveText(event.target.value)} disabled={isEditorDisabled || isActionLoading} placeholder="예: 등록된 자료로 이 개념의 부족한 원리·한계·사례·관계를 보강해줘" style={{
          ...style,
          flex: 1
        }} />
        <button type="submit" disabled={!directiveText.trim() || isEditorDisabled || isActionLoading} style={style}><Send size={14} />{isActionLoading ? '처리 중…' : '초안 보강'}</button>
      </div>
      <details><summary>정정 사유 입력 (선택)</summary><input aria-label="정정 사유" value={overrideReason} onChange={event => setOverrideReason(event.target.value)} disabled={isEditorDisabled || isActionLoading} style={{
          ...style,
          width: '100%'
        }} /></details>
    </form>
    {!!directiveHistory.length && <details style={{
      marginTop: '12px'
    }}><summary>지시 이력 ({directiveHistory.length})</summary><ol>{directiveHistory.map((entry, index) => <li key={index}>{entry.directiveText} · {entry.timestamp}</li>)}</ol>
      {canUndo && <button type="button" onClick={onUndoDirective} disabled={isActionLoading || isEditorDisabled} style={style}>이번 지시 되돌리기</button>}
    </details>}
  </div>;
}
