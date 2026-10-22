/**
 * [계층 1] EvidenceFeedList View (Pure Dumb UI Component)
 * - 화면 2단계: Deep Research Agent가 발굴한 공인 문헌 피드 목록 및 종합 분석 선택 바
 */

import React from 'react';
import { BookOpen, ExternalLink, CheckSquare, Square, Layers, ArrowRight, Quote } from 'lucide-react';
import { researchFormatterService } from '../../services/researchFormatterService';

export function EvidenceFeedList({
  evidenceFeed = [],
  selectedEvidenceIds = [],
  searchTopic = '',
  isSynthesizing = false,
  onToggleEvidence,
  onSelectAll,
  onSynthesize,
  onBackToSearch
}) {
  const allSelected = evidenceFeed.length > 0 && selectedEvidenceIds.length === evidenceFeed.length;

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
      {/* 헤더 바 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingBottom: '16px',
          borderBottom: '1px solid var(--border-color)',
          flexWrap: 'wrap',
          gap: '12px'
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={18} style={{ color: 'var(--accent-primary)' }} />
            <h3 style={{ fontSize: '1.125rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
              문헌 검색 결과 (Evidence Feed)
            </h3>
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
              {evidenceFeed.length}건 발굴
            </span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            조사 주제: <strong>{searchTopic}</strong>
          </div>
        </div>

        {/* 상단 컨트롤 버튼 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            type="button"
            onClick={onSelectAll}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface-2)',
              color: 'var(--text-secondary)',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            {allSelected ? <CheckSquare size={14} /> : <Square size={14} />}
            <span>{allSelected ? '선택 해제' : '전체 선택'}</span>
          </button>

          <button
            type="button"
            onClick={onBackToSearch}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface)',
              color: 'var(--text-muted)',
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            주제 다시 검색
          </button>
        </div>
      </div>

      {/* 문헌 카드 목록 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {evidenceFeed.length === 0 && <p role="status">관련 문헌을 찾지 못했습니다. 검색어나 기관 필터를 바꿔 다시 조사해 주세요.</p>}
        {evidenceFeed.map((item) => {
          const isChecked = selectedEvidenceIds.includes(item.id);
          const tierMeta = researchFormatterService.getCredibilityMeta(item.credibilityTier);
          const typeLabel = researchFormatterService.getSourceTypeLabel(item.sourceType);
          const relMeta = researchFormatterService.getRelevanceMeta(item.relevanceScore);

          return (
            <div
              key={item.id}
              style={{
                borderRadius: '10px',
                border: isChecked ? '1px solid var(--accent-primary)' : '1px solid var(--border-color)',
                background: isChecked ? 'var(--accent-primary-light, rgba(37,99,235,0.02))' : 'var(--bg-surface-2)',
                padding: '16px 20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                transition: 'all 0.15s ease'
              }}
            >
              {/* 상단 메타 바 */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <input
                    type="checkbox"
                    aria-label={`${item.sourceName} 선택`}
                    checked={isChecked}
                    onChange={() => onToggleEvidence(item.id)}
                    style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                  />

                  {/* 출처 ID 배지 */}
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.75rem',
                      fontWeight: 800,
                      color: 'var(--accent-primary)',
                      background: 'var(--bg-surface)',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      border: '1px solid var(--border-color)'
                    }}
                  >
                    [{item.id}]
                  </span>

                  {/* 신뢰도 티어 배지 */}
                  <span
                    style={{
                      fontSize: '0.6875rem',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '4px',
                      color: tierMeta.color,
                      background: tierMeta.bg,
                      border: tierMeta.border
                    }}
                  >
                    {tierMeta.label}
                  </span>

                  {/* 출처 유형 라벨 */}
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {typeLabel} · {item.retrievalStatus === 'metadata' ? '서지정보만 확보' : item.retrievalStatus === 'abstract' ? '초록 확보' : ['source_excerpt', 'registered_excerpt'].includes(item.retrievalStatus) ? '원문 발췌 확보' : '확보 상태 미확인'}
                  </span>
                </div>

                {/* 적합도 점수 */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>검색 일치도:</span>
                  <span style={{ fontSize: '0.8125rem', fontWeight: 800, color: relMeta.color }}>
                    {relMeta.percentText}
                  </span>
                </div>
              </div>

              {/* 문헌 제목 및 발행처 */}
              <div>
                <h4 style={{ margin: '0 0 4px 0', fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {item.sourceName}
                </h4>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {item.publisher} • {item.publishedDate}
                </div>
              </div>

              {/* 핵심 인용 및 실측 데이터 박스 */}
              <div
                style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '6px',
                  padding: '12px 14px',
                  fontSize: '0.8125rem',
                  lineHeight: 1.6,
                  color: 'var(--text-primary)',
                  position: 'relative'
                }}
              >
                <div style={{ display: 'flex', gap: '8px' }}>
                  <Quote size={16} style={{ color: 'var(--accent-primary)', flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <div style={{ fontStyle: 'italic', whiteSpace: 'pre-wrap' }}>{item.quote ? `“${item.quote}”` : '내용을 아직 확보하지 못했습니다. 출판사 링크에서 확인해 주세요.'}</div>
                    {item.sectionContext && (
                      <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                        📍 {item.sectionContext}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* 원문 링크 */}
              {item.externalUrl && (
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <a
                    href={item.externalUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      color: 'var(--accent-primary)',
                      textDecoration: 'none',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <span>{item.urlLabel || '공인 원문 보기'}</span>
                    <ExternalLink size={12} />
                  </a>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 하단 CTA 액션 바 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingTop: '16px',
          borderTop: '1px solid var(--border-color)',
          flexWrap: 'wrap',
          gap: '12px'
        }}
      >
        <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
          선택된 문헌: <strong style={{ color: 'var(--accent-primary)' }}>{selectedEvidenceIds.length}</strong> / {evidenceFeed.length}건
        </div>

        <button
          type="button"
          onClick={onSynthesize}
          disabled={isSynthesizing || selectedEvidenceIds.length === 0}
          style={{
            padding: '12px 24px',
            borderRadius: '8px',
            border: 'none',
            background: isSynthesizing || selectedEvidenceIds.length === 0 ? 'var(--text-muted)' : 'var(--accent-primary)',
            color: '#fff',
            fontSize: '0.875rem',
            fontWeight: 700,
            cursor: isSynthesizing || selectedEvidenceIds.length === 0 ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          {isSynthesizing ? (
            <span>문헌 교차 분석 및 리포트 합성 중...</span>
          ) : (
            <>
              <span>📊 이 문헌들로 종합 분석 리포트 생성 (리포트 보기 ➔)</span>
              <ArrowRight size={16} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
