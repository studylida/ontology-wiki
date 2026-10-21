/**
 * [계층 1] ChatbotDrawer View (Pure Dumb UI Component)
 * - [F-01] 플로팅 실시간 챗봇 드로어 패널
 * - 컨텍스트 인식 헤더, 퀵 질문 칩, 스트리밍 메시지 스크롤 영역 및 입력 폼
 */

import React, { useEffect, useRef } from 'react';
import { Bot, X, RotateCcw, Send, Sparkles } from 'lucide-react';
import { ChatMessageItem } from './ChatMessageItem';

export function ChatbotDrawer({
  isOpen,
  contextData = {},
  messages = [],
  inputText = '',
  isStreaming = false,
  isThinking = false,
  onClose,
  onChangeInput,
  setInputText,
  onSendMessage,
  handleSendMessage,
  onReset,
  handleReset,
  onActionClick,
  handleActionClick
}) {
  const messagesEndRef = useRef(null);

  const changeTextHandler = onChangeInput || setInputText;
  const sendMessageHandler = onSendMessage || handleSendMessage;
  const resetHandler = onReset || handleReset;
  const actionClickHandler = onActionClick || handleActionClick;

  // 새 메시지 및 스트리밍 시 자동 하단 스크롤
  useEffect(() => {
    if (isOpen && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim() || isStreaming) return;
    if (sendMessageHandler) {
      sendMessageHandler(inputText.trim());
    }
  };

  return (
    <div
      className="floating-chat-widget active"
      style={{
        position: 'fixed',
        bottom: '80px',
        right: '24px',
        width: '420px',
        maxWidth: 'calc(100vw - 32px)',
        height: '620px',
        maxHeight: 'calc(100vh - 110px)',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-color)',
        borderRadius: '16px',
        boxShadow: '0 20px 50px rgba(0, 0, 0, 0.28)',
        zIndex: 10000,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        opacity: 1,
        pointerEvents: 'auto'
      }}
    >
      {/* 헤더 바 */}
      <div
        style={{
          padding: '14px 16px',
          background: 'var(--bg-surface-2)',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              background: 'var(--accent-primary)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}
          >
            <Bot size={16} />
          </div>
          <div style={{ overflow: 'hidden' }}>
            <div
              style={{
                fontSize: '0.8125rem',
                fontWeight: 800,
                color: 'var(--text-primary)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}
            >
              {contextData.conceptTitle || '반도체 인과 온톨로지 어시스턴트'}
            </div>
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', display: 'flex', gap: '6px' }}>
              <span>{contextData.scaleBadge || '전역 탐색'}</span>
              <span>•</span>
              <span style={{ color: '#10b981', fontWeight: 600 }}>{contextData.engineModeLabel || '🟢 Live'}</span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <button
            type="button"
            onClick={resetHandler}
            title="대화 이력 초기화"
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              padding: '6px',
              borderRadius: '4px'
            }}
          >
            <RotateCcw size={15} />
          </button>
          <button
            type="button"
            onClick={onClose}
            title="챗봇 닫기"
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              padding: '6px',
              borderRadius: '4px'
            }}
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* 퀵 질문 칩 바 */}
      {contextData.quickQuestionChips && contextData.quickQuestionChips.length > 0 && (
        <div
          style={{
            padding: '8px 12px',
            background: 'var(--bg-surface)',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            gap: '6px',
            overflowX: 'auto',
            flexShrink: 0
          }}
        >
          {contextData.quickQuestionChips.map((chip, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => sendMessageHandler && sendMessageHandler(chip)}
              style={{
                padding: '4px 10px',
                borderRadius: '12px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface-2)',
                color: 'var(--text-secondary)',
                fontSize: '0.6875rem',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--accent-primary)';
                e.currentTarget.style.color = 'var(--accent-primary)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-color)';
                e.currentTarget.style.color = 'var(--text-secondary)';
              }}
            >
              {chip}
            </button>
          ))}
        </div>
      )}

      {/* 대화 메시지 영역 */}
      <div
        style={{
          flex: 1,
          padding: '16px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {messages.map((msg, idx) => (
          <ChatMessageItem
            key={idx}
            message={msg}
            onFollowUpClick={sendMessageHandler}
            onActionClick={actionClickHandler}
          />
        ))}

        {isThinking && (
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', color: 'var(--text-muted)', fontSize: '0.75rem', padding: '6px 0' }}>
            <Sparkles size={14} style={{ color: 'var(--accent-primary)' }} />
            <span>온톨로지 인과 경로 탐색 및 의도 분석 중...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 입력 바 */}
      <form
        onSubmit={handleSubmit}
        style={{
          padding: '12px 14px',
          borderTop: '1px solid var(--border-color)',
          background: 'var(--bg-surface-2)',
          display: 'flex',
          gap: '8px',
          flexShrink: 0
        }}
      >
        <input
          type="text"
          value={inputText}
          onChange={(e) => changeTextHandler && changeTextHandler(e.target.value)}
          placeholder="공정 인과 관계 또는 물리 규격을 질문하세요..."
          style={{
            flex: 1,
            padding: '8px 12px',
            borderRadius: '6px',
            border: '1px solid var(--border-color)',
            background: 'var(--bg-surface)',
            color: 'var(--text-primary)',
            fontSize: '0.8125rem'
          }}
        />
        <button
          type="submit"
          disabled={isStreaming || !inputText.trim()}
          style={{
            padding: '8px 14px',
            borderRadius: '6px',
            border: 'none',
            background: isStreaming || !inputText.trim() ? 'var(--text-muted)' : 'var(--accent-primary)',
            color: '#fff',
            cursor: isStreaming || !inputText.trim() ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <Send size={15} />
        </button>
      </form>
    </div>
  );
}
