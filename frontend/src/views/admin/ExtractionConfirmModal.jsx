import React, { useEffect, useRef } from 'react';

export function ExtractionConfirmModal({ confirmation, onConfirm, onCancel }) {
  const dialogRef = useRef(null);
  useEffect(() => {
    const dialog = dialogRef.current;
    if (confirmation && !dialog.open) dialog.showModal();
    else if (!confirmation && dialog.open) dialog.close();
  }, [confirmation]);

  const total = confirmation?.docIds.length || 0;
  const pending = confirmation?.pendingIds.length || 0;
  const buttonStyle = { padding: '9px 12px', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'var(--bg-page)', color: 'var(--text-primary)', cursor: 'pointer' };

  return (
    <dialog
      ref={dialogRef}
      className="modal-box"
      aria-labelledby="extraction-confirm-title"
      aria-describedby="extraction-confirm-description"
      onCancel={(event) => { event.preventDefault(); onCancel(); }}
      style={{ width: 'min(520px, calc(100% - 32px))', maxHeight: '85vh', margin: 'auto', padding: '24px', borderRadius: '12px', border: '1px solid var(--border-color)', background: 'var(--bg-surface)', color: 'var(--text-primary)' }}
    >
      {confirmation && <>
        <h3 id="extraction-confirm-title" style={{ margin: '0 0 14px' }}>재추출할 문서가 포함되어 있습니다</h3>
        <div id="extraction-confirm-description" style={{ lineHeight: 1.7 }}>
          <p>선택한 {total}건 중 미추출 {pending}건, 기추출 {total - pending}건입니다.</p>
          <p>재추출하면 이전 추출 미리보기가 새 결과로 갱신되고, 처리 시간과 API 사용량이 추가됩니다. 기존 위키는 적용 전까지 변경되지 않습니다.</p>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'flex-end', gap: '8px', marginTop: '20px' }}>
          <button type="button" autoFocus onClick={onCancel} style={buttonStyle}>취소</button>
          <button type="button" disabled={pending === 0} onClick={() => onConfirm(false)} style={{ ...buttonStyle, opacity: pending === 0 ? 0.5 : 1, cursor: pending === 0 ? 'not-allowed' : 'pointer' }}>미추출만 실행 ({pending}건)</button>
          <button type="button" onClick={() => onConfirm(true)} style={{ ...buttonStyle, background: 'var(--accent-primary)', color: '#fff' }}>재추출 포함 실행 ({total}건)</button>
        </div>
      </>}
    </dialog>
  );
}
