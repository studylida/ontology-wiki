/**
 * [계층 1] ResearchSearchArea View (Pure Dumb UI Component)
 * - 화면 1단계: 외부 문헌 조사 주제 입력, 반도체 추천 키워드 칩 및 5대 공인 발행 기관 필터
 */

import React from 'react';
import { Search, Sparkles, Building2, ArrowRight } from 'lucide-react';

const PRESET_TOPICS = [
  '차세대 유리기판 TGV 공정 및 물성 표준 규격',
  'HBM4 16Hi 하이브리드 본딩 Cu-Cu 직접 접합 물성',
  '3D DRAM 모놀리식 인터커넥트 신뢰성 및 열 저항'
];



export function ResearchSearchArea({
  searchTopic = '',
  institutionQuery = '',
  isDiscovering = false,
  onChangeSearchTopic,
  onChangeInstitutionQuery,
  onDiscover
}) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!searchTopic.trim() || isDiscovering) return;
    onDiscover(searchTopic.trim());
  };

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '28px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
      }}
    >
      {/* 타이틀 및 안내 */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
          <Sparkles size={22} style={{ color: 'var(--accent-primary)' }} />
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
            외부 문헌·백서 조사실
          </h2>
        </div>
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6 }}>
          등록 원문과 Crossref의 논문 서지정보·초록을 검색합니다. 확보한 내용과 적용 조건을 확인해
          비교에 필요한 근거를 보강하세요. 기관을 선택하지 않으면 전체를 조사합니다.
        </p>
      </div>

      {/* 검색 입력 폼 */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '8px' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search
            size={18}
            style={{
              position: 'absolute',
              left: '14px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)'
            }}
          />
          <input
            type="text"
            value={searchTopic}
            onChange={(e) => onChangeSearchTopic(e.target.value)}
            placeholder="조사할 기술 주제를 입력하세요 (예: 차세대 유리기판 TGV 공정 및 물성 표준 규격)"
            style={{
              width: '100%',
              padding: '12px 14px 12px 42px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface-2)',
              color: 'var(--text-primary)',
              fontSize: '0.875rem'
            }}
          />
        </div>

        <button
          type="submit"
          disabled={isDiscovering || !searchTopic.trim()}
          style={{
            padding: '12px 24px',
            borderRadius: '8px',
            border: 'none',
            background: isDiscovering || !searchTopic.trim() ? 'var(--text-muted)' : 'var(--accent-primary)',
            color: '#fff',
            fontSize: '0.875rem',
            fontWeight: 700,
            cursor: isDiscovering || !searchTopic.trim() ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            whiteSpace: 'nowrap'
          }}
        >
          {isDiscovering ? (
            <span>문헌 발굴 중...</span>
          ) : (
            <>
              <span>문헌 검색 시작</span>
              <ArrowRight size={16} />
            </>
          )}
        </button>
      </form>

      {/* 추천 반도체 주제 칩 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
          조사 주제 입력 예시:
        </span>
        {PRESET_TOPICS.map((topic, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => {
              onChangeSearchTopic(topic);
              onDiscover(topic);
            }}
            style={{
              padding: '4px 12px',
              borderRadius: '20px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface-2)',
              color: 'var(--text-secondary)',
              fontSize: '0.75rem',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent-primary)';
              e.currentTarget.style.color = 'var(--accent-primary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-color)';
              e.currentTarget.style.color = 'var(--text-secondary)';
            }}
          >
            {topic}
          </button>
        ))}
      </div>

      <div style={{ paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
        <label htmlFor="research-publisher-filter" style={{ display: 'block', marginBottom: '8px' }}>발행처 키워드 필터 (선택)</label>
        <input id="research-publisher-filter" type="text" value={institutionQuery}
          onChange={(event) => onChangeInstitutionQuery(event.target.value)}
          placeholder="발행처명을 입력하세요. 여러 값은 쉼표로 구분합니다."
          style={{ width: '100%', padding: '10px', border: '1px solid var(--border-color)', borderRadius: '6px', background: 'var(--bg-surface-2)', color: 'var(--text-primary)' }} />
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>자료의 발행처·제목에 입력한 문자열이 포함되는지 확인합니다. 비워두면 전체를 검색하며, 학회·행사 전용 코퍼스 검색을 뜻하지 않습니다.</p>
      </div>
    </div>
  );
}
