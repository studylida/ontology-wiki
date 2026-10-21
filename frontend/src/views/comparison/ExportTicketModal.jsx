/**
 * [계층 1] ExportTicketModal View (Pure Dumb UI Component)
 * - 화면 2-B: 비교 분석 및 튜닝 결과를 검토 승인 센터(Tab 3)의 개정안 티켓으로 내보내는 모달
 * - transitions.dev 기반 모달 스타일 및 네이티브 <dialog closedby="any"> 패턴
 */

import React, { useEffect, useRef, useState } from 'react';
import { ArrowRight, FileCheck, X, AlertCircle } from 'lucide-react';

export function ExportTicketModal({
  isOpen,
  currentSession,
  currentUser,
  isLoading,
  onClose,
  onSubmit
}) {
  const dialogRef = useRef(null);

  const [title, setTitle] = useState('');
  const [reviewType, setReviewType] = useState('minor_revision');
  const [overrideReason, setOverrideReason] = useState('비교 매트릭스 다차원 분석 및 엔지니어링 조건 검토에 따른 개정 발의');

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      if (!dialog.open) {
        dialog.showModal();
      }
      // 기본 타이틀 채우기
      if (currentSession) {
        setTitle(`${currentSession.title} 비교 분석 결과 개정안`);
      }
    } else {
      if (dialog.open) {
        dialog.close();
      }
    }
  }, [isOpen, currentSession]);

  const handleBackdropClick = (e) => {
    if (e.target === dialogRef.current) {
      onClose();
    }
  };

  const handleSubmitForm = (e) => {
    e.preventDefault();
    if (!title.trim() || isLoading) return;

    onSubmit({
      title: title.trim(),
      reviewType,
      overrideReason: overrideReason.trim()
    });
  };

  if (!isOpen) return null;

  return (
    <dialog
      ref={dialogRef}
      closedby="any"
      onClick={handleBackdropClick}
      onClose={onClose}
      className="modal-box"
      style={{
        maxWidth: '560px',
        width: '90%',
        padding: '0',
        borderRadius: '12px',
        border: '1px solid var(--border-color)',
        background: 'var(--bg-surface)',
        boxShadow: '0 12px 36px rgba(0, 0, 0, 0.25)',
        color: 'var(--text-primary)'
      }}
    >
      {/* 헤더 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-color)',
          background: 'var(--bg-surface-2)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileCheck size={18} style={{ color: 'var(--accent-primary)' }} />
          <h4 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 800 }}>
            검토 승인 센터(Tab 3)로 티켓 내보내기
          </h4>
        </div>
        <button
          type="button"
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--text-muted)',
            padding: '4px'
          }}
        >
          <X size={18} />
        </button>
      </div>

      {/* 본문 폼 */}
      <form onSubmit={handleSubmitForm}>
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div
            style={{
              padding: '10px 14px',
              borderRadius: '8px',
              background: 'var(--bg-surface-2)',
              border: '1px solid var(--border-color)',
              fontSize: '0.75rem',
              color: 'var(--text-secondary)'
            }}
          >
            <div>
              <strong>비교 세션:</strong> {currentSession?.title}
            </div>
            <div style={{ marginTop: '2px' }}>
              <strong>대상 컨셉:</strong> {currentSession?.contextParams?.targetA || 'concept-tcb'} vs{' '}
              {currentSession?.contextParams?.targetB || 'concept-mrmuf'}
            </div>
          </div>

          {/* 티켓 제목 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
              개정 티켓 제목 *
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="예: [TCB vs MR-MUF] 140N 가압 조건 비교 기반 공정 가이드 개정안"
              style={{
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface)',
                color: 'var(--text-primary)',
                fontSize: '0.8125rem'
              }}
            />
          </div>

          {/* 개정 유형 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
              개정 유형 (Review Type)
            </label>
            <select
              value={reviewType}
              onChange={(e) => setReviewType(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface)',
                color: 'var(--text-primary)',
                fontSize: '0.8125rem'
              }}
            >
              <option value="minor_revision">MINOR: 수치 파라미터 / 안전 마진 보정 (추천)</option>
              <option value="patch">PATCH: 오탈자 / 출처 보완</option>
              <option value="major_revision">MAJOR: 신규 공정 도입 / 인과 메커니즘 전면 변경</option>
            </select>
          </div>

          {/* 작성자 정보 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
              발행 작성자
            </label>
            <input
              type="text"
              readOnly
              value={`${currentUser?.name || '현장 엔지니어'} (${currentUser?.role || 'Guest'})`}
              style={{
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface-2)',
                color: 'var(--text-muted)',
                fontSize: '0.8125rem'
              }}
            />
          </div>

          {/* 물리 예외 사유 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
              물리 예외 및 개정 사유 (Override Reason, 선택 사항)
            </label>
            <textarea
              rows={3}
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              placeholder="표준 안전 마진 이탈 또는 추가 연구 결과에 따른 개정 근거를 기술하세요."
              style={{
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface)',
                color: 'var(--text-primary)',
                fontSize: '0.8125rem',
                resize: 'vertical'
              }}
            />
          </div>
        </div>

        {/* 풋터 액션 바 */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: '10px',
            padding: '14px 20px',
            borderTop: '1px solid var(--border-color)',
            background: 'var(--bg-surface-2)'
          }}
        >
          <button
            type="button"
            disabled={isLoading}
            onClick={onClose}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-surface)',
              color: 'var(--text-secondary)',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: isLoading ? 'not-allowed' : 'pointer'
            }}
          >
            취소
          </button>
          <button
            type="submit"
            disabled={isLoading || !title.trim()}
            style={{
              padding: '8px 18px',
              borderRadius: '6px',
              border: 'none',
              background: isLoading || !title.trim() ? 'var(--text-muted)' : 'var(--accent-primary)',
              color: '#fff',
              fontSize: '0.8125rem',
              fontWeight: 700,
              cursor: isLoading || !title.trim() ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            {isLoading ? (
              <span>발행 중...</span>
            ) : (
              <>
                <span>티켓 생성 및 발행</span>
                <ArrowRight size={14} />
              </>
            )}
          </button>
        </div>
      </form>
    </dialog>
  );
}
