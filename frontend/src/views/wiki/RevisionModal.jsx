/**
 * [계층 1] RevisionModal View (Pure Dumb UI Component)
 * - 기존 문서 개정 발의 모달 (Tab 3 거버넌스 티켓 제출)
 * - Modern Web Guidance: <dialog closedby="any">
 */

import React, { useRef, useEffect, useState } from 'react';
import { Edit3, X, Send } from 'lucide-react';

export function RevisionModal({
  isOpen,
  conceptDetail,
  currentUser,
  onClose,
  onSubmit
}) {
  const dialogRef = useRef(null);
  const [targetSection, setTargetSection] = useState('principles');
  const [userNote, setUserNote] = useState('');
  const [overrideReason, setOverrideReason] = useState('');

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      if (!dialog.open) dialog.showModal();
    } else {
      if (dialog.open) dialog.close();
      setUserNote('');
      setOverrideReason('');
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
    if (!userNote.trim()) return;

    onSubmit({
      conceptId: conceptDetail?.id,
      title: `${conceptDetail?.title} 개정안 발의`,
      author: currentUser?.name || '현장 엔지니어',
      department: currentUser?.department || '공정기술팀',
      reviewType: 'minor_revision',
      originType: 'human_engineer',
      targetSection,
      userNote: userNote.trim(),
      overrideReason: overrideReason.trim()
    });
  };

  return (
    <dialog ref={dialogRef} closedby="any" className="native-modal-dialog" style={{ maxWidth: '580px' }} onClose={onClose}>
      <div style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Edit3 size={18} style={{ color: 'var(--accent-primary)' }} />
            <h3 style={{ fontSize: '1.0625rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              지식 문서 개정 발의하기
            </h3>
          </div>
          <button type="button" onClick={onClose} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
            <X size={18} style={{ color: 'var(--text-muted)' }} />
          </button>
        </div>

        <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: 1.5 }}>
          <strong>대상 문서:</strong> {conceptDetail?.title} (v{conceptDetail?.version || '1.2.0'})<br />
          발의된 개정안은 Tab 3 거버넌스 승인 센터에 티켓으로 등록되며, 수석 검토관의 심사를 거쳐 정식 위키에 반영됩니다.
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
              수정 대상 섹션
            </label>
            <select
              value={targetSection}
              onChange={(e) => setTargetSection(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 10px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface-2)',
                color: 'var(--text-primary)',
                fontSize: '0.8125rem'
              }}
            >
              <option value="summary">1. 개요 및 기술 정의</option>
              <option value="principles">2. 작동 및 물리 원리 (KaTeX 수식)</option>
              <option value="limitations">3. 물리적 한계 및 트레이드오프</option>
              <option value="perspectives">4. 적응형 실무 사례 및 파라미터 (L3 규격)</option>
              <option value="relations">5. 온톨로지 인과 관계망 및 규모별 계층</option>
              <option value="evidences">6. 공식 검증 출처 원문</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
              개정 제안 사유 및 실무 근거 (필수)
            </label>
            <textarea
              rows={4}
              value={userNote}
              onChange={(e) => setUserNote(e.target.value)}
              placeholder="예: 최신 ECTC 2025 논문 실측 데이터를 바탕으로 접합 압력 권고 수치를 수정할 것을 제안합니다."
              required
              style={{
                width: '100%',
                padding: '10px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface-2)',
                color: 'var(--text-primary)',
                fontSize: '0.8125rem',
                resize: 'none'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
              물리 안전 마진 예외 사유 (선택)
            </label>
            <input
              type="text"
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              placeholder="예: 16단 적층 시 본딩 압력 140N 초과 필요 (신규 NCF 소재 적용)"
              style={{
                width: '100%',
                padding: '8px 10px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface-2)',
                color: 'var(--text-primary)',
                fontSize: '0.8125rem'
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
                color: 'var(--text-secondary)',
                fontSize: '0.8125rem',
                cursor: 'pointer'
              }}
            >
              취소
            </button>
            <button
              type="submit"
              style={{
                padding: '8px 16px',
                borderRadius: '6px',
                border: 'none',
                background: 'var(--accent-primary)',
                color: '#ffffff',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Send size={13} />
              <span>개정안 티켓 제출 (Tab 3)</span>
            </button>
          </div>
        </form>
      </div>
    </dialog>
  );
}
