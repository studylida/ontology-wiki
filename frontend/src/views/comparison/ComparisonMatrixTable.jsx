/**
 * [계층 1] ComparisonMatrixTable View (Pure Dumb UI Component)
 * - 화면 2-B 중앙: 4단계 다차원 심층 인과 비교 매트릭스
 * - 카테고리 축 필터링 & 온디맨드 지식 갭(Knowledge Gap) 팝오버 트리거
 */

import React from 'react';
import { Layers, AlertTriangle, BookCheck, Sparkles, Filter } from 'lucide-react';
import { matrixHighlightService } from '../../services/matrixHighlightService';
import {evidenceHref, openEvidence} from './ComparisonMarkdown';

export function ComparisonMatrixTable({
  matrixRows = [],
  categories = [{ id: 'all', label: '전체 축' }],
  selectedCategory,
  targetAName = 'Target A',
  targetBName = 'Target B',
  isLoading,
  onSelectCategory,
  onOpenGapPopover
}) {
  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '24px',
        marginBottom: '20px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
      }}
    >
      {/* ── 카테고리 축 필터 탭 바 ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={18} style={{ color: 'var(--accent-primary)' }} />
          <h3 style={{ fontSize: '1rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
            목적별 비교와 근거
          </h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            현재 {matrixRows.length}개 항목
          </span>
        </div>

        {/* 축 필터 슬라이딩 탭 */}
        <div className="sliding-tabs-container" style={{ padding: '2px' }}>
          {categories.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`sliding-tab-item ${selectedCategory === tab.id ? 'active' : ''}`}
              style={{ padding: '4px 10px', fontSize: '0.75rem' }}
              onClick={() => onSelectCategory(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── 매트릭스 테이블 ── */}
      <div style={{ overflowX: 'auto' }}>
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: '0.8125rem',
            textAlign: 'left'
          }}
        >
          <thead>
            <tr style={{ borderBottom: '2px solid var(--border-color)', background: 'var(--bg-surface-2)', color: 'var(--text-secondary)' }}>
              <th style={{ padding: '12px 14px', width: '25%', fontWeight: 700 }}>비교 평가 축 (Parameter Axis)</th>
              <th style={{ padding: '12px 14px', width: '15%', fontWeight: 700 }}>분류 카테고리</th>
              <th style={{ padding: '12px 14px', width: '30%', fontWeight: 700, color: 'var(--accent-primary)' }}>
                {targetAName}
              </th>
              <th style={{ padding: '12px 14px', width: '30%', fontWeight: 700, color: 'var(--accent-primary)' }}>
                {targetBName}
              </th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={4} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  다차원 매트릭스 수치 및 지식 갭을 계산 중입니다...
                </td>
              </tr>
            ) : matrixRows.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  해당 카테고리의 비교 축이 없습니다.
                </td>
              </tr>
            ) : (
              matrixRows.map((row, idx) => {
                const catMeta = matrixHighlightService.getCategoryMeta(row.axisCategory);
                const isGapA = matrixHighlightService.isGapValue(row.valA);
                const isGapB = matrixHighlightService.isGapValue(row.valB);

                return (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: '1px solid var(--border-color)',
                      transition: 'background 0.15s ease'
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-surface-2)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    {/* 축 명칭 */}
                    <td style={{ padding: '12px 14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {row.axis}
                      {row.basis && <small style={{ display: 'block', fontWeight: 400 }}>{row.basis}</small>}
                    </td>

                    {/* 카테고리 배지 */}
                    <td style={{ padding: '12px 14px' }}>
                      <span
                        style={{
                          fontSize: '0.6875rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background: catMeta.bg,
                          color: catMeta.color
                        }}
                      >
                        {row.categoryLabel || catMeta.label}
                      </span>
                    </td>

                    {/* Target A 값 */}
                    <td style={{ padding: '12px 14px' }}>
                      {isGapA ? (
                        <button
                          type="button"
                          onClick={() => onOpenGapPopover(row, 'A')}
                          style={{
                            padding: '3px 8px',
                            borderRadius: '4px',
                            border: '1px dashed var(--accent-warning)',
                            background: 'var(--accent-warning-light)',
                            color: 'var(--accent-warning)',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            cursor: 'pointer',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}
                          title="클릭하여 지식 갭 상세 확인 및 외부 문헌 조사(Tab 4) 연계"
                        >
                          <AlertTriangle size={12} />
                          <span>{row.valA === '공개 근거 미확인' ? '공개 근거 미확인' : '미등록 데이터 (Gap)'}</span>
                        </button>
                      ) : (
                        <div>
                          <span style={{ fontWeight: row.axisCategory === 'purpose' ? 400 : 600, color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
                            {row.valA}
                          </span>
                          {row.evidenceA && (
                            <span style={{ marginLeft: '6px', fontSize: '0.6875rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
                              {(row.evidenceIdsA?.length ? row.evidenceIdsA : [row.evidenceA]).map(id => <a key={id} href={evidenceHref(id)} onClick={event => openEvidence(event, id)}>[{id}] </a>)}
                            </span>
                          )}
                        </div>
                      )}
                    </td>

                    {/* Target B 값 */}
                    <td style={{ padding: '12px 14px' }}>
                      {isGapB ? (
                        <button
                          type="button"
                          onClick={() => onOpenGapPopover(row, 'B')}
                          style={{
                            padding: '3px 8px',
                            borderRadius: '4px',
                            border: '1px dashed var(--accent-warning)',
                            background: 'var(--accent-warning-light)',
                            color: 'var(--accent-warning)',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            cursor: 'pointer',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}
                          title="클릭하여 지식 갭 상세 확인 및 외부 문헌 조사(Tab 4) 연계"
                        >
                          <AlertTriangle size={12} />
                          <span>{row.valB === '공개 근거 미확인' ? '공개 근거 미확인' : '미등록 데이터 (Gap)'}</span>
                        </button>
                      ) : (
                        <div>
                          <span style={{ fontWeight: row.axisCategory === 'purpose' ? 400 : 600, color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
                            {row.valB}
                          </span>
                          {row.evidenceB && (
                            <span style={{ marginLeft: '6px', fontSize: '0.6875rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
                              {(row.evidenceIdsB?.length ? row.evidenceIdsB : [row.evidenceB]).map(id => <a key={id} href={evidenceHref(id)} onClick={event => openEvidence(event, id)}>[{id}] </a>)}
                            </span>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
