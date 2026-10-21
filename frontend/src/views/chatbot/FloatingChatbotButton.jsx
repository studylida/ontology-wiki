/**
 * [계층 1] FloatingChatbotButton View (Pure Dumb UI Component)
 * - 우하단 플로팅 챗봇 트리거 버튼 및 실시간 AI 활성 인디케이터
 */

import React from 'react';
import { Bot, MessageSquare } from 'lucide-react';

export function FloatingChatbotButton({ isOpen, onToggle }) {
  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        onToggle();
      }}
      className="floating-chat-fab"
      id="floating-chat-fab"
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '12px 20px',
        borderRadius: '28px',
        background: 'var(--accent-primary, #2563eb)',
        color: '#ffffff',
        border: 'none',
        fontSize: '0.875rem',
        fontWeight: 700,
        boxShadow: '0 6px 20px rgba(37, 99, 235, 0.45)',
        cursor: 'pointer',
        transition: 'transform 0.2s ease, box-shadow 0.2s ease'
      }}
      title="[F-01] 반도체 인과 온톨로지 AI 어시스턴트 열기"
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px) scale(1.03)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0) scale(1)';
      }}
    >
      <Bot size={20} />
      <span>온톨로지 챗</span>

      {/* 실시간 Live 인디케이터 도트 */}
      <span
        style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          background: '#10b981',
          border: '1.5px solid #fff',
          display: 'inline-block'
        }}
      />
    </button>
  );
}
