/**
 * [계층 1] Spotlight Search Modal View (Pure Dumb UI Component)
 * - Modern Web Guidance: <dialog closedby="any">
 * - transitions.dev 모달 트랜지션
 * - 기존 Spotlight API의 등록 개념 추천·검색 결과 표시
 */

import React, { useRef, useEffect } from 'react';
import { Search, CornerDownLeft, FileText } from 'lucide-react';
import { DOMAIN_FACET_LABELS } from '../types/concept.dto';
import { relationService } from '../services/relationService';

export function SpotlightModal({
  isOpen,
  searchTerm = '', onSearchTermChange, results = [], isLoading = false, error, totalIndexed = 0,
  onClose,
  onSelectConcept
}) {
  const dialogRef = useRef(null);
  const inputRef = useRef(null);

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
      aria-label="등록 지식 검색"
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
            onChange={(e) => onSearchTermChange(e.target.value)}
            aria-label="지식 검색어"
            placeholder="등록된 개념명·약어·본문 요약 검색..."
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
            {searchTerm.trim() ? '검색 결과' : '등록된 지식 바로가기'}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {isLoading && <p role="status">등록된 지식을 불러오는 중입니다...</p>}
            {error && <p role="alert">{error}</p>}
            {!isLoading && !error && results.length === 0 && <p role="status">일치하는 등록 개념이 없습니다.</p>}
            {!isLoading && !error && results.map((item) => (
              <button
                type="button"
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
                  border: '1px solid var(--border-color)',
                  textAlign: 'left',
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
                      {DOMAIN_FACET_LABELS[item.domainFacet] || item.domainFacet} · {relationService.getScaleLabel(item.scaleLevel)}
                    </div>
                  </div>
                </div>
                <CornerDownLeft size={14} style={{ color: 'var(--text-muted)' }} />
              </button>
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
          <span>개념명·영문명·등록 약어로 검색할 수 있습니다.</span>
          <span>등록 개념 {totalIndexed}개</span>
        </div>
      </div>
    </dialog>
  );
}
