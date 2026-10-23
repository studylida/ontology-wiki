/**
 * [계층 1] SettingsModal View (Pure Dumb UI Component)
 * - 사용자 AI Provider API Key (OpenAI / Gemini) 브라우저 로컬 저장 및 관리 모달
 * - transitions.dev modal-open-close 표준 클래스 준수
 */

import React, { useState, useEffect } from 'react';
import { Key, Shield, Check, X, Sparkles, ExternalLink, RefreshCw } from 'lucide-react';

export function SettingsModal({
  isOpen,
  onClose,
  initialOpenAiKey = '',
  initialGeminiKey = '',
  onSave
}) {
  const [openAiKey, setOpenAiKey] = useState('');
  const [geminiKey, setGeminiKey] = useState('');
  const [savedNotification, setSavedNotification] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setOpenAiKey(localStorage.getItem('semicon_wiki_openai_key') || '');
      setGeminiKey(localStorage.getItem('semicon_wiki_gemini_key') || '');
      setSavedNotification(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = (e) => {
    e.preventDefault();
    localStorage.setItem('semicon_wiki_openai_key', openAiKey.trim());
    localStorage.setItem('semicon_wiki_gemini_key', geminiKey.trim());
    if (onSave) {
      onSave({
        openAiKey: openAiKey.trim(),
        geminiKey: geminiKey.trim()
      });
    }
    setSavedNotification(true);
    setTimeout(() => {
      setSavedNotification(false);
      onClose();
    }, 800);
  };

  const handleClear = () => {
    localStorage.removeItem('semicon_wiki_openai_key');
    localStorage.removeItem('semicon_wiki_gemini_key');
    setOpenAiKey('');
    setGeminiKey('');
    if (onSave) {
      onSave({ openAiKey: '', geminiKey: '' });
    }
    setSavedNotification(true);
    setTimeout(() => {
      setSavedNotification(false);
      onClose();
    }, 800);
  };

  return (
    <div
      className="modal-backdrop open"
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0, 0, 0, 0.45)',
        backdropFilter: 'blur(3px)',
        zIndex: 11000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px'
      }}
    >
      <div
        className="modal-box open"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%',
          maxWidth: '520px',
          background: 'var(--bg-surface)',
          borderRadius: '14px',
          border: '1px solid var(--border-color)',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.25)',
          overflow: 'hidden'
        }}
      >
        {/* 헤더 */}
        <div
          style={{
            padding: '18px 24px',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--bg-surface-2)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'var(--accent-primary-light)',
                color: 'var(--accent-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Key size={18} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                AI 추론 엔진 API 설정
              </h3>
              <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                4-Tier Hybrid Gateway 개인 API 키 브라우저 연동
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              padding: '4px'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* 폼 본문 */}
        <form onSubmit={handleSave} style={{ padding: '20px 24px' }}>
          {/* 보안 가이드 배너 */}
          <div
            style={{
              padding: '10px 14px',
              borderRadius: '8px',
              background: 'var(--bg-surface-2)',
              border: '1px solid var(--border-color)',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px',
              fontSize: '0.75rem',
              color: 'var(--text-secondary)'
            }}
          >
            <Shield size={16} style={{ color: '#10b981', flexShrink: 0, marginTop: '2px' }} />
            <div>
              입력하신 API Key는 백엔드 서버 DB에 절대 영구 저장되지 않으며, 사용자 브라우저의 안전한 로컬 저장소에만 보관되어 REST 호출 시 헤더(X-OpenAI-Key / X-Gemini-Key)로 안전하게 전송됩니다.
            </div>
          </div>

          {/* OpenAI API Key 입력 */}
          <div style={{ marginBottom: '14px' }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.8125rem',
                fontWeight: 700,
                color: 'var(--text-primary)',
                marginBottom: '6px'
              }}
            >
              OpenAI API Key (GPT-4o / GPT-4o-mini)
            </label>
            <input
              type="password"
              value={openAiKey}
              onChange={(e) => setOpenAiKey(e.target.value)}
              placeholder="sk-..."
              autoComplete="off"
              style={{
                width: '100%',
                padding: '9px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface-2)',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.8125rem'
              }}
            />
          </div>

          {/* Gemini API Key 입력 */}
          <div style={{ marginBottom: '18px' }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.8125rem',
                fontWeight: 700,
                color: 'var(--text-primary)',
                marginBottom: '6px'
              }}
            >
              Google Gemini API Key (Gemini 2.5 Flash / Pro)
            </label>
            <input
              type="password"
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              placeholder="AIzaSy..."
              autoComplete="off"
              style={{
                width: '100%',
                padding: '9px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-surface-2)',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.8125rem'
              }}
            />
          </div>

          {/* 저장 완료 알림 배너 */}
          {savedNotification && (
            <div
              style={{
                padding: '8px 12px',
                borderRadius: '6px',
                background: 'var(--accent-success-light)',
                color: 'var(--accent-success)',
                fontSize: '0.75rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                marginBottom: '14px'
              }}
            >
              <Check size={14} />
              <span>설정이 브라우저에 안전하게 저장되었습니다.</span>
            </div>
          )}

          {/* 하단 액션 버튼 */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '12px' }}>
            <button
              type="button"
              onClick={handleClear}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                fontSize: '0.75rem',
                cursor: 'pointer',
                textDecoration: 'underline'
              }}
            >
              키 초기화 (삭제)
            </button>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                onClick={onClose}
                style={{
                  padding: '7px 14px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-surface-2)',
                  color: 'var(--text-secondary)',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                취소
              </button>
              <button
                type="submit"
                style={{
                  padding: '7px 18px',
                  borderRadius: '6px',
                  border: 'none',
                  background: 'var(--accent-primary)',
                  color: '#ffffff',
                  fontSize: '0.8125rem',
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                저장하기
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
