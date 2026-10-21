/**
 * [계층 1] PresenceBanner View (Pure Dumb UI Component)
 * - 10분 편집 점유 락(Presence Lock) 실시간 카운트다운 타이머
 * - [⚡ 편집 세션 인계받기] 및 감사 로그 조회 트리거
 */

import React from 'react';
import { Lock, Unlock, Clock, Zap, History, PlusCircle, ShieldCheck } from 'lucide-react';

export function PresenceBanner({
  presenceLock,
  isEditorDisabled,
  currentUser,
  ticketStatus,
  onTakeoverLock,
  onOpenAuditModal,
  onOpenNewConceptModal
}) {
  const { isLocked, holder, isHeldByMe, remainingSeconds } = presenceLock;

  // 초 단위를 MM:SS 포맷으로 변환
  const formatTime = (secs) => {
    const m = Math.floor(Math.max(0, secs) / 60);
    const s = Math.max(0, secs) % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  const isWarning = remainingSeconds <= 60 && remainingSeconds > 0;
  const isPending = ticketStatus === 'pending';

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '14px 20px',
        marginBottom: '16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
      }}
    >
      {/* ── 좌측: 락 상태 및 실시간 카운트다운 ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* 락 아이콘 & 상태 텍스트 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isHeldByMe ? (
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: isWarning ? 'var(--accent-warning-light)' : 'var(--accent-success-light)',
                color: isWarning ? 'var(--accent-warning)' : 'var(--accent-success)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Unlock size={16} />
            </div>
          ) : (
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'var(--bg-surface-3)',
                color: 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Lock size={16} />
            </div>
          )}

          <div>
            <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {isHeldByMe
                ? '내 편집 세션 활성화됨 (동시 편집 락 점유 중)'
                : isLocked
                ? `동시 편집 락 점유 중: ${holder}`
                : isPending
                ? '편집 락 비점유 (자유 편집 가능)'
                : '심사 완료 티켓 (읽기 전용)'}
            </div>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
              10분 독점 방지 가드레일 (Presence Lock 600s Auto-Expire)
            </div>
          </div>
        </div>

        {/* ⏳ 실시간 10분 카운트다운 타이머 배지 */}
        {isHeldByMe && (
          <div
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              background: isWarning ? 'var(--accent-danger-light)' : 'var(--bg-surface-2)',
              border: `1px solid ${isWarning ? 'var(--accent-danger)' : 'var(--border-color)'}`,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.875rem',
              fontWeight: 700,
              color: isWarning ? 'var(--accent-danger)' : 'var(--text-primary)'
            }}
          >
            <Clock size={15} style={{ color: isWarning ? 'var(--accent-danger)' : 'var(--accent-primary)' }} />
            <span>남은 시간: {formatTime(remainingSeconds)}</span>
          </div>
        )}

        {/* 타인 점유 중이거나 만료 시 세션 인계받기 버튼 */}
        {!isHeldByMe && isPending && (
          <button
            type="button"
            onClick={onTakeoverLock}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid var(--accent-warning)',
              background: 'var(--accent-warning-light)',
              color: 'var(--accent-warning)',
              fontSize: '0.75rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <Zap size={13} />
            <span>⚡ 편집 세션 인계받기</span>
          </button>
        )}
      </div>

      {/* ── 우측: 감사 로그 & 신규 발의 모달 액션 ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <button
          type="button"
          onClick={onOpenAuditModal}
          style={{
            padding: '6px 12px',
            borderRadius: '6px',
            border: '1px solid var(--border-color)',
            background: 'var(--bg-surface-2)',
            fontSize: '0.8125rem',
            fontWeight: 600,
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <History size={14} />
          <span>감사 로그 📜</span>
        </button>

        <button
          type="button"
          onClick={onOpenNewConceptModal}
          style={{
            padding: '6px 12px',
            borderRadius: '6px',
            border: '1px solid var(--accent-primary)',
            background: 'var(--accent-primary-light)',
            color: 'var(--accent-primary)',
            fontSize: '0.8125rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <PlusCircle size={14} />
          <span>+ 새 문서 추가 발의</span>
        </button>
      </div>
    </div>
  );
}
