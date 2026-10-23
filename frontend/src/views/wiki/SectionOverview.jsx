/**
 * [계층 1] SectionOverview View (Pure Dumb UI Component)
 * - 1번 섹션: 핵심 기술 정의, 개요 및 도입 목적
 * - 온톨로지 핵심 용어 인라인 태그 및 0ms 문맥 해설 트리거
 */

import React from 'react';
import { Target, BookOpen } from 'lucide-react';

export function SectionOverview({
  summary,
  purpose
}) {
  return (
    <section
      style={{
        padding: '24px 28px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        marginBottom: '20px'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
        <div
          style={{
            width: '24px',
            height: '24px',
            borderRadius: '6px',
            background: 'var(--accent-primary-light)',
            color: 'var(--accent-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 700,
            fontSize: '0.8125rem'
          }}
        >
          1
        </div>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
          개요 및 기술 정의 (Summary & Definition)
        </h2>
      </div>

      {/* 개요 본문 */}
      <div style={{ fontSize: '0.9375rem', lineHeight: 1.7, color: 'var(--text-secondary)', marginBottom: '16px' }}>
        {summary}
      </div>

      {/* 도입 목적 박스 */}
      {purpose && (
        <div
          style={{
            background: 'var(--bg-surface-2)',
            borderLeft: '4px solid var(--accent-primary)',
            borderRadius: '0 8px 8px 0',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px'
          }}
        >
          <Target size={18} style={{ color: 'var(--accent-primary)', marginTop: '2px', flexShrink: 0 }} />
          <div>
            <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
              공학적 도입 목적 및 핵심 과제
            </div>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {purpose}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
