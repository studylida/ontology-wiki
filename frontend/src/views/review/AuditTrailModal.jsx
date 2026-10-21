/**
 * [계층 1] AuditTrailModal View (Pure Dumb UI Component)
 * - WORM 머클 감사로그 불변 체인 내역 열람 모달
 * - Modern Web Guidance: <dialog closedby="any">
 */

import React, { useRef, useEffect } from 'react';
import { History, X, ShieldCheck, Hash, Link2, User } from 'lucide-react';
import { formatService } from '../../services/formatService';

export function AuditTrailModal({
  isOpen,
  ticketId,
  auditLogs = [],
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
    <dialog ref={dialogRef} closedby="any" className="native-modal-dialog" style={{ maxWidth: '680px', maxHeight: '85vh' }} onClose={onClose}>
      <div style={{ display: 'flex', flexDirection: 'column', maxHeight: '80vh' }}>
        {/* 모달 헤더 */}
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <History size={18} style={{ color: 'var(--accent-primary)' }} />
            <div>
              <h3 style={{ fontSize: '1.0625rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                WORM 불변 머클 감사 로그 (Audit Trail)
              </h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                티켓 식별자: {ticketId} · 해시체인 무결성 보존
              </span>
            </div>
          </div>
          <button type="button" onClick={onClose} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
            <X size={18} style={{ color: 'var(--text-muted)' }} />
          </button>
        </div>

        {/* 감사 로그 목록 */}
        <div style={{ padding: '20px 24px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {auditLogs.length === 0 ? (
            <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
              기록된 감사 체인이 비어있습니다.
            </div>
          ) : (
            auditLogs.map((log, idx) => (
              <div
                key={log.id || idx}
                style={{
                  padding: '14px 16px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-surface-2)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: 'var(--accent-primary-light)',
                      color: 'var(--accent-primary)'
                    }}
                  >
                    {log.action}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {formatService.formatDateTime(log.timestamp)}
                  </span>
                </div>

                <div style={{ fontSize: '0.8125rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <User size={13} style={{ color: 'var(--text-muted)' }} />
                  <span>수행자: <strong>{log.performedBy}</strong></span>
                </div>

                {/* 머클 해시 체인 정보 */}
                <div style={{ marginTop: '4px', paddingTop: '6px', borderTop: '1px dashed var(--border-color)', display: 'flex', flexDirection: 'column', gap: '2px', fontFamily: 'var(--font-mono)', fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                  <div>Entry Hash: {log.entryHash}</div>
                  {log.previousLogHash && <div>Prev Hash: {log.previousLogHash}</div>}
                </div>
              </div>
            ))
          )}
        </div>

        {/* 푸터 */}
        <div style={{ padding: '12px 24px', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-surface-2)' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--accent-success)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <ShieldCheck size={14} />
            WORM 무결성 체인 유효
          </span>
          <button
            type="button"
            onClick={onClose}
            style={{ padding: '6px 14px', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'var(--bg-surface)', fontSize: '0.75rem', cursor: 'pointer' }}
          >
            닫기
          </button>
        </div>
      </div>
    </dialog>
  );
}
