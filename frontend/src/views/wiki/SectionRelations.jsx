/**
 * [계층 1] SectionRelations View (Pure Dumb UI Component)
 * - 4번 섹션: 온톨로지 분류·인과 관계망 및 물리적 규모(Scale) 계층도
 * - 상단 멀티스케일 인과 네비게이터 카드 (Scale n+1 ➔ Scale n ➔ Scale n-1)
 * - 하단 4분할 온톨로지 관계 그리드 (is_a, part_of, next_step, alternative_to)
 */

import React from 'react';
import { GitBranch, Layers, ArrowRight, ArrowUpRight, Cpu, Box, Activity } from 'lucide-react';
import { formatService } from '../../services/formatService';

export function SectionRelations({
  conceptDetail,
  onSelectConcept
}) {
  if (!conceptDetail) return null;

  const relations = conceptDetail.relations || {};
  const currentScale = conceptDetail.scaleLevel || 3;
  const scaleInfo = formatService.getScaleInfo(currentScale);

  const isAList = relations.is_a || [];
  const partOfList = relations.part_of || [];
  const nextStepList = relations.next_step || [];
  const altList = relations.alternative_to || [];

  return (
    <article
      style={{
        padding: '24px 28px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        marginBottom: '20px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
        <GitBranch size={20} style={{ color: 'var(--accent-primary)' }} />
        <h2 style={{ fontSize: '1.125rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
          4. 온톨로지 관계 및 물리적 규모(Scale) 계층
        </h2>
      </div>

      {/* ── 상단 멀티스케일 컨텍스트 네비게이터 카드 (3-Tier Scale Cards) ── */}
      <div
        style={{
          background: 'var(--bg-surface-2)',
          border: '1px solid var(--border-color)',
          borderRadius: '10px',
          padding: '16px',
          marginBottom: '18px'
        }}
      >
        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Layers size={14} />
          <span>멀티스케일 인과 제어 계층도 (Multi-Scale Context Navigator)</span>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '12px'
          }}
        >
          {/* 상위 제어·설비 계층 (Scale n+1) */}
          <div
            style={{
              padding: '12px',
              borderRadius: '8px',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}
          >
            <div style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-muted)' }}>
              ▲ 상위 제어·설비 계층 (Scale {Math.min(5, currentScale + 1)})
            </div>
            <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {partOfList.length > 0 ? partOfList[0].name : '단위 공정 제어 및 장비 인프라'}
            </div>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-secondary)' }}>
              상위 설비 및 챔버 제어 파라미터가 현재 공정 상태를 결정합니다.
            </div>
          </div>

          {/* 현재 공정·소자 계층 (Scale n) */}
          <div
            style={{
              padding: '12px',
              borderRadius: '8px',
              background: 'var(--accent-primary-light)',
              border: '1px solid var(--accent-primary)',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}
          >
            <div style={{ fontSize: '0.6875rem', fontWeight: 800, color: 'var(--accent-primary)' }}>
              ● 현재 단위 공정 계층 (Scale {currentScale})
            </div>
            <div style={{ fontSize: '0.875rem', fontWeight: 800, color: 'var(--accent-primary)' }}>
              {conceptDetail.title}
            </div>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-primary)' }}>
              {conceptDetail.scaleName || '단위 공정 규격 및 물리 임계 조건'}
            </div>
          </div>

          {/* 하위 물리·재료 계층 (Scale n-1) */}
          <div
            style={{
              padding: '12px',
              borderRadius: '8px',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}
          >
            <div style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-muted)' }}>
              ▼ 하위 물리·재료 계층 (Scale {Math.max(1, currentScale - 1)})
            </div>
            <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              나노 패턴 계면 & 원자 물성 반응
            </div>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-secondary)' }}>
              하위 미시 물성 거동이 단위 공정의 수율 및 보이드 결함으로 발현됩니다.
            </div>
          </div>
        </div>
      </div>

      {/* ── 하단 4분할 온톨로지 관계망 그리드 ── */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '12px'
        }}
      >
        {/* 1. 분류 체계 (is_a) */}
        <div style={{ background: 'var(--bg-surface-2)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.6875rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
            분류 체계 (is_a)
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {isAList.length > 0 ? (
              isAList.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => item.id && onSelectConcept && onSelectConcept(item.id)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-surface)',
                    color: item.id ? 'var(--accent-primary)' : 'var(--text-primary)',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    cursor: item.id ? 'pointer' : 'default',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <span>{item.name || item.title || item.id}</span>
                  {item.id && <ArrowUpRight size={12} />}
                </button>
              ))
            ) : (
              <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                {conceptDetail.processCategory || '표준 공정 분류'}
              </span>
            )}
          </div>
        </div>

        {/* 2. 상위 구성 (part_of) */}
        <div style={{ background: 'var(--bg-surface-2)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.6875rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
            상위 구성 모듈 (part_of)
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {partOfList.length > 0 ? (
              partOfList.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => item.id && onSelectConcept && onSelectConcept(item.id)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-surface)',
                    color: item.id ? 'var(--accent-primary)' : 'var(--text-primary)',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    cursor: item.id ? 'pointer' : 'default',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <span>{item.name || item.title || item.id}</span>
                  {item.id && <ArrowUpRight size={12} />}
                </button>
              ))
            ) : (
              <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                패키징 라인 제조 모듈
              </span>
            )}
          </div>
        </div>

        {/* 3. 다음 연계 공정 (next_step) */}
        <div style={{ background: 'var(--bg-surface-2)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.6875rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
            다음 연계 단계 (next_step)
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {nextStepList.length > 0 ? (
              nextStepList.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => item.id && onSelectConcept && onSelectConcept(item.id)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '6px',
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-surface)',
                    color: item.id ? 'var(--accent-primary)' : 'var(--text-primary)',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    cursor: item.id ? 'pointer' : 'default',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <span>{item.name || item.title || item.id}</span>
                  {item.id && <ArrowRight size={12} />}
                </button>
              ))
            ) : (
              <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                품질 검사 및 신뢰성 평가
              </span>
            )}
          </div>
        </div>

        {/* 4. 대안 및 경쟁 기술 (alternative_to) */}
        <div style={{ background: 'var(--bg-surface-2)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.6875rem', fontWeight: 800, color: 'var(--accent-primary)', textTransform: 'uppercase', marginBottom: '8px' }}>
            기술 대안 (alternative_to)
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {altList.length > 0 ? (
              altList.map((item, idx) => (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  <button
                    type="button"
                    onClick={() => item.targetId && onSelectConcept && onSelectConcept(item.targetId)}
                    style={{
                      padding: '4px 8px',
                      borderRadius: '4px',
                      border: '1px solid var(--accent-primary)',
                      background: 'var(--accent-primary-light)',
                      color: 'var(--accent-primary)',
                      fontSize: '0.8125rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <span>대안: {item.targetName || item.targetId}</span>
                    <ArrowRight size={12} />
                  </button>
                  {item.commonGoal && (
                    <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', paddingLeft: '2px' }}>
                      목표: {item.commonGoal}
                    </span>
                  )}
                </div>
              ))
            ) : (
              <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                등록된 직접 대안 없음
              </span>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}
