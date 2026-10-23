/**
 * [계층 1] ComparisonHeaderBar View (Pure Dumb UI Component)
 * - 화면 2-B 상단: 분석 전제 요약 바 & [조건 수정 ↩] 원클릭 복귀
 */

import React from 'react';
import { ArrowLeft, RotateCcw, GitCompare, Tag } from 'lucide-react';

export function ComparisonHeaderBar({
  currentSession,
  onResetToSetup
}) {
  if (!currentSession) return null;

  const targetA = currentSession.contextParams?.targetAName || currentSession.contextParams?.targetA || 'Target A';
  const targetB = currentSession.contextParams?.targetBName || currentSession.contextParams?.targetB || 'Target B';
  const domain = currentSession.contextParams?.domain || '적용 맥락 미지정';

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '14px 20px',
        marginBottom: '20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            background: 'var(--accent-primary-light)',
            color: 'var(--accent-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <GitCompare size={18} />
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
              📌 {targetA} vs {targetB}
            </h3>
            <span
              style={{
                fontSize: '0.6875rem',
                fontWeight: 600,
                padding: '2px 6px',
                borderRadius: '4px',
                background: 'var(--bg-surface-2)',
                color: 'var(--text-secondary)',
                border: '1px solid var(--border-color)'
              }}
            >
              {domain}
            </span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            비교 목적: {currentSession.contextParams?.draft?.purpose || currentSession.query}
            {currentSession.contextParams?.draft?.purpose && <div>원래 질문: {currentSession.query}</div>}
          </div>
        </div>
      </div>

      {/* 조건 수정 버튼 */}
      <button
        type="button"
        onClick={onResetToSetup}
        style={{
          padding: '6px 14px',
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
        <RotateCcw size={13} />
        <span>조건 수정 ↩</span>
      </button>
    </div>
  );
}
