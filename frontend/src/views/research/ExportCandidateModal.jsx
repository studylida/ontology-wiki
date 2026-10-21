/**
 * [계층 1] ExportCandidateModal View (Pure Dumb UI Component)
 * - 외부 문헌 조사에서 도출된 지식 후보를 검토 센터(Tab 3)의 ReviewTicket으로 발행하는 모달
 * - transitions.dev 기반 모달 스타일 및 네이티브 <dialog closedby="any"> 패턴
 */

import React, { useEffect, useRef, useState } from 'react';
import { Send, X, FileText, CheckCircle2 } from 'lucide-react';

export function ExportCandidateModal({
  isOpen,
  candidate,
  currentUser,
  isLoading,
  onClose,
  onSubmit
}) {
  const dialogRef = useRef(null);
  const [userNote, setUserNote] = useState('공인 문헌 교차 분석 및 실측 데이터에 기반한 신규 온톨로지 지식 승격 제안');

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      if (!dialog.open) {
        dialog.showModal();
      }
    } else {
      if (dialog.open) {
        dialog.close();
      }
    }
  }, [isOpen]);

  const handleBackdropClick = (e) => {
    if (e.target === dialogRef.current) {
      onClose();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isLoading) return;
    onSubmit({ userNote: userNote.trim() });
  };

  if (!isOpen || !candidate) return null;

  return (
    <dialog
      ref={dialogRef}
      closedby="any"
      onClick={handleBackdropClick}
      onClose={onClose}
      className="modal-box"
      style={{
        maxWidth: '540px',
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
          <FileText size={18} style={{ color: 'var(--accent-primary)' }} />
          <h4 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 800 }}>
            검토 승인 센터(Tab 3)로 티켓 발행
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

      {/* 본문 */}
      <form onSubmit={handleSubmit}>
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* 후보 메타 요약 */}
          <div
            style={{
              padding: '12px 14px',
              borderRadius: '8px',
              background: 'var(--bg-surface-2)',
              border: '1px solid var(--border-color)',
              fontSize: '0.8125rem'
            }}
          >
            <div style={{ fontWeight: 800, color: 'var(--text-primary)', marginBottom: '4px' }}>
              [{candidate.candidateType || '신규 개념'}] {candidate.title}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {candidate.summary}
            </div>
            {candidate.evidenceIds && (
              <div style={{ marginTop: '6px', fontSize: '0.6875rem', color: 'var(--accent-primary)', fontWeight: 700 }}>
                근거 출처: {candidate.evidenceIds.map((e) => `[${e}]`).join(' ')}
              </div>
            )}
          </div>

          {/* 발의자 정보 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
              발의 엔지니어
            </label>
            <input
              type="text"
              readOnly
              value={`${currentUser?.name || '현장 엔지니어'} (${currentUser?.department || '패키징선행개발팀'}, Level ${currentUser?.level || 2})`}
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

          {/* 검토 제안 사유 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
              검토 제안 및 개정 사유 (User Note) *
            </label>
            <textarea
              rows={3}
              required
              value={userNote}
              onChange={(e) => setUserNote(e.target.value)}
              placeholder="검토관이 확인할 수 있도록 신규 지식 발의 배경과 실측 근거를 기재하세요."
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

        {/* 풋터 */}
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
            disabled={isLoading || !userNote.trim()}
            style={{
              padding: '8px 18px',
              borderRadius: '6px',
              border: 'none',
              background: isLoading || !userNote.trim() ? 'var(--text-muted)' : 'var(--accent-primary)',
              color: '#fff',
              fontSize: '0.8125rem',
              fontWeight: 700,
              cursor: isLoading || !userNote.trim() ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            {isLoading ? (
              <span>발행 중...</span>
            ) : (
              <>
                <Send size={14} />
                <span>티켓 생성 및 발행</span>
              </>
            )}
          </button>
        </div>
      </form>
    </dialog>
  );
}
