/**
 * [계층 1] SectionPrinciples View (Pure Dumb UI Component)
 * - 2번 섹션: 반도체 물리 원리, 단계별 메커니즘
 * - KaTeX 수식 블록 자동 렌더링
 */

import React from 'react';
import { Cpu, Zap } from 'lucide-react';
import { formulaService } from '../../services/formulaService';

export function SectionPrinciples({ principles = [] }) {
  if (!principles || principles.length === 0) return null;

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
            background: 'var(--accent-primary-light)',
            color: 'var(--accent-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 700,
            fontSize: '0.8125rem'
          }}
        >
          2
        </div>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
          작동 및 물리 원리 (Physical Principles & Formulas)
        </h2>
      </div>

      {/* 단계별 원리 카드 목록 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {principles.map((p, idx) => {
          const formulaHtml = p.formula ? formulaService.renderFormula(p.formula, true) : null;
          return (
            <div
              key={idx}
              style={{
                background: 'var(--bg-surface-2)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '16px 20px'
              }}
            >
              {/* 스텝 번호 & 제목 */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: 'var(--accent-primary)',
                    color: '#ffffff'
                  }}
                >
                  Step {p.step || idx + 1}
                </span>
                <span style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {p.title}
                </span>
              </div>

              {/* 물리적 메커니즘 설명 */}
              <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: p.formula ? '12px' : '0' }}>
                {p.content}
              </div>

              {/* KaTeX 수식 블록 */}
              {formulaHtml && (
                <div
                  style={{
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '6px',
                    padding: '12px 16px',
                    margin: '8px 0 0 0',
                    overflowX: 'auto'
                  }}
                  dangerouslySetInnerHTML={{ __html: formulaHtml }}
                />
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
