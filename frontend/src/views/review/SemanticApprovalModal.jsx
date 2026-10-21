/**
 * [계층 1] SemanticApprovalModal View (Pure Dumb UI Component)
 * - 최종 승인 시 세맨틱 버전(vMAJOR.MINOR.PATCH) 승계 및 WORM 감사로그 확정 모달
 * - Modern Web Guidance: <dialog closedby="any">
 */

import React, { useRef, useEffect, useState } from 'react';
import { CheckCircle2, X, ArrowRight, ShieldCheck, Tag } from 'lucide-react';

export function SemanticApprovalModal({
  isOpen,
  currentVersion = 'v1.2.0',
  computedSemanticVersion,
  onClose,
  onApprove
}) {
  const dialogRef = useRef(null);
  const [overrideReason, setOverrideReason] = useState('');
  const [customVersion, setCustomVersion] = useState('');

  const targetVersion = customVersion || computedSemanticVersion?.targetVersion || 'v1.2.1';

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      if (!dialog.open) dialog.showModal();
      setCustomVersion(computedSemanticVersion?.targetVersion || '');
    } else {
      if (dialog.open) dialog.close();
      setOverrideReason('');
      setCustomVersion('');
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
  }, [isOpen, onClose, computedSemanticVersion]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onApprove({
      targetVersion,
      overrideReason: overrideReason.trim()
    });
  };

  return (
    <dialog ref={dialogRef} closedby="any" className="native-modal-dialog" style={{ maxWidth: '540px' }} onClose={onClose}>
      <div style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle2 size={18} style={{ color: 'var(--accent-success)' }} />
            <h3 style={{ fontSize: '1.0625rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              세맨틱 버전 승계 및 최종 승인 의결
            </h3>
          </div>
          <button type="button" onClick={onClose} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
            <X size={18} style={{ color: 'var(--text-muted)' }} />
          </button>
        </div>

        {/* ── 버전 승계 안내 박스 ── */}
        <div
          style={{
            background: 'var(--bg-surface-2)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '16px',
            textAlign: 'center'
          }}
        >
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
            승계 판본 계산 결과 ({computedSemanticVersion?.bumpType || 'PATCH'} 승계)
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
            <span style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              {currentVersion}
            </span>
            <ArrowRight size={16} style={{ color: 'var(--accent-primary)' }} />
            <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--accent-success)' }}>
              {targetVersion}
            </span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: '8px 0 0 0' }}>
            {computedSemanticVersion?.reasoning}
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
              최종 승계 버전 직접 지정 (선택)
            </label>
            <input
              type="text"
              value={customVersion}
              onChange={(e) => setCustomVersion(e.target.value)}
              placeholder="예: v1.2.1"
              style={{
                width: '100%',
                padding: '8px 10px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface-2)',
                fontSize: '0.8125rem',
                color: 'var(--text-primary)'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
              심사관 최종 승인 사유 및 의결 의견
            </label>
            <textarea
              rows={3}
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              placeholder="예: 실무 엔지니어의 수식 보정 사항과 출처 무결성이 검증되어 정식 공인 온톨로지 문서로 승인합니다."
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

          {/* WORM 감사로그 안내 배너 */}
          <div
            style={{
              padding: '10px 12px',
              borderRadius: '6px',
              background: 'var(--accent-primary-light)',
              border: '1px solid rgba(37, 99, 235, 0.2)',
              fontSize: '0.75rem',
              color: 'var(--accent-primary)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <ShieldCheck size={14} />
            <span>승인 시 WORM 불변 머클 해시체인 감사로그에 서명 해시가 영구 기록됩니다.</span>
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
                background: 'var(--accent-success)',
                color: '#ffffff',
                fontSize: '0.8125rem',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              최종 승인 집행 ➔
            </button>
          </div>
        </form>
      </div>
    </dialog>
  );
}
