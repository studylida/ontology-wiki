import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { ReviewWikiSections } from './ReviewWikiSections';
import { DOMAIN_FACET_LABELS } from '../../types/concept.dto';
import { relationService } from '../../services/relationService';
export function WikiPreviewModal({
  isOpen,
  previewData,
  onClose,
  currentUser
}) {
  const dialogRef = useRef(null);
  useEffect(() => {
    const dialog = dialogRef.current;
    if (isOpen && !dialog.open) dialog.showModal();
    if (!isOpen && dialog.open) dialog.close();
    if (isOpen) {
      const section = Array.from(dialog.querySelectorAll('[data-section]')).find(node => node.dataset.section === previewData?.focusSection);
      section?.scrollIntoView({
        block: 'start'
      });
    }
  }, [isOpen, previewData]);
  const concept = previewData?.previewConcept || {};
  return <dialog ref={dialogRef} className="native-modal-dialog" style={{
    maxWidth: '1000px',
    width: '90vw',
    maxHeight: '90vh',
    padding: 0,
    color: 'var(--text-primary)',
    background: 'var(--bg-surface)'
  }} onCancel={onClose} onClose={onClose}>
    <header style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '16px',
      borderBottom: '1px solid var(--border-color)'
    }}>
      <strong>위키 미리보기 · 승인 시 반영될 내용 · 판본 {previewData?.ticketVersion}</strong><button type="button" onClick={onClose} aria-label="위키 미리보기 닫기"><X size={18} /></button>
    </header>
    <div style={{
      padding: '20px',
      overflowY: 'auto',
      maxHeight: '75vh'
    }}>
      <h2>{concept.title}</h2><p>{DOMAIN_FACET_LABELS[concept.domainFacet] || '분야 미확정'} · {concept.processCategory || '분류 미확정'} · {relationService.getScaleLabel(concept.scaleLevel)}</p>
      <p style={{
        color: 'var(--text-muted)'
      }}>등록 자료 중 관련 발췌를 사용한 변경안입니다. 의미 검토 결과가 전체 문서 검증이나 물리 안전성의 승인을 뜻하지는 않습니다. 직접 편집 내용도 함께 확인해주세요.</p>
      <ReviewWikiSections concept={concept} currentUser={currentUser} />
    </div>
  </dialog>;
}
