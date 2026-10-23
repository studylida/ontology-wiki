/**
 * [계층 1] SectionLimitations View (Pure Dumb UI Component)
 * - 3번 섹션: 물리적 한계 및 트레이드오프
 * - [E-01] 공인 출처 배지 및 신뢰도 배지 렌더링
 */

import React from 'react';
import { AlertTriangle, BookCheck, ExternalLink } from 'lucide-react';

export function SectionLimitations({ limitations = [] }) {
  if (!limitations || limitations.length === 0) return null;

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
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
        <div
          style={{
            width: '24px',
            height: '24px',
            borderRadius: '6px',
            background: 'var(--accent-warning-light)',
            color: 'var(--accent-warning)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 700,
            fontSize: '0.8125rem'
          }}
        >
          3
        </div>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
          물리적 한계 및 공학 트레이드오프 (Physical Limitations & Tradeoffs)
        </h2>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {limitations.map((lim, idx) => (
          <div
            key={idx}
            style={{
              background: 'var(--bg-surface-2)',
              border: '1px solid var(--border-color)',
              borderLeft: '4px solid var(--accent-warning)',
              borderRadius: '0 8px 8px 0',
              padding: '16px 20px'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle size={15} style={{ color: 'var(--accent-warning)' }} />
                <span style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {lim.title}
                </span>
              </div>

              {/* 공인 출처 배지 목록 */}
              {lim.evidenceIds && lim.evidenceIds.length > 0 && (
                <div style={{ display: 'flex', gap: '6px' }}>
                  {lim.evidenceIds.map((eid) => {
                    return (
                      <span
                        key={eid}
                        style={{
                          fontSize: '0.6875rem',
                          fontWeight: 700,
                          padding: '2px 7px',
                          borderRadius: '4px',
                          background: 'var(--accent-primary-light)',
                          color: 'var(--accent-primary)',
                          border: '1px solid rgba(37, 99, 235, 0.2)',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '3px',
                          cursor: 'pointer'
                        }}
                        title={'출처 ' + eid + ' · 원문 정보는 아래 출처 목록에서 확인하세요.'}
                      >
                        <BookCheck size={11} />
                        [{eid}]
                      </span>
                    );
                  })}
                </div>
              )}
            </div>

            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
              {lim.description}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
