/**
 * [계층 1] TwoSegmentEditor View (Pure Dumb UI Component)
 * - 2-Segment 개정 초안 에디터 (좌: 기준 초안 / 우: 전문가 직접 편집기)
 * - 10분 잠금 시 Read-only 전환 및 툴바 액션
 */

import React from 'react';
import { Save, Eye, CheckCircle2, XCircle, Lock, Sparkles } from 'lucide-react';

export function TwoSegmentEditor({
  currentTicket,
  workingDraft,
  isEditorDisabled,
  isActionLoading,
  onDraftChange,
  onSaveDraft,
  onOpenWikiPreview,
  onOpenApproveModal,
  onOpenRejectModal
}) {
  if (!currentTicket) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
        좌측 큐에서 검토할 티켓을 선택해 주세요.
      </div>
    );
  }

  const isPending = currentTicket.status === 'pending';
  const baselineContent = currentTicket.currentContent || currentTicket.aiMergedDraft || '등록된 이전 판본이 없습니다.';

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '16px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)'
      }}
    >
      {/* ── 에디터 상단 티켓 타이틀 & 의결 버튼 바 ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontSize: '0.6875rem',
                fontWeight: 700,
                padding: '2px 6px',
                borderRadius: '4px',
                background: 'var(--bg-surface-2)',
                color: 'var(--accent-primary)',
                border: '1px solid var(--border-color)'
              }}
            >
              {currentTicket.reviewType}
            </span>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
              {currentTicket.title}
            </h2>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            대상 개념: <strong>{currentTicket.conceptTitle || currentTicket.conceptId}</strong> | 판본: {currentTicket.currentVersion} ➔ {currentTicket.targetVersion}
          </div>
        </div>

        {/* 심사 의결 액션 버튼 그룹 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            onClick={onOpenWikiPreview}
            disabled={isActionLoading}
            style={{
              padding: '7px 12px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface-2)',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Eye size={14} style={{ color: 'var(--accent-primary)' }} />
            <span>위키 미리보기</span>
          </button>

          {isPending && (
            <>
              <button
                type="button"
                onClick={onSaveDraft}
                disabled={isEditorDisabled || isActionLoading}
                style={{
                  padding: '7px 14px',
                  borderRadius: '6px',
                  border: '1px solid var(--accent-primary)',
                  background: 'var(--accent-primary-light)',
                  color: 'var(--accent-primary)',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  cursor: isEditorDisabled ? 'not-allowed' : 'pointer',
                  opacity: isEditorDisabled ? 0.6 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <Save size={14} />
                <span>초안 저장</span>
              </button>

              <button
                type="button"
                onClick={onOpenRejectModal}
                disabled={isActionLoading}
                style={{
                  padding: '7px 14px',
                  borderRadius: '6px',
                  border: '1px solid var(--accent-danger)',
                  background: 'var(--accent-danger-light)',
                  color: 'var(--accent-danger)',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <XCircle size={14} />
                <span>반려</span>
              </button>

              <button
                type="button"
                onClick={onOpenApproveModal}
                disabled={isActionLoading}
                style={{
                  padding: '7px 16px',
                  borderRadius: '6px',
                  border: 'none',
                  background: 'var(--accent-success)',
                  color: '#ffffff',
                  fontSize: '0.8125rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  boxShadow: '0 2px 6px rgba(16, 185, 129, 0.3)'
                }}
              >
                <CheckCircle2 size={14} />
                <span>최종 승인 의결 ➔</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* ── 2-Segment 스플릿 편집기 ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        {/* 좌측 Segment: 기준 초안 (읽기 전용 베이스라인) */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span>기준 본문 (이전 판본 / AI 합성 초안)</span>
          </div>
          <div
            style={{
              flex: 1,
              height: '380px',
              padding: '14px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface-2)',
              fontSize: '0.8125rem',
              color: 'var(--text-secondary)',
              lineHeight: 1.6,
              overflowY: 'auto',
              whiteSpace: 'pre-wrap',
              fontFamily: 'inherit'
            }}
          >
            {baselineContent}
          </div>
        </div>

        {/* 우측 Segment: 전문가 직접 편집기 */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '6px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span>전문가 직접 수정본 (Working Draft)</span>
            {isEditorDisabled && (
              <span style={{ color: 'var(--accent-danger)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                <Lock size={11} /> 읽기 전용 (락 만료 또는 비인가)
              </span>
            )}
          </div>
          <textarea
            value={workingDraft}
            onChange={(e) => onDraftChange(e.target.value)}
            disabled={isEditorDisabled}
            placeholder="전문가 직접 수정 내용을 입력하세요..."
            style={{
              width: '100%',
              height: '380px',
              padding: '14px',
              borderRadius: '8px',
              border: `1px solid ${isEditorDisabled ? 'var(--border-color)' : 'var(--accent-primary)'}`,
              background: isEditorDisabled ? 'var(--bg-surface-2)' : 'var(--bg-surface)',
              color: 'var(--text-primary)',
              fontSize: '0.8125rem',
              lineHeight: 1.6,
              resize: 'none',
              fontFamily: 'inherit',
              outline: 'none'
            }}
          />
        </div>
      </div>
    </div>
  );
}
