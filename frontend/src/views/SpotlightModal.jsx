/**
 * [계층 1] Spotlight Search Modal View (Pure Dumb UI Component)
 * - Modern Web Guidance: <dialog closedby="any">
 * - transitions.dev 모달 트랜지션
 * - Phase 1: 스포트라이트 뼈대 및 단축키 연동 (Phase 2에서 실시간 검색 엔진 결합)
 */

import React, { useRef, useEffect, useState } from 'react';
import { Search, X, ArrowRight, CornerDownLeft, FileText, Cpu, GitCompare, ExternalLink } from 'lucide-react';

export function SpotlightModal({
  isOpen,
  onClose,
  onSelectConcept
}) {
  const dialogRef = useRef(null);
  const inputRef = useRef(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      if (!dialog.open) {
        dialog.showModal();
        setTimeout(() => inputRef.current?.focus(), 50);
      }
    } else {
      if (dialog.open) {
        dialog.close();
      }
      setSearchTerm('');
    }

    const handleBackdropClick = (e) => {
      if (e.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      const inBox =
        rect.top <= e.clientY &&
        e.clientY <= rect.top + rect.height &&
        rect.left <= e.clientX &&
        e.clientX <= rect.left + rect.width;
      if (!inBox) {
        onClose();
      }
    };

    if (!('closedBy' in HTMLDialogElement.prototype)) {
      dialog.addEventListener('click', handleBackdropClick);
      return () => dialog.removeEventListener('click', handleBackdropClick);
    }
  }, [isOpen, onClose]);

  return (
    <dialog
      ref={dialogRef}
      closedby="any"
      aria-labelledby="spotlightDialogTitle"
      className="native-modal-dialog"
      style={{ maxWidth: '640px' }}
      onClose={onClose}
    >
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {/* 상단 검색 인풋바 */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '16px 20px',
            borderBottom: '1px solid var(--border-color)',
            gap: '12px'
          }}
        >
          <Search size={20} style={{ color: 'var(--text-muted)' }} />
          <input
            ref={inputRef}
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="공정 개념, 물리 원리, KaTeX 수식, L3 파라미터 검색..."
            style={{
              flex: 1,
              border: 'none',
              background: 'transparent',
              outline: 'none',
              fontSize: '1rem',
              color: 'var(--text-primary)'
            }}
          />
          <kbd
            style={{
              fontSize: '0.75rem',
              padding: '2px 6px',
              borderRadius: '4px',
              background: 'var(--bg-surface-2)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-muted)'
            }}
          >
            ESC
          </kbd>
        </div>

        {/* 결과 또는 추천 키워드 영역 */}
        <div style={{ padding: '16px 20px', maxHeight: '360px', overflowY: 'auto' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
            ⚡ 추천 바로가기
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {[
              { id: 'concept-tcb', title: '열압착 본딩 (TCB: Thermo-Compression Bonding)', facet: '첨단 패키징', scale: '스케일 5' },
              { id: 'concept-hybrid-bonding', title: '하이브리드 다이렉트 Cu-Cu 본딩', facet: '초고밀도 적층', scale: '스케일 4' },
              { id: 'concept-cryo-etch', title: '극저온 원자층 식각 (Cryo-ALE)', facet: '단위 공정', scale: '스케일 2' }
            ].map((item) => (
              <div
                key={item.id}
                onClick={() => {
                  if (onSelectConcept) onSelectConcept(item.id);
                  onClose();
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  background: 'var(--bg-surface-2)',
                  transition: 'background 0.15s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <FileText size={16} style={{ color: 'var(--accent-primary)' }} />
                  <div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {item.title}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {item.facet} · {item.scale}
                    </div>
                  </div>
                </div>
                <CornerDownLeft size={14} style={{ color: 'var(--text-muted)' }} />
              </div>
            ))}
          </div>
        </div>

        {/* 하단 단축키 가이드 */}
        <div
          style={{
            padding: '10px 20px',
            background: 'var(--bg-surface-2)',
            borderTop: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.75rem',
            color: 'var(--text-muted)'
          }}
        >
          <span>Tip: 수식 기호나 DOI 번호로도 인과 지식을 검색할 수 있습니다.</span>
          <span>Tab 1~4 실시간 색인</span>
        </div>
      </div>
    </dialog>
  );
}
