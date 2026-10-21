/**
 * [계층 1] RejectModal View (Pure Dumb UI Component)
 * - 티켓 반려 의결 모달
 * - Modern Web Guidance: <dialog closedby="any">
 */

import React, { useRef, useEffect, useState } from 'react';
import { XCircle, X } from 'lucide-react';

export function RejectModal({
  isOpen,
  ticketTitle,
  onClose,
  onReject
}) {
  const dialogRef = useRef(null);
  const [rejectReason, setRejectReason] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      if (!dialog.open) dialog.showModal();
    } else {
      if (dialog.open) dialog.close();
      setRejectReason('');
      setError(null);
    }

    const handleBackdrop = (e) => {
      if (e.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      const inBox =
        rect.top <= e.clientY &&
        e.clientY <= rect.top + rect.height &&
        rect.left <= e.clientX &&
        e.clientX <= rect.left + rect.width;
      if (!inBox) onClose();
    };

    if (!('closedBy' in HTMLDialogElement.prototype)) {
      dialog.addEventListener('click', handleBackdrop);
      return () => dialog.removeEventListener('click', handleBackdrop);
    }
  }, [isOpen, onClose]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!rejectReason.trim()) {
      setError('반려 사유를 상세히 입력해 주세요.');
      return;
    }
    onReject(rejectReason.trim());
  };

  return (
    <dialog ref={dialogRef} closedby="any" className="native-modal-dialog" style={{ maxWidth: '500px' }} onClose={onClose}>
      <div style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <XCircle size={18} style={{ color: 'var(--accent-danger)' }} />
            <h3 style={{ fontSize: '1.0625rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              개정안 발의 티켓 반려 의결
            </h3>
          </div>
          <button type="button" onClick={onClose} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
            <X size={18} style={{ color: 'var(--text-muted)' }} />
          </button>
        </div>

        <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '14px' }}>
          <strong>티켓:</strong> {ticketTitle}<br />
          반려 사유는 발의한 엔지니어에게 피드백으로 전달되며, WORM 감사 체인에 기록됩니다.
        </p>

        {error && (
          <div style={{ padding: '8px 12px', background: 'var(--accent-danger-light)', color: 'var(--accent-danger)', borderRadius: '6px', fontSize: '0.75rem', marginBottom: '12px' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
              반려 사유 (필수)
            </label>
            <textarea
              rows={4}
              value={rejectReason}
              onChange={(e) => {
                setRejectReason(e.target.value);
                if (error) setError(null);
              }}
              placeholder="예: 제안된 수치가 물리 안전 마진(140N 이하)을 초과하였으며 타당한 예외 근거가 제시되지 않았습니다."
              required
              style={{
                width: '100%',
                padding: '10px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface-2)',
                fontSize: '0.8125rem',
                color: 'var(--text-primary)',
                resize: 'none'
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '8px 14px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface-2)',
                fontSize: '0.8125rem',
                cursor: 'pointer'
              }}
            >
              취소
            </button>
            <button
              type="submit"
              style={{
                padding: '8px 18px',
                borderRadius: '6px',
                border: 'none',
                background: 'var(--accent-danger)',
                color: '#ffffff',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              반려 의결 확정
            </button>
          </div>
        </form>
      </div>
    </dialog>
  );
}
