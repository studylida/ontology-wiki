/**
 * [계층 1] ChatMessageItem View (Pure Dumb UI Component)
 * - 챗봇 개별 메시지 버블 (사용자 vs 어시스턴트)
 * - SSE 스트리밍 텍스트 타이핑 효과 (.streaming-text-char) 및 인과 액션 카드/출처 렌더러
 */

import React from 'react';
import { Bot, User, ArrowRight, Sparkles, ExternalLink, HelpCircle } from 'lucide-react';

const PATH_BADGES = {
  factoid: { label: '단답·해설', color: '#2563eb', bg: 'rgba(37, 99, 235, 0.1)' },
  causal_clarifier: { label: '인과 구체화', color: '#7c3aed', bg: 'rgba(124, 58, 237, 0.1)' },
  action_trigger: { label: '화면 연계', color: '#059669', bg: 'rgba(5, 150, 105, 0.1)' }
};

export function ChatMessageItem({
  message,
  onFollowUpClick,
  onActionClick
}) {
  const isUser = message.sender === 'user';
  const pathMeta = message.pathType ? PATH_BADGES[message.pathType] : null;

  if (isUser) {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '12px' }}>
        <div
          style={{
            maxWidth: '82%',
            padding: '10px 14px',
            borderRadius: '14px 14px 2px 14px',
            background: 'var(--accent-primary)',
            color: '#fff',
            fontSize: '0.8125rem',
            lineHeight: 1.5,
            boxShadow: '0 1px 2px rgba(0, 0, 0, 0.1)'
          }}
        >
          <div>{message.text}</div>
          <div style={{ fontSize: '0.6875rem', opacity: 0.75, marginTop: '4px', textAlign: 'right' }}>
            {message.timestamp}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', gap: '8px', marginBottom: '14px', alignItems: 'flex-start' }}>
      {/* 챗봇 아이콘 */}
      <div
        style={{
          width: '28px',
          height: '28px',
          borderRadius: '50%',
          background: 'var(--accent-primary-light)',
          color: 'var(--accent-primary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          marginTop: '2px'
        }}
      >
        <Bot size={16} />
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxWidth: '85%' }}>
        {/* 버블 본체 */}
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '2px 14px 14px 14px',
            background: 'var(--bg-surface-2)',
            border: '1px solid var(--border-color)',
            fontSize: '0.8125rem',
            lineHeight: 1.6,
            color: 'var(--text-primary)'
          }}
        >
          {/* 의도 라우터 배지 */}
          {pathMeta && (
            <div style={{ marginBottom: '6px' }}>
              <span
                style={{
                  fontSize: '0.6875rem',
                  fontWeight: 800,
                  padding: '1px 6px',
                  borderRadius: '4px',
                  color: pathMeta.color,
                  background: pathMeta.bg
                }}
              >
                {pathMeta.label}
              </span>
            </div>
          )}

          {/* 스트리밍 텍스트 */}
          <div style={{ whiteSpace: 'pre-wrap' }}>
            {message.text ? (
              <span>{message.text}</span>
            ) : (
              <span style={{ color: 'var(--text-muted)' }}>온톨로지 인과 그래프를 탐색 중입니다...</span>
            )}
            {message.isStreaming && (
              <span className="streaming-text-char" style={{ display: 'inline-block', width: '6px', height: '14px', background: 'var(--accent-primary)', marginLeft: '2px', verticalAlign: 'middle' }} />
            )}
          </div>

          {/* 출처 각주 배지 */}
          {message.citations && message.citations.length > 0 && (
            <div style={{ marginTop: '8px', paddingTop: '6px', borderTop: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '4px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>근거 출처:</span>
              {message.citations.map((cite, cIdx) => (
                <span
                  key={cIdx}
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.6875rem',
                    fontWeight: 700,
                    color: 'var(--accent-primary)',
                    background: 'var(--bg-surface)',
                    padding: '1px 5px',
                    borderRadius: '4px',
                    border: '1px solid var(--border-color)'
                  }}
                >
                  [{cite}]
                </span>
              ))}
            </div>
          )}
        </div>

        {/* 액션 카드 트리거 버튼 */}
        {message.actionPayload && (
          <button
            type="button"
            onClick={() => onActionClick(message.actionPayload)}
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid var(--accent-primary)',
              background: 'var(--accent-primary-light)',
              color: 'var(--accent-primary)',
              fontSize: '0.75rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              alignSelf: 'flex-start'
            }}
          >
            <span>{message.actionPayload.buttonLabel || '관련 화면으로 바로 이동하기'}</span>
            <ArrowRight size={14} style={{ marginLeft: '6px' }} />
          </button>
        )}

        {/* 후속 꼬리질문 칩 */}
        {message.followUpChips && message.followUpChips.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '2px' }}>
            {message.followUpChips.map((chip, chipIdx) => (
              <button
                key={chipIdx}
                type="button"
                onClick={() => onFollowUpClick(chip)}
                style={{
                  padding: '4px 8px',
                  borderRadius: '12px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-surface)',
                  color: 'var(--text-secondary)',
                  fontSize: '0.6875rem',
                  cursor: 'pointer',
                  textAlign: 'left',
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
      </div>
    </div>
  );
}
