import React from 'react';
import { SectionPrinciples } from '../wiki/SectionPrinciples';
import { SectionLimitations } from '../wiki/SectionLimitations';
import { SectionPerspectives } from '../wiki/SectionPerspectives';
import { SectionRelations } from '../wiki/SectionRelations';

export function ReviewWikiSections({concept, currentUser, section=null, emptyMessage='이번 보강안에서 확인된 내용이 없습니다. 원문에 실제 내용이 있는지는 추가 검토가 필요합니다.'}) {
  const value = concept || {};
  const empty = <p style={{color:'var(--text-muted)'}}>{emptyMessage}</p>;
  return <div className="review-wiki-sections" data-focus-section={section || "all"}>
    <section data-section="summary"><h3>1. 개요 및 기술 정의</h3>{<div style={{whiteSpace:'pre-wrap'}}>{value.summary || empty}</div>}<h4>도입 목적</h4><p style={{whiteSpace:'pre-wrap'}}>{value.purpose || emptyMessage}</p></section>
    <section data-section="principles">{value.principles?.length ? <SectionPrinciples principles={value.principles} /> : <><h3>2. 작동 및 물리 원리</h3>{empty}</>}</section>
    <section data-section="limitations">{value.limitations?.length ? <SectionLimitations limitations={value.limitations} /> : <><h3>3. 물리적 한계 및 트레이드오프</h3>{empty}</>}</section>
    <section data-section="perspectiveCases">{value.perspectives?.length ? <SectionPerspectives isPreview perspectives={value.perspectives} currentUser={currentUser} l3AccessStatus={value.l3AccessStatus || {hasAccess:false,requestStatus:'none'}} /> : <><h3>4. 적용 사례와 주요 수치</h3>{empty}</>}</section>
    <section data-section="relations">{concept ? <SectionRelations conceptDetail={value} /> : <><h3>5. 온톨로지 인과 관계망 및 규모별 계층도</h3>{empty}</>}</section>
    <section data-section="evidences"><h3>6. 출처 원문</h3>{value.evidences?.length ? value.evidences.map(e => <article key={e.id} style={{padding:'12px',border:'1px solid var(--border-color)',marginBottom:'8px'}}><strong>{e.sourceName}</strong><blockquote style={{whiteSpace:'pre-wrap'}}>{e.quote}</blockquote>{/^https?:\/\//.test(e.externalUrl || '') && <a href={e.externalUrl} target="_blank" rel="noreferrer">원문 출처</a>}</article>) : empty}</section>
  </div>;
}
