/**
 * [계층 1] ContextualPopover View (Pure Dumb UI Component)
 * - 본문 텍스트 드래그(선택) 또는 인라인 개념 클릭 시 마우스 커서 부근에 표출되는 플로팅 문맥 해설 팝오버
 * - [💬 챗봇 질문] 및 [➔ 문서 이동] 듀얼 액션 탑재
 */

import React, { useEffect } from 'react';
import { MessageSquare, ArrowRight, X, Sparkles } from 'lucide-react';

export function ContextualPopover({
  isOpen,
  position,
  data,
  onClose,
  onAskChatbot,
  onNavigateConcept
}) {
  useEffect(() => {
    if (!isOpen) return;
    const handleOutsideClick = (e) => {
      if (!e.target.closest('.concept-popover, [data-wiki-article]')) {
        onClose();
      }
    };
    const timer = setTimeout(() => {
      window.addEventListener('mousedown', handleOutsideClick);
    }, 150);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('mousedown', handleOutsideClick);
    };
  }, [isOpen, onClose]);

  if (!isOpen || !data || !position) return null;

  const targetId = data.targetConceptId || data.conceptId;

  return (
    <div
      className="concept-popover open"
      style={{
        position: 'fixed',
        left: `${position.x}px`,
        top: `${position.y}px`,
        width: '320px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '10px',
        padding: '14px',
        boxShadow: '0 12px 32px rgba(0, 0, 0, 0.22)',
        zIndex: 9990,
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        opacity: 1,
        visibility: 'visible',
        pointerEvents: 'auto',
        transform: 'translateY(0) scale(1)',
        animation: 'fadeIn 0.15s ease'
      }}
    >
      {/* 팝오버 헤더 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Sparkles size={14} style={{ color: 'var(--accent-primary)' }} />
          <strong style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>
            {data.title || '용어 문맥 해설'}
          </strong>
        </div>
        <button
          type="button"
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            padding: '2px'
          }}
        >
          <X size={14} />
        </button>
      </div>

      {data.isLoading && <p role="status">뜻과 문맥 해설을 불러오는 중입니다...</p>}
      {data.error && <p role="alert">{data.error}</p>}
      {/* 표현의 뜻 */}
      {data.definition && <p style={{ fontSize: '0.75rem', lineHeight: 1.5, color: 'var(--text-secondary)', margin: 0 }}>
        <strong>뜻:</strong> {data.definition}
      </p>}

      {/* AI 문맥 맞춤 해설 */}
      {data.contextSentence && (
        <div
          style={{
            padding: '8px 10px',
            borderRadius: '6px',
            background: 'var(--accent-primary-light)',
            fontSize: '0.75rem',
            color: 'var(--accent-primary)',
            lineHeight: 1.4
          }}
        >
          <strong>이 문장에서:</strong> {data.contextSentence}
        </div>
      )}

      {/* 풋터 액션 바: [ 💬 챗봇 질문 ] & [ ➔ 문서 이동 ] */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-end',
          gap: '6px',
          paddingTop: '8px',
          borderTop: '1px solid var(--border-color)',
          marginTop: '4px'
        }}
      >
        <button
          type="button"
          onClick={() => {
            onClose();
            onAskChatbot(data.title || data.term);
          }}
          style={{
            padding: '4px 8px',
            borderRadius: '4px',
            border: '1px solid var(--accent-primary)',
            background: 'var(--accent-primary-light)',
            color: 'var(--accent-primary)',
            fontSize: '0.6875rem',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px'
          }}
          title="이 용어에 대해 AI 챗봇에게 심층 질문을 전송합니다."
        >
          <MessageSquare size={12} />
          <span>챗봇 질문</span>
        </button>

        {targetId && (
          <button
            type="button"
            onClick={() => {
              onClose();
              onNavigateConcept(targetId);
            }}
            style={{
              padding: '4px 10px',
              borderRadius: '4px',
              border: 'none',
              background: 'var(--accent-primary)',
              color: '#fff',
              fontSize: '0.6875rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <span>문서 이동</span>
            <ArrowRight size={12} />
          </button>
        )}
      </div>
    </div>
  );
}
