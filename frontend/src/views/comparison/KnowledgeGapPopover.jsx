/**
 * [계층 1] KnowledgeGapPopover View (Pure Dumb UI Component)
 * - 화면 2-B: 매트릭스의 '⚠️ 미등록 데이터 (Gap)' 셀 클릭 시 노출
 * - 온톨로지 부재 지식 설명 및 [외부 문헌 조사실(Tab 4)에서 백서 발굴하기 ➔] 연계 액션
 */

import React, { useEffect, useRef } from 'react';
import { AlertTriangle, BookOpen, ExternalLink, X } from 'lucide-react';

export function KnowledgeGapPopover({
  activeGap,
  targetAName = 'Target A',
  targetBName = 'Target B',
  onClose,
  onNavigateToResearch
}) {
  const dialogRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (activeGap) {
      if (!dialog.open) {
        dialog.showModal();
      }
    } else {
      if (dialog.open) {
        dialog.close();
      }
    }
  }, [activeGap]);

  if (!activeGap) return null;

  const { row, targetSide } = activeGap;
  const targetName = targetSide === 'A' ? targetAName : targetBName;
  const searchKeyword = `${targetName} ${row?.axis || ''}`.trim();

  const handleBackdropClick = (e) => {
    if (e.target === dialogRef.current) {
      onClose();
    }
  };

  return (
    <dialog
      ref={dialogRef}
      closedby="any"
      onClick={handleBackdropClick}
      onClose={onClose}
      className="modal-box"
      style={{
        maxWidth: '520px',
        width: '90%',
        padding: '0',
        borderRadius: '12px',
        border: '1px solid var(--border-color)',
        background: 'var(--bg-surface)',
        boxShadow: '0 12px 36px rgba(0, 0, 0, 0.25)',
        color: 'var(--text-primary)'
      }}
    >
      {/* 헤더 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-color)',
          background: 'var(--bg-surface-2)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertTriangle size={18} style={{ color: 'var(--accent-warning)' }} />
          <h4 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 800 }}>
            온톨로지 지식 갭 (Knowledge Gap)
          </h4>
        </div>
        <button
          type="button"
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--text-muted)',
            padding: '4px'
          }}
        >
          <X size={18} />
        </button>
      </div>

      {/* 본문 */}
      <div style={{ padding: '20px' }}>
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '8px',
            background: 'var(--accent-warning-light)',
            border: '1px solid var(--accent-warning)',
            marginBottom: '16px'
          }}
        >
          <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--accent-warning)', marginBottom: '4px' }}>
            대상 기술: <span style={{ color: 'var(--text-primary)' }}>{targetName}</span>
          </div>
          <div style={{ fontSize: '0.875rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            평가 축: {row?.axis}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            분류 카테고리: {row?.axisCategory || '일반'}
          </div>
        </div>

        <p style={{ fontSize: '0.8125rem', lineHeight: 1.6, color: 'var(--text-secondary)', margin: '0 0 16px 0' }}>
          현재 반도체 공정 인과 온톨로지 지식 베이스에 해당 항목에 대한 <strong>실측 데이터 또는 공인 문헌 출처([E-xx])</strong>가
          등록되어 있지 않습니다. 신뢰성 있는 인과 추론을 위해 외부 학술 논문, 백서, 특허 등의 추가 조사가 필요합니다.
        </p>

        <div
          style={{
            padding: '12px',
            borderRadius: '8px',
            background: 'var(--bg-surface-2)',
            border: '1px solid var(--border-color)',
            fontSize: '0.75rem',
            color: 'var(--text-muted)'
          }}
        >
          💡 <strong>연계 안내:</strong> [외부 문헌 조사실] 버튼을 누르면 추천 검색어(<code>{searchKeyword}</code>)를 바탕으로
          arXiv, IEEE, 산학 백서의 실측 인과 데이터를 즉시 교차 분석할 수 있습니다.
        </div>
      </div>

      {/* 풋터 액션 바 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-end',
          gap: '10px',
          padding: '14px 20px',
          borderTop: '1px solid var(--border-color)',
          background: 'var(--bg-surface-2)'
        }}
      >
        <button
          type="button"
          onClick={onClose}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: '1px solid var(--border-color)',
            background: 'var(--bg-surface)',
            color: 'var(--text-secondary)',
            fontSize: '0.8125rem',
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          닫기
        </button>
        <button
          type="button"
          onClick={() => onNavigateToResearch(searchKeyword)}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: 'none',
            background: 'var(--accent-primary)',
            color: '#fff',
            fontSize: '0.8125rem',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <BookOpen size={14} />
          <span>외부 문헌 조사(Tab 4)에서 백서 발굴하기 ➔</span>
        </button>
      </div>
    </dialog>
  );
}
