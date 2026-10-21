/**
 * [계층 1] LockoutModal View (Pure Dumb UI Component)
 * - 10분 독점 방지 정책에 의해 편집 세션이 자동 만료되었음을 안내하는 모달
 * - Modern Web Guidance: <dialog closedby="any">
 */

import React, { useRef, useEffect } from 'react';
import { Clock, AlertTriangle, X } from 'lucide-react';

export function LockoutModal({
  isOpen,
  onClose
}) {
  const dialogRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      if (!dialog.open) dialog.showModal();
    } else {
      if (dialog.open) dialog.close();
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

  return (
    <dialog ref={dialogRef} closedby="any" className="native-modal-dialog" style={{ maxWidth: '460px' }} onClose={onClose}>
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <div
          style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            background: 'var(--accent-warning-light)',
            color: 'var(--accent-warning)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px auto'
          }}
        >
          <Clock size={24} />
        </div>

        <h3 style={{ fontSize: '1.125rem', fontWeight: 800, margin: '0 0 8px 0', color: 'var(--text-primary)' }}>
          10분 편집 세션이 자동 만료되었습니다
        </h3>

        <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 0 20px 0' }}>
          온톨로지 거버넌스의 <strong>10분 독점 방지 정책</strong>에 의해 편집 점유 락이 자동 반환되었습니다.<br />
          편집기가 읽기 전용으로 전환되었습니다. 다른 검토관이 세션을 인계받을 수 있으며, 필요 시 다시 세션을 인계받아 편집할 수 있습니다.
        </p>

        <button
          type="button"
          onClick={onClose}
          style={{
            padding: '9px 24px',
            borderRadius: '8px',
            border: 'none',
            background: 'var(--accent-primary)',
            color: '#ffffff',
            fontSize: '0.8125rem',
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          확인
        </button>
      </div>
    </dialog>
  );
}
