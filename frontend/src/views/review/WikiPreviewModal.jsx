/**
 * [계층 1] WikiPreviewModal View (Pure Dumb UI Component)
 * - 승인 전 공용 위키 브라우저 사전 렌더링 미리보기
 * - Modern Web Guidance: <dialog closedby="any">
 */

import React, { useRef, useEffect } from 'react';
import { Eye, X, CheckCircle2 } from 'lucide-react';
import { formulaService } from '../../services/formulaService';

export function WikiPreviewModal({
  isOpen,
  previewData,
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

  const concept = previewData?.previewConcept || {};

  return (
    <dialog ref={dialogRef} closedby="any" className="native-modal-dialog" style={{ maxWidth: '800px', maxHeight: '90vh' }} onClose={onClose}>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', maxHeight: '85vh' }}>
        {/* 모달 헤더 */}
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Eye size={18} style={{ color: 'var(--accent-primary)' }} />
            <h3 style={{ fontSize: '1.0625rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              위키 본문 사전 렌더링 미리보기 (승인 시 반영될 화면)
            </h3>
          </div>
          <button type="button" onClick={onClose} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>
            <X size={18} style={{ color: 'var(--text-muted)' }} />
          </button>
        </div>

        {/* 위키 본문 렌더링 영역 */}
        <div style={{ padding: '24px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* 개념 타이틀 & 버전 */}
          <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '2px 8px', borderRadius: '4px', background: 'var(--accent-success-light)', color: 'var(--accent-success)' }}>
                승인 예정 버전: {previewData?.targetVersion || concept.version || 'v1.2.1'}
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                분류: {concept.domainFacet || '단위 공정'} · {concept.scaleName || '공정 스케일'}
              </span>
            </div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, margin: '0 0 6px 0' }}>
              {concept.title || '개념 명칭'}
            </h1>
            {concept.engName && <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>{concept.engName}</div>}
          </div>

          {/* 1번 개요 */}
          <div>
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, marginBottom: '6px', color: 'var(--text-primary)' }}>
              1. 개요 및 기술 정의
            </h4>
            <p style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
              {concept.summary || '개요 내용이 없습니다.'}
            </p>
          </div>

          {/* 2번 원리 */}
          {concept.principles && concept.principles.length > 0 && (
            <div>
              <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-primary)' }}>
                2. 작동 및 물리 원리 (KaTeX 수식)
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {concept.principles.map((p, idx) => (
                  <div key={idx} style={{ background: 'var(--bg-surface-2)', padding: '12px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.8125rem', marginBottom: '4px' }}>
                      Step {p.step || idx + 1}: {p.title}
                    </div>
                    <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: p.formula ? '8px' : 0 }}>
                      {p.content}
                    </div>
                    {p.formula && (
                      <div
                        style={{ background: 'var(--bg-surface)', padding: '8px 12px', borderRadius: '4px', overflowX: 'auto' }}
                        dangerouslySetInnerHTML={{ __html: formulaService.renderFormula(p.formula, true) }}
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3번 한계 */}
          {concept.limitations && concept.limitations.length > 0 && (
            <div>
              <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-primary)' }}>
                3. 물리적 한계 및 트레이드오프
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {concept.limitations.map((lim, idx) => (
                  <div key={idx} style={{ background: 'var(--bg-surface-2)', padding: '10px 12px', borderRadius: '6px', borderLeft: '3px solid var(--accent-warning)' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.8125rem' }}>{lim.title}</div>
                    <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>{lim.description}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 모달 푸터 */}
        <div style={{ padding: '14px 24px', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end', background: 'var(--bg-surface-2)' }}>
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: '8px 18px',
              borderRadius: '6px',
              border: 'none',
              background: 'var(--accent-primary)',
              color: '#ffffff',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            미리보기 닫기
          </button>
        </div>
      </div>
    </dialog>
  );
}
