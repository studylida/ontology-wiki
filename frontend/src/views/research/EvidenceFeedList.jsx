/**
 * [계층 1] EvidenceFeedList View (Pure Dumb UI Component)
 * - 화면 2단계: Deep Research Agent가 발굴한 공인 문헌 피드 목록 및 종합 분석 선택 바
 */

import React from 'react';
import { usableEvidenceIds, evidenceState, safeSourceUrl } from '../../services/researchService';
import { BookOpen, ExternalLink, CheckSquare, Square, Layers, ArrowRight, Quote } from 'lucide-react';
import { researchFormatterService } from '../../services/researchFormatterService';

export function EvidenceFeedList({
  evidenceFeed = [],
  displayedEvidence = evidenceFeed,
  evidenceCounts = {},
  evidenceFilter = 'all',
  onFilter,
  onShowMore,
  isDiscovering = false,
  selectedEvidenceIds = [],
  searchTopic = '',
  isSynthesizing = false,
  onToggleEvidence,
  onSelectAll,
  onSynthesize,
  onBackToSearch
}) {
  const eligibleIds = usableEvidenceIds(evidenceFeed, evidenceFeed.map((e) => e.id));
  const allSelected = eligibleIds.length > 0 && eligibleIds.every((id) => selectedEvidenceIds.includes(id));

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
              문헌 조사 결과
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
            disabled={isDiscovering}
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

      <div aria-label="문헌 처리 상태">
        <label htmlFor="research-evidence-state">상태별 문헌 </label>
        <select id="research-evidence-state" value={evidenceFilter} onChange={(event) => onFilter?.(event.target.value)}>
          <option value="all">전체 ({evidenceFeed.length})</option>
          {['included', 'content_unavailable', 'insufficient_content', 'not_assessed', 'assessment_failed', 'excluded', 'unverified'].map((state) =>
            <option key={state} value={state}>{researchFormatterService.getResearchStateLabel(state)} ({evidenceCounts[state] || 0})</option>)}
        </select>
        <p>{Object.entries(evidenceCounts).map(([state, count]) => `${researchFormatterService.getResearchStateLabel(state)} ${count}건`).join(' · ')}</p>
      </div>

      {/* 문헌 카드 목록 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {evidenceFeed.length === 0 && <p role="status">관련 문헌을 찾지 못했습니다. 검색어나 기관 필터를 바꿔 다시 조사해 주세요.</p>}
        {displayedEvidence.map((item) => {
          const isChecked = selectedEvidenceIds.includes(item.id);
          const tierMeta = researchFormatterService.getCredibilityMeta(item.credibilityTier);
          const typeLabel = researchFormatterService.getSourceTypeLabel(item.sourceType);
          const assessment = item.assessment;

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
                    disabled={isDiscovering || !eligibleIds.includes(item.id)}
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
                    {typeLabel} · {item.retrievalStatus === 'metadata' ? '서지정보만 확보' : item.retrievalStatus === 'abstract' ? '초록 확보' : item.retrievalStatus === 'external_excerpt' ? '공개 원문 일부 확보' : ['source_excerpt', 'registered_excerpt'].includes(item.retrievalStatus) ? '원문 발췌 확보' : '확보 상태 미확인'}
                  </span>
                </div>

                {/* 적합도 점수 */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>관련성 판단:</span>
                  <span style={{ fontSize: '0.8125rem', fontWeight: 800, color: 'var(--text-secondary)' }}>
                    {researchFormatterService.getResearchStateLabel(evidenceState(item))}
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

              {item.assessmentCurrent === false && <p role="status">{researchFormatterService.getResearchStateLabel(evidenceState(item))} · 최신 확보 구간의 평가가 완료되면 선택할 수 있습니다.</p>}
              {assessment && item.assessmentCurrent !== false && <div aria-label="문헌 관련성 설명" style={{ lineHeight: 1.7 }}>
                <p><strong>어떤 문헌인가요?</strong> {assessment.documentSummary}</p>
                <p><strong>{assessment.decision === 'included' ? '왜 이번 조사에 포함했나요?' : '왜 보류·제외했나요?'}</strong> {assessment.inclusionReason}</p>
                {assessment.usefulness && <p><strong>무엇을 알아볼 수 있나요?</strong> {assessment.usefulness}</p>}
                {assessment.limitations?.map((text, i) => <p key={i}><strong>적용 한계·미확인:</strong> {text}</p>)}
                <p>{assessment.evidenceReferences?.length ? '위 설명은 확보한 내용에 대한 AI의 판단입니다.' : '확보 범위와 판단 상태를 확인해 주세요.'}</p>
                {assessment.evidenceReferences?.length > 0 && <details>
                  <summary>판단에 사용한 근거 구절 보기</summary>
                  {item.readSegments?.filter((segment) => assessment.evidenceReferences.includes(segment.id)).map((segment) =>
                    <blockquote key={segment.id} style={{ whiteSpace: 'pre-wrap' }}>{segment.text}<footer>{segment.sectionContext}</footer></blockquote>)}
                </details>}
              </div>}
              {item.assessmentCurrent === false && assessment?.evidenceReferences?.length > 0 && <details><summary>이전 확보 구간의 평가 보기</summary><p>{assessment.inclusionReason}</p></details>}
              {item.acquisitionAttempts?.length > 0 && <details><summary>내용 확보 기록 ({item.acquisitionAttempts.length})</summary>
                {item.acquisitionAttempts.map((attempt, index) => <p key={index}>{safeSourceUrl(attempt.resolvedUrl || attempt.url) ? <a href={safeSourceUrl(attempt.resolvedUrl || attempt.url)} target="_blank" rel="noopener noreferrer">조회한 출처</a> : '주소 확인 불가'} · {researchFormatterService.getAcquisitionLabel(attempt.outcome)} · {attempt.at}</p>)}
              </details>}
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
              {safeSourceUrl(item.externalUrl) && (
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <a
                    href={safeSourceUrl(item.externalUrl)}
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
                    <span>{item.urlLabel || '출처 링크 확인'}</span>
                    <ExternalLink size={12} />
                  </a>
                </div>
              )}
            </div>
          );
        })}
      </div>
      {displayedEvidence.length < (evidenceFilter === 'all' ? evidenceFeed.length : evidenceCounts[evidenceFilter] || 0) && <button type="button" onClick={onShowMore}>문헌 더 보기</button>}

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
          disabled={isDiscovering || isSynthesizing || selectedEvidenceIds.length === 0}
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
