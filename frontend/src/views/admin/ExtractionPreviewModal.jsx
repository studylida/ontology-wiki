/**
 * [계층 1] ExtractionPreviewModal (Pure Dumb UI Component)
 * - 추출된 기술 지식을 기존 위키 데이터 계약(Wiki DTO)으로 시각화하는 변경 미리보기 모달
 * - 목적, 단계별 원리, 한계, 적용 사례, 관계망을 한눈에 검토 후 관리자가 [위키에 적용] 클릭
 */

import React, { useState } from 'react';
import { SectionPrinciples } from '../wiki/SectionPrinciples';
import { SectionLimitations } from '../wiki/SectionLimitations';
import { SectionPerspectives } from '../wiki/SectionPerspectives';
import { DOMAIN_FACET_LABELS } from '../../types/concept.dto';
import { relationService } from '../../services/relationService';
import {
  X,
  CheckCircle2,
  Database,
  ArrowRight,
  Layers,
  Cpu,
  AlertTriangle,
  GitBranch,
  Quote,
  Check
} from 'lucide-react';

export function ExtractionPreviewModal({
  isOpen = false,
  previewData = null,
  isApplying = false,
  onClose,
  onApply,
  onChangeClassification,
  classificationError = null
}) {
  const [selectedConceptIndex, setSelectedConceptIndex] = useState(0);
  const [showExtracted, setShowExtracted] = useState(false);

  if (!isOpen || !previewData) return null;

  const concepts = previewData.aggregatedConcepts || previewData.preview || [];
  if (concepts.length === 0) {
    return (
      <div className="modal-backdrop" style={backdropStyle}>
        <div className="modal-box" style={{ ...boxStyle, maxWidth: '500px', padding: '24px', textAlign: 'center' }}>
          <AlertTriangle size={36} style={{ color: '#f59e0b', margin: '0 auto 12px' }} />
          <div style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '8px' }}>추출된 온톨로지 지식이 없습니다.</div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
            해당 백서에서 추출 가능한 공정/기술 개념을 포착하지 못했습니다.
          </p>
          <button type="button" onClick={onClose} style={btnSecondaryStyle}>
            닫기
          </button>
        </div>
      </div>
    );
  }

  const currentConcept = concepts[selectedConceptIndex] || concepts[0];
  const body = showExtracted ? currentConcept : (currentConcept.mergedPreview || {});
  const coverage = currentConcept.sourceCoverage;
  const hasBlockers = concepts.some((concept) => concept.applyBlockers?.length || !concept.mergedPreview);
  const changeClassification = (values) => onChangeClassification?.(currentConcept.conceptId, {
    domainFacet: currentConcept.domainFacet, category: currentConcept.category, scaleLevel: currentConcept.scaleLevel, ...values
  });

  return (
    <div className="modal-backdrop" style={backdropStyle}>
      <div className="modal-box" style={boxStyle}>
        {/* ── 상단 헤더 ── */}
        <div style={headerStyle}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                추출 결과 위키 변경 미리보기 (Diff Preview)
              </span>
              <span
                style={{
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontSize: '0.6875rem',
                  fontWeight: 600,
                  background: 'rgba(59, 130, 246, 0.1)',
                  color: 'var(--accent-primary)'
                }}
              >
                총 {concepts.length}개 개념 도출됨
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              기존 내용 보존과 빈칸 보강을 반영한 본문을 확인하세요. 인용문 위치 확인은 해석의 정확성까지 보장하지 않습니다.
            </div>
          </div>

          <button type="button" onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
            <X size={20} />
          </button>
        </div>

        {/* ── 본문: 좌측 개념 탭 + 우측 위키 풀 스키마 뷰어 ── */}
        <div style={{ display: 'flex', flex: 1, minHeight: 0, overflow: 'hidden' }}>
          {/* 좌측: 도출된 개념 탭 */}
          <div
            style={{
              width: '220px',
              borderRight: '1px solid var(--border-color)',
              background: 'var(--bg-page)',
              display: 'flex',
              flexDirection: 'column',
              overflowY: 'auto'
            }}
          >
            <div style={{ padding: '12px 14px', fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-muted)' }}>
              도출된 온톨로지 개념 목록
            </div>
            {concepts.map((c, idx) => {
              const isSelected = idx === selectedConceptIndex;
              return (
                <button
                  key={c.conceptId + '-' + idx}
                  type="button"
                  onClick={() => setSelectedConceptIndex(idx)}
                  style={{
                    padding: '10px 14px',
                    textAlign: 'left',
                    background: isSelected ? 'var(--bg-surface)' : 'transparent',
                    border: 'none',
                    borderLeft: isSelected ? '3px solid var(--accent-primary)' : '3px solid transparent',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ fontWeight: isSelected ? 700 : 500, fontSize: '0.8125rem', color: 'var(--text-primary)' }}>
                    {c.title}
                  </div>
                  <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                    {c.conceptId}
                  </div>
                </button>
              );
            })}
          </div>

          {/* 우측: 위키 본문 풀 계약 시각화 */}
          <div style={{ flex: 1, padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* 개념 식별자 & 카테고리 헤더 */}
            <div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '6px' }}>
                <span style={badgeStyle}>{currentConcept.category || '미분류'}</span>
                {currentConcept.isNew ? (
                  <span style={{ ...badgeStyle, background: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>
                    신규 개념 생성
                  </span>
                ) : (
                  <span style={{ ...badgeStyle, background: 'rgba(59, 130, 246, 0.1)', color: 'var(--accent-primary)' }}>
                    기존 개념 보강
                  </span>
                )}
              </div>
              <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                {currentConcept.title}
              </h2>
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                {currentConcept.engName} ({currentConcept.conceptId})
              </div>
            </div>

            <div style={sectionBoxStyle}>
              <div style={sectionTitleStyle}>분류 검토</div>
              {currentConcept.existingClassification && <p style={{ fontSize: '0.75rem' }}>
                현재 위키: {DOMAIN_FACET_LABELS[currentConcept.existingClassification.domainFacet]} / {currentConcept.existingClassification.category} / Scale {currentConcept.existingClassification.scaleLevel}
              </p>}
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <label>분야 <select aria-label="추출 개념 분야" value={currentConcept.domainFacet || ''} disabled={isApplying}
                  onChange={(e) => changeClassification({ domainFacet: e.target.value || null })}>
                  <option value="">분야 확인 필요</option>
                  {Object.entries(DOMAIN_FACET_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select></label>
                <label>분류 <input aria-label="추출 개념 분류" value={currentConcept.category || ''} maxLength={64} disabled={isApplying}
                  onChange={(e) => changeClassification({ category: e.target.value })} /></label>
                <label>규모 <select aria-label="추출 개념 규모" value={currentConcept.scaleLevel || ''} disabled={isApplying}
                  onChange={(e) => changeClassification({ scaleLevel: e.target.value ? Number(e.target.value) : null })}>
                  <option value="">규모 확인 필요</option>
                  {[1, 2, 3, 4, 5].map((scale) => <option key={scale} value={scale}>{relationService.getScaleLabel(scale)}</option>)}
                </select></label>
              </div>
              {(currentConcept.classificationProposals || []).map((proposal, index) => <p key={index} style={{ fontSize: '0.75rem' }}>
                이번 추출 제안: {DOMAIN_FACET_LABELS[proposal.domainFacet] || '분야 미확정'} / {proposal.category} / {proposal.scaleLevel ? `Scale ${proposal.scaleLevel}` : '규모 미확정'}
                {proposal.classificationNote && ` · ${proposal.classificationNote}`}
              </p>)}
              {!currentConcept.classificationProposals?.length && currentConcept.classificationNote && <p>추출 분류 사유: {currentConcept.classificationNote}</p>}
              {currentConcept.existingClassification && <p>기존 위키 분류를 기본으로 유지합니다. 위 입력에서 정정하면 같은 개념의 모든 제안에 반영됩니다.</p>}
              {currentConcept.classificationConflict && <p role="alert">원문 구간별 분류 제안이 다릅니다. {currentConcept.existingClassification ? '기존 위키 분류를 유지하거나 명시적으로 정정해주세요.' : '분류를 확인한 뒤 확정해주세요.'}</p>}
              <button type="button" disabled={isApplying} onClick={() => changeClassification({})}>현재 분류로 확정</button>
              {classificationError && <p role="alert" style={{ color: '#b45309' }}>{classificationError}</p>}
              {(currentConcept.validationWarnings || []).map((warning, index) => <p key={index} style={{ color: '#b45309', fontSize: '0.75rem' }}>{warning}</p>)}
            </div>

            {/* 개요 (Summary) & 목적 (Purpose) */}
            <div style={sectionBoxStyle}>
              <div style={sectionTitleStyle}>원문 처리 범위 및 적용 상태</div>
              <p>{coverage?.complete
                ? '원문 전체 구간 처리: ' + coverage.processedParts + '/' + coverage.totalParts + '구간 · ' + coverage.processedCharacters + '/' + coverage.totalCharacters + '자'
                : '전체 원문 처리 이력 없음 · 다시 추출 필요'}</p>
              {(currentConcept.applyBlockers || []).map((message, index) => <p key={index} role="alert" style={{ color: '#b45309' }}>{message}</p>)}
              {currentConcept.missingFields?.length > 0 && <p>적용 후 비어 있는 항목: {currentConcept.missingFields.join(', ')}. 원문에 없는 내용을 만들어 채우지 않습니다.</p>}
              <label><input type="checkbox" checked={showExtracted} onChange={(e) => setShowExtracted(e.target.checked)} /> 이번 추출 제안 보기</label>
              <p>{showExtracted ? '아래는 병합 전 제안입니다. 근거 미확인 항목은 적용에서 제외됩니다.' : '아래는 선택한 문서들을 적용했을 때의 위키 본문입니다.'}</p>
            </div>

            <div style={sectionBoxStyle}>
              <div style={sectionTitleStyle}>1. 개요 및 목적</div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-primary)', marginBottom: '8px', lineHeight: 1.5 }}>
                <strong>개요:</strong> {body.summary || '내용 없음'}
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                <strong>도입 목적:</strong> {body.purpose || '내용 없음'}
              </div>
            </div>

            {/* 단계별 작동 원리 (Principles) */}
            <SectionPrinciples principles={body.principles} />

            {/* 공학적 한계 및 트레이드오프 (Limitations) */}
            <SectionLimitations limitations={body.limitations} />

            <SectionPerspectives
              isPreview
              perspectives={(body.perspectiveCases || []).map((item) => ({...item, contextNarrative: item.narrative || item.contextNarrative}))}
              currentUser={{level: 4}}
              l3AccessStatus={{hasAccess: true, requestStatus: 'approved'}}
            />

            <div style={sectionBoxStyle}>
              <div style={sectionTitleStyle}>관계 및 원문 근거</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px' }}>
                {[
                  ['previousSteps', '선행 공정'], ['nextSteps', '후속 공정'], ['alternatives', '기술적 대안'],
                  ['partOf', '상위 소속 대상'], ['isA', '분류 관계']
                ].map(([field, label]) => <div key={field} style={{ padding: '8px 10px', background: 'var(--bg-page)', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700 }}>{label}</div>
                  {(body[field] || []).length === 0 && <p>내용 없음</p>}
                  {(body[field] || []).map((rel, index) => <div key={index} style={{ fontSize: '0.75rem', marginTop: '8px' }}>
                    <strong>{rel.name || rel.targetName || rel.id || rel.targetId}</strong>
                    {rel.reason && <p>{rel.reason}</p>}
                    {rel.commonGoal && <p>공통 목적: {rel.commonGoal}</p>}
                    {rel.tradeoff && <p>비교: {rel.tradeoff}</p>}
                    <div style={{ color: rel.evidenceVerified === false ? '#b45309' : 'var(--text-secondary)' }}>
                      {rel.evidenceVerified === false ? '근거 확인 필요 · 적용 제외' : rel.evidenceVerified ? '추출 제안' : '기존 등록 내용 보존'}
                    </div>
                    <blockquote>{rel.evidenceQuote || '인용문 없음'}</blockquote>
                  </div>)}
                </div>)}
              </div>
            </div>

            {/* 원문 인용 출처 (Evidence Quote) */}
            <details style={sectionBoxStyle}>
              <summary>이번 추출의 본문 항목별 원문 근거</summary>
              {['summary', 'purpose'].map((field) => <div key={field}>
                <strong>{field === 'summary' ? '개요' : '목적'}</strong>
                {(currentConcept[field + 'EvidenceQuotes']?.length
                  ? currentConcept[field + 'EvidenceQuotes'] : [currentConcept[field + 'EvidenceQuote']])
                  .filter(Boolean).map((quote, index) => <blockquote key={index}>{quote}</blockquote>)}
              </div>)}
              {['principles', 'limitations', 'perspectiveCases'].map((field) => (currentConcept[field] || []).map((item, index) => <div key={field + '-' + index}>
                <strong>{item.title || item.perspectiveTitle || field}</strong>
                <p>{item.evidenceVerified ? '추출 제안' : '근거 확인 필요 · 적용 제외'}</p>
                <blockquote>{item.evidenceQuote || '인용문 없음'}</blockquote>
              </div>))}
            </details>

            {currentConcept.evidenceQuote && (
              <div style={{ padding: '12px 14px', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.15)', fontSize: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, color: 'var(--accent-primary)', marginBottom: '4px' }}>
                  <Quote size={13} />
                  <span>{currentConcept.evidenceVerified ? '추출 과정의 참고 인용' : '추출 과정의 참고 인용'}</span>
                </div>
                <div style={{ color: 'var(--text-primary)', fontStyle: 'italic', lineHeight: 1.5 }}>
                  "{currentConcept.evidenceQuote}"
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── 하단 액션 바 ── */}
        <div style={footerStyle}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            확인 후 [위키에 적용]을 누르면 운영계 온톨로지 DB에 원자적으로 커밋됩니다.
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button type="button" onClick={onClose} style={btnSecondaryStyle}>
              닫기
            </button>
            <button
              type="button"
              disabled={isApplying || hasBlockers || !!classificationError || !(previewData.results || []).some((r) => r.succeeded)}
              onClick={() => onApply()}
              style={btnPrimaryStyle}
            >
              <Database size={15} />
              <span>{isApplying ? '위키 적용 중...' : '위키에 최종 적용 (Apply)'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const backdropStyle = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  background: 'rgba(0,0,0,0.65)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 10000,
  padding: '24px'
};

const boxStyle = {
  background: 'var(--bg-surface)',
  border: '1px solid var(--border-color)',
  borderRadius: '12px',
  width: '100%',
  maxWidth: '960px',
  height: '85vh',
  display: 'flex',
  flexDirection: 'column',
  boxShadow: '0 24px 48px rgba(0,0,0,0.3)',
  overflow: 'hidden'
};

const headerStyle = {
  padding: '16px 24px',
  borderBottom: '1px solid var(--border-color)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between'
};

const footerStyle = {
  padding: '14px 24px',
  borderTop: '1px solid var(--border-color)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  background: 'var(--bg-surface)'
};

const sectionBoxStyle = {
  padding: '14px 16px',
  background: 'var(--bg-surface)',
  border: '1px solid var(--border-color)',
  borderRadius: '8px'
};

const sectionTitleStyle = {
  fontSize: '0.8125rem',
  fontWeight: 700,
  color: 'var(--text-primary)',
  marginBottom: '8px'
};

const badgeStyle = {
  display: 'inline-block',
  padding: '2px 8px',
  borderRadius: '4px',
  fontSize: '0.6875rem',
  fontWeight: 600,
  background: 'var(--bg-page)',
  color: 'var(--text-secondary)',
  border: '1px solid var(--border-color)'
};

const btnSecondaryStyle = {
  padding: '8px 16px',
  borderRadius: '6px',
  border: '1px solid var(--border-color)',
  background: 'var(--bg-page)',
  color: 'var(--text-primary)',
  fontSize: '0.8125rem',
  cursor: 'pointer'
};

const btnPrimaryStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  padding: '8px 20px',
  borderRadius: '6px',
  border: 'none',
  background: 'var(--accent-primary)',
  color: '#fff',
  fontSize: '0.8125rem',
  fontWeight: 600,
  cursor: 'pointer'
};
