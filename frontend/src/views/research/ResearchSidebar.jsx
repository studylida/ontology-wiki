/**
 * [계층 1] ResearchSidebar View (Pure Dumb UI Component)
 * - 외부 문헌 조사실 좌측: 날짜별 과거 조사 세션 히스토리 목록 및 [+ 새 문헌 조사] 액션
 */

import React from 'react';
import { History, Plus, BookOpen, Clock, ChevronRight } from 'lucide-react';

export function ResearchSidebar({
  pastSessions = [],
  currentSessionId,
  isLoading,
  onSelectSession,
  onNewSearch
}) {
  return (
    <aside
      style={{
        width: '280px',
        flexShrink: 0,
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
      }}
    >
      {/* 새 조사 시작 버튼 */}
      <button
        type="button"
        onClick={onNewSearch}
        style={{
          width: '100%',
          padding: '10px 14px',
          borderRadius: '8px',
          border: '1px solid var(--accent-primary)',
          background: 'var(--accent-primary-light)',
          color: 'var(--accent-primary)',
          fontSize: '0.8125rem',
          fontWeight: 700,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '6px',
          transition: 'all 0.15s ease'
        }}
      >
        <Plus size={16} />
        <span>새 문헌 조사 시작</span>
      </button>

      {/* 헤더 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '0 4px' }}>
        <History size={16} style={{ color: 'var(--text-muted)' }} />
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
          과거 조사 세션 이력 ({pastSessions.length})
        </span>
      </div>

      {/* 세션 리스트 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', overflowY: 'auto', flex: 1, maxHeight: '680px' }}>
        {isLoading ? (
          <div style={{ padding: '24px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
            조사 이력을 불러오는 중...
          </div>
        ) : pastSessions.length === 0 ? (
          <div style={{ padding: '24px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
            과거 조사 세션이 없습니다.
          </div>
        ) : (
          pastSessions.map((session) => {
            const isSelected = session.id === currentSessionId;
            const dateStr = session.createdAt ? new Date(session.createdAt).toLocaleDateString() : '';

            return (
              <div
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  border: isSelected ? '1px solid var(--accent-primary)' : '1px solid transparent',
                  background: isSelected ? 'var(--accent-primary-light)' : 'var(--bg-surface-2)',
                  transition: 'all 0.15s ease',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px'
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) e.currentTarget.style.background = 'var(--bg-surface-hover, rgba(0,0,0,0.04))';
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) e.currentTarget.style.background = 'var(--bg-surface-2)';
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div
                    style={{
                      fontSize: '0.8125rem',
                      fontWeight: isSelected ? 800 : 600,
                      color: isSelected ? 'var(--accent-primary)' : 'var(--text-primary)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      maxWidth: '190px'
                    }}
                    title={session.searchTopic}
                  >
                    {session.searchTopic}
                  </div>
                  <ChevronRight size={14} style={{ color: isSelected ? 'var(--accent-primary)' : 'var(--text-muted)' }} />
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                  <span>문헌 {session.evidenceCount}건</span>
                  <span>•</span>
                  <span>후보 {session.candidateCount}건</span>
                  {dateStr && (
                    <>
                      <span>•</span>
                      <span>{dateStr}</span>
                    </>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
