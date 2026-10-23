/**
 * [계층 1] KnowledgeCandidateList View (Pure Dumb UI Component)
 * - 화면 3단계: 문헌 교차 분석에서 도출된 정형 온톨로지 신규 지식 후보 카드 목록
 * - [📋 검토 센터(Tab 3)로 티켓 등록 ➔] 액션 트리거
 */

import React from 'react';
import { researchFormatterService } from '../../services/researchFormatterService';
import { Lightbulb, Send, Check, ShieldAlert, Tag, ExternalLink } from 'lucide-react';

export function KnowledgeCandidateList({
  candidates = [],
  currentUser = null,
  onOpenExportModal
}) {
  if (!candidates || candidates.length === 0) return null;

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '24px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
      }}
    >
      {/* 헤더 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '16px', borderBottom: '1px solid var(--border-color)', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Lightbulb size={20} style={{ color: 'var(--accent-primary)' }} />
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
              도출된 온톨로지 지식 후보 (Knowledge Candidates)
            </h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
              확보한 문헌을 바탕으로 AI가 제안한 검토 대기 후보입니다. 검토 승인 센터(Tab 3)에 정식 안건으로 등록할 수 있습니다.
            </p>
          </div>
        </div>
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            padding: '2px 8px',
            borderRadius: '12px',
            background: 'var(--accent-primary-light)',
            color: 'var(--accent-primary)'
          }}
        >
          총 {candidates.length}건 도출
        </span>
      </div>

      {/* 후보 목록 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {candidates.map((cand) => {
          const specs = cand.draftPayload?.specifications || [];
          const evidenceIds = cand.evidenceIds || [];

          return (
            <div
              key={cand.candidateId}
              style={{
                borderRadius: '10px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface-2)',
                padding: '18px 20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}
            >
              {/* 카드 상단 바 */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span
                    style={{
                      fontSize: '0.6875rem',
                      fontWeight: 800,
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: 'var(--accent-primary)',
                      color: '#fff'
                    }}
                  >
                    {researchFormatterService.getCandidateTypeLabel(cand.candidateType)}
                  </span>
                  <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                    {cand.title}
                  </h4>
                </div>

                <button
                  type="button"
                  onClick={() => onOpenExportModal(cand)}
                  style={{
                    padding: '8px 14px',
                    borderRadius: '6px',
                    border: 'none',
                    background: 'var(--accent-primary)',
                    color: '#fff',
                    fontSize: '0.8125rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    transition: 'all 0.15s ease'
                  }}
                  title="검토 센터(Tab 3) 대기 큐에 정식 개정 티켓으로 등록합니다."
                >
                  <Send size={14} />
                  <span>검토 센터(Tab 3)로 티켓 등록 ➔</span>
                </button>
              </div>

              {/* 요약 */}
              <p style={{ fontSize: '0.8125rem', lineHeight: 1.6, color: 'var(--text-primary)', margin: 0 }}>
                {cand.summary}
              </p>

              {/* 스펙 배지 목록 */}
              {specs.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', paddingTop: '4px' }}>
                  <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-muted)' }}>정형 스펙:</span>
                  {specs.map((s, sIdx) => (
                    <div
                      key={sIdx}
                      style={{
                        fontSize: '0.75rem',
                        padding: '3px 8px',
                        borderRadius: '4px',
                        background: 'var(--bg-surface)',
                        border: '1px solid var(--border-color)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      <span style={{ color: 'var(--text-secondary)' }}>{s.label}:</span>
                      <strong style={{ color: 'var(--accent-primary)', fontFamily: 'var(--font-mono)' }}>{s.value}</strong>
                    </div>
                  ))}
                </div>
              )}

              {cand.draftPayload?.content && cand.draftPayload.content !== cand.summary && <p style={{ whiteSpace: 'pre-wrap' }}>{cand.draftPayload.content}</p>}
              {cand.draftPayload?.isNewConcept && <p>분류안: {cand.draftPayload.domainFacet || '분야 미확정'} · 규모 {cand.draftPayload.scaleLevel ?? '미확정'} · {cand.draftPayload.processCategory || '분류 미확정'} (검토관이 승인 시 확정)</p>}
              {/* 뒷받침 공인 출처 배지 목록 */}
              {evidenceIds.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-muted)' }}>근거 출처:</span>
                  {evidenceIds.map((eid, eIdx) => (
                    <span
                      key={eIdx}
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.6875rem',
                        fontWeight: 700,
                        color: 'var(--accent-primary)',
                        background: 'var(--accent-primary-light)',
                        padding: '1px 6px',
                        borderRadius: '4px'
                      }}
                    >
                      [{eid}]
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
