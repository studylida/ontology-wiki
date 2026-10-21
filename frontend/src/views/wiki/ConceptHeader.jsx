/**
 * [계층 1] ConceptHeader View (Pure Dumb UI Component)
 * - 개념 명칭, 영문명, 동의어, 세맨틱 버전(v1.2.0), 스케일 뱃지
 * - 듀얼 발의 진입로: [✍️ 이 문서 개정 발의] & [+ 새 문서 발의]
 */

import React from 'react';
import { Edit3, PlusCircle, CheckCircle2, Clock } from 'lucide-react';
import { formatService } from '../../services/formatService';

export function ConceptHeader({
  conceptDetail,
  onOpenRevisionModal,
  onOpenNewConceptModal
}) {
  if (!conceptDetail) return null;

  const scale = formatService.getScaleInfo(conceptDetail.scaleLevel);
  const facet = formatService.getFacetInfo(conceptDetail.domainFacet);

  return (
    <div
      style={{
        padding: '24px 28px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        marginBottom: '20px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
      }}
    >
      {/* 상단 메타데이터 배지 행 & 듀얼 액션 버튼 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {/* 패싯 뱃지 */}
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              padding: '2px 8px',
              borderRadius: '6px',
              background: 'var(--bg-surface-2)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border-color)'
            }}
          >
            {facet.label}
          </span>

          {/* 스케일 레벨 뱃지 */}
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '6px',
              background: scale.bg,
              color: scale.color
            }}
          >
            {scale.label} ({conceptDetail.scaleName || '공정'})
          </span>

          {/* 세맨틱 버전 */}
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              padding: '2px 8px',
              borderRadius: '6px',
              background: 'var(--accent-primary-light)',
              color: 'var(--accent-primary)'
            }}
          >
            v{conceptDetail.version || '1.2.0'}
          </span>

          {/* 채택 상태 */}
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              padding: '2px 8px',
              borderRadius: '6px',
              background: 'var(--accent-success-light)',
              color: 'var(--accent-success)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <CheckCircle2 size={12} />
            공인 온톨로지 승인
          </span>

          {/* 최종 검토 일시 */}
          {conceptDetail.lastReviewedAt && (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <Clock size={12} />
              {formatService.formatDateTime(conceptDetail.lastReviewedAt)} 검토
            </span>
          )}
        </div>

        {/* 🌟 듀얼 발의 진입로 버튼 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            onClick={onOpenRevisionModal}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface-2)',
              color: 'var(--text-primary)',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Edit3 size={13} style={{ color: 'var(--accent-primary)' }} />
            <span>이 문서 개정 발의</span>
          </button>

          <button
            type="button"
            onClick={onOpenNewConceptModal}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid var(--accent-primary)',
              background: 'var(--accent-primary)',
              color: '#ffffff',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <PlusCircle size={13} />
            <span>+ 새 문서 발의</span>
          </button>
        </div>
      </div>

      {/* 개념 타이틀 & 영문명 */}
      <h1 style={{ fontSize: '1.625rem', fontWeight: 800, margin: '0 0 6px 0', color: 'var(--text-primary)' }}>
        {conceptDetail.title}
      </h1>
      {conceptDetail.engName && (
        <div style={{ fontSize: '0.9375rem', color: 'var(--text-muted)', marginBottom: '10px' }}>
          {conceptDetail.engName}
        </div>
      )}

      {/* 동의어 및 축약어 칩 */}
      {conceptDetail.aliases && conceptDetail.aliases.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>동의어 / 표준 축약어:</span>
          {conceptDetail.aliases.map((alias, idx) => (
            <span
              key={idx}
              style={{
                fontSize: '0.75rem',
                padding: '2px 6px',
                borderRadius: '4px',
                background: 'var(--bg-surface-2)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-secondary)'
              }}
            >
              {alias}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
