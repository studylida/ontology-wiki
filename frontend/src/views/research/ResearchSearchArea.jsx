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

const AVAILABLE_INSTITUTIONS = [
  'Intel Foundry',
  'IEEE ECTC',
  'SEMI 3D Packaging',
  'Samsung Tech Day',
  'TSMC OIP'
];

export function ResearchSearchArea({
  searchTopic = '',
  targetInstitutions = [],
  isDiscovering = false,
  onChangeSearchTopic,
  onToggleInstitution,
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
            글로벌 공인 문헌·백서 Deep Research 조사실
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
              <span>공인 문헌 발굴 시작</span>
              <ArrowRight size={16} />
            </>
          )}
        </button>
      </form>

      {/* 추천 반도체 주제 칩 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
          추천 조사 주제:
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

      {/* 5대 공인 발행 기관 필터 체크 */}
      <div style={{ paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
          <Building2 size={16} style={{ color: 'var(--accent-primary)' }} />
          <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            타깃 공인 발행 기관 코퍼스 필터
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {AVAILABLE_INSTITUTIONS.map((inst) => {
            const isChecked = targetInstitutions.includes(inst);
            return (
              <label
                key={inst}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  border: isChecked ? '1px solid var(--accent-primary)' : '1px solid var(--border-color)',
                  background: isChecked ? 'var(--accent-primary-light)' : 'var(--bg-surface-2)',
                  color: isChecked ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  fontSize: '0.75rem',
                  fontWeight: isChecked ? 700 : 500,
                  cursor: 'pointer',
                  userSelect: 'none',
                  transition: 'all 0.15s ease'
                }}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => onToggleInstitution(inst)}
                  style={{ cursor: 'pointer' }}
                />
                <span>{inst}</span>
              </label>
            );
          })}
        </div>
      </div>
    </div>
  );
}
