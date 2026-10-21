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
      onClick={onToggle}
      className="floating-chatbot-btn"
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 1000,
        width: '56px',
        height: '56px',
        borderRadius: '50%',
        background: 'var(--accent-primary)',
        color: '#fff',
        border: 'none',
        boxShadow: '0 8px 24px rgba(37, 99, 235, 0.35)',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'transform 0.2s ease, box-shadow 0.2s ease'
      }}
      title="[F-01] 반도체 인과 온톨로지 AI 어시스턴트 열기"
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'scale(1.08)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
      }}
    >
      <Bot size={26} />

      {/* 실시간 Live 인디케이터 도트 */}
      <span
        style={{
          position: 'absolute',
          top: '2px',
          right: '2px',
          width: '12px',
          height: '12px',
          borderRadius: '50%',
          background: '#10b981',
          border: '2px solid #fff'
        }}
      />
    </button>
  );
}
