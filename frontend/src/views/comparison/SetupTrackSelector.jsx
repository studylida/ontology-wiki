import React from 'react';
import {ConceptSearch} from './ConceptSearch';

export function SetupTrackSelector({trackMode, query, isClarifying, clarifyResult, targetA, targetB, domain,
  concepts = [], isStartingComparison, onSelectTrackMode, onQueryChange, onClarifyQuery,
  onTargetAChange, onTargetBChange, onDomainChange, onStartDirectComparison,
  axisCandidates = [], selectedAxes = [], customAxisText = '', onCustomAxisTextChange, onToggleAxis,
  answers = {}, onAnswerChange, onConfirmTargets, draft = {}, onDraftFieldChange, onApplyDraft, onResearch}) {
  const busy = isClarifying || isStartingComparison;
  const draftFields = <>
    <div className="comparison-targets">
      <label>대상 A 초안<input aria-label="대상 A 초안" value={draft.targetAName || ''} disabled={busy} onChange={event => onDraftFieldChange('targetAName', event.target.value)}/></label>
      <label>대상 B 초안<input aria-label="대상 B 초안" value={draft.targetBName || ''} disabled={busy} onChange={event => onDraftFieldChange('targetBName', event.target.value)}/></label>
    </div>
    <label>비교 목적<textarea aria-label="비교 목적" rows={2} value={draft.purpose || ''} disabled={busy} onChange={event => onDraftFieldChange('purpose', event.target.value)}/></label>
    <label>적용 맥락<input aria-label="적용 맥락" value={domain} disabled={busy} onChange={event => onDomainChange(event.target.value)} placeholder="적용할 제품·공정 (알고 있는 경우)"/></label>
    <div className="comparison-axis-editor">
      <strong>추천 비교 축</strong><p>목적에 맞는 항목을 확인·수정하세요. 추천 초안은 성능이나 근거의 검증 결과가 아닙니다.</p>
      <div className="comparison-axis-options">{axisCandidates.map(axis => <label key={axis.label}>
        <input type="checkbox" checked={selectedAxes.some(a => a.label === axis.label)} disabled={busy} onChange={() => onToggleAxis(axis)}/>{axis.label}
      </label>)}</div>
      <label>비교 축 직접 입력<input aria-label="비교 축 직접 입력" value={customAxisText} disabled={busy} onChange={event => onCustomAxisTextChange(event.target.value)} placeholder="쉼표로 구분해서 입력"/></label>
    </div>
    <div className="comparison-targets">
      <ConceptSearch label="대상 A 위키 연결" value={targetA} concepts={concepts} onChange={onTargetAChange} excludeId={targetB} disabled={busy}/>
      <ConceptSearch label="대상 B 위키 연결" value={targetB} concepts={concepts} onChange={onTargetBChange} excludeId={targetA} disabled={busy}/>
    </div>
    {(!targetA || !targetB) && <p className="comparison-message">위키 미연결 대상도 초안에 유지합니다. 위키 근거로 비교를 실행하려면 두 대상을 연결하고, 아직 자료가 없는 대상은 이 초안으로 문헌 조사를 시작할 수 있습니다.</p>}
  </>;
  const questions = <>{(clarifyResult?.clarificationQuestions || []).map(item => <div key={item.questionId}>
    <label htmlFor={`clarification-${item.questionId}`}>{item.question}</label>
    <input id={`clarification-${item.questionId}`} value={answers[item.questionId] || ''} disabled={busy} onChange={event => onAnswerChange(item.questionId, event.target.value)}/>
    <div>{item.options.map(option => <button key={option} type="button" disabled={busy} onClick={() => onAnswerChange(item.questionId, option)}>{option}</button>)}</div>
  </div>)}</>;
  return <section className="comparison-setup" aria-label="기술 비교 설정">
    <div><h2>기술 비교의 대상과 목적</h2><p>에이전트가 질문을 분석해 비교 초안을 추천합니다. 위키 등록 여부와 관계없이 초안을 보완할 수 있습니다.</p></div>
    <div className="sliding-tabs-container">
      <button className={`sliding-tab-item ${trackMode === 'track1' ? 'active' : ''}`} type="button" disabled={busy} onClick={() => onSelectTrackMode('track1')}>Track 1: 자연어 질의 구체화</button>
      <button className={`sliding-tab-item ${trackMode === 'track2' ? 'active' : ''}`} type="button" disabled={busy} onClick={() => onSelectTrackMode('track2')}>Track 2: 대상 A/B 직접 지정</button>
    </div>
    {trackMode === 'track1' ? <>
      <form onSubmit={event => {event.preventDefault(); onClarifyQuery(query);}}>
        <label htmlFor="comparison-query">비교할 기술과 달성할 목적</label>
        <textarea id="comparison-query" rows={3} value={query} onChange={event => onQueryChange(event.target.value)} placeholder="비교할 기술과 적용 맥락, 중요하게 볼 항목을 적어 주세요."/>
        <button type="submit" className="comparison-primary" disabled={busy || !query.trim()}>{isClarifying ? '분석 중…' : '에이전트로 구체화'}</button>
      </form>
      {clarifyResult && <div className="comparison-confirmation">
        <p><strong>원래 질문:</strong> {query}</p>
        {clarifyResult.message && <p className="comparison-message" role="status">{clarifyResult.message}</p>}
        {draftFields}{questions}
        <button type="button" disabled={busy} onClick={onConfirmTargets}>답변을 반영해 초안 보완</button>
        <button type="button" className="comparison-primary" disabled={busy} onClick={onApplyDraft}>이 초안으로 직접 지정</button>
        <button type="button" disabled={busy} onClick={() => onResearch()}>이 초안으로 문헌 조사</button>
      </div>}
    </> : <>
      {query && <p><strong>원래 질문:</strong> {query}</p>}
      {clarifyResult?.message && <p className="comparison-message" role="status">{clarifyResult.message}</p>}
      {draftFields}{questions}
      <button type="button" disabled={busy || !query.trim() && !draft.purpose?.trim()} onClick={onConfirmTargets}>에이전트로 초안 보완</button>
      <button type="button" disabled={busy || !query.trim() && !draft.purpose?.trim() && !draft.targetAName?.trim()} onClick={() => onResearch()}>이 초안으로 문헌 조사</button>
      <button type="button" className="comparison-primary" disabled={busy || !targetA || !targetB || targetA === targetB || !draft.purpose?.trim()} onClick={onStartDirectComparison}>{isStartingComparison ? '비교 중…' : '위키 근거로 비교 시작'}</button>
    </>}
  </section>;
}
