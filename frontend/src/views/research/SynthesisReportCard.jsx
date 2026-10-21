/**
 * [계층 1] SynthesisReportCard View (Pure Dumb UI Component)
 * - 화면 3단계: 발굴 문헌 종합 분석 리포트 카드
 * - 교차 분석 서술(Markdown) & [공통 합의점] vs [이견/한계 지점] 2컬럼 비교
 */

import React from 'react';
import { FileText, CheckCircle2, AlertTriangle } from 'lucide-react';

export function SynthesisReportCard({ synthesisReport }) {
  if (!synthesisReport) return null;

  const { title, narrativeMarkdown, consensusFacts = [], tensionGaps = [] } = synthesisReport;

  // 마크다운 서술 간단 렌더러 (### 헤더 및 본문 단락 분리)
  const renderMarkdown = (text = '') => {
    return text.split('\n\n').map((block, idx) => {
      const trimmed = block.trim();
      if (trimmed.startsWith('### ')) {
        return (
          <h4
            key={idx}
            style={{
              fontSize: '1rem',
              fontWeight: 800,
              color: 'var(--text-primary)',
              margin: '18px 0 8px 0',
              paddingBottom: '4px',
              borderBottom: '1px solid var(--border-color)'
            }}
          >
            {trimmed.replace('### ', '')}
          </h4>
        );
      }
      return (
        <p
          key={idx}
          style={{
            fontSize: '0.875rem',
            lineHeight: 1.7,
            color: 'var(--text-primary)',
            margin: '0 0 12px 0'
          }}
        >
          {trimmed}
        </p>
      );
    });
  };

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
      {/* 리포트 헤더 */}
      <div style={{ paddingBottom: '16px', borderBottom: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <FileText size={20} style={{ color: 'var(--accent-primary)' }} />
          <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
            {title || '문헌 교차 종합 분석 리포트'}
          </h3>
        </div>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>
          선택된 공인 기술 문헌 및 표준 규격을 대조 분석하여 도출된 공학적 인과 인사이트입니다.
        </p>
      </div>

      {/* 리포트 본문 서술 */}
      <div style={{ background: 'var(--bg-surface-2)', borderRadius: '8px', padding: '16px 20px', border: '1px solid var(--border-color)' }}>
        {renderMarkdown(narrativeMarkdown)}
      </div>

      {/* 2컬럼 콜아웃: 공통 합의점 vs 이견/한계 지점 */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '16px'
        }}
      >
        {/* 공통 합의 사실 */}
        <div
          style={{
            background: 'rgba(16, 185, 129, 0.06)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: '8px',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle2 size={18} style={{ color: '#059669' }} />
            <h4 style={{ margin: 0, fontSize: '0.875rem', fontWeight: 800, color: '#059669' }}>
              공통 합의 사실 (Consensus Facts)
            </h4>
          </div>
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.8125rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
            {consensusFacts.map((fact, idx) => (
              <li key={idx} style={{ marginBottom: '4px' }}>{fact}</li>
            ))}
          </ul>
        </div>

        {/* 이견 및 물리적 한계점 */}
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.06)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '8px',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} style={{ color: '#dc2626' }} />
            <h4 style={{ margin: 0, fontSize: '0.875rem', fontWeight: 800, color: '#dc2626' }}>
              이견 및 기술적 한계 (Tension Gaps & Bottlenecks)
            </h4>
          </div>
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.8125rem', lineHeight: 1.6, color: 'var(--text-primary)' }}>
            {tensionGaps.map((gap, idx) => (
              <li key={idx} style={{ marginBottom: '4px' }}>{gap}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
