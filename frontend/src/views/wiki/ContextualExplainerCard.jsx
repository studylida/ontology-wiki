/**
 * [계층 1] ContextualExplainerCard View (Pure Dumb UI Component)
 * - 0ms 인라인 문맥 해설 팝오버 / 플로팅 카드
 * - 부모 공정 맥락 문장 및 deep link 제공
 */

import React from 'react';
import { X, ExternalLink, Sparkles, BookOpen } from 'lucide-react';

export function ContextualExplainerCard({
  explainerData,
  onClose,
  onNavigate
}) {
  if (!explainerData) return null;

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--accent-primary)',
        borderRadius: '10px',
        padding: '16px',
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)',
        marginBottom: '20px'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Sparkles size={15} style={{ color: 'var(--accent-primary)' }} />
          <h4 style={{ fontSize: '0.875rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            {explainerData.title}
          </h4>
          {explainerData.cached && (
            <span
              style={{
                fontSize: '0.625rem',
                padding: '1px 4px',
                borderRadius: '3px',
                background: 'var(--accent-success-light)',
                color: 'var(--accent-success)',
                fontWeight: 600
              }}
            >
              0ms 캐시
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="닫기"
          style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
        >
          <X size={15} />
        </button>
      </div>

      {/* 공학적 정의 */}
      <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 0 10px 0' }}>
        {explainerData.definition}
      </p>

      {/* 부모 문맥 문장 */}
      {explainerData.contextSentence && (
        <div
          style={{
            background: 'var(--bg-surface-2)',
            padding: '8px 10px',
            borderRadius: '6px',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            lineHeight: 1.5,
            marginBottom: '12px'
          }}
        >
          {explainerData.contextSentence}
        </div>
      )}

      {/* 개념 상세 페이지 바로가기 */}
      <button
        type="button"
        onClick={() => {
          onNavigate(explainerData.childConceptId);
          onClose();
        }}
        style={{
          width: '100%',
          padding: '6px 10px',
          borderRadius: '6px',
          border: '1px solid var(--accent-primary)',
          background: 'var(--accent-primary-light)',
          color: 'var(--accent-primary)',
          fontSize: '0.75rem',
          fontWeight: 600,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '4px'
        }}
      >
        <BookOpen size={13} />
        <span>해당 개념 지식 페이지로 이동 ➔</span>
      </button>
    </div>
  );
}
