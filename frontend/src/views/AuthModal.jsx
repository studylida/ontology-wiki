/**
 * [계층 1] AuthModal View (Pure Dumb UI Component)
 * - 비즈니스 로직 0줄: 모든 상태와 액션은 useAuthController에서 주입받음
 * - Modern Web Guidance: <dialog closedby="any"> 및 클릭 백드롭 폴백 탑재
 * - transitions.dev 모달 트랜지션 및 슬라이딩 탭 스타일 적용
 */

import React, { useRef, useEffect, useState } from 'react';
import { X, Shield, Lock, User, Building, LogIn, UserPlus } from 'lucide-react';

export function AuthModal({
  isOpen,
  mode, // 'login' | 'register'
  isLoading,
  error,
  fieldErrors,
  onClose,
  onSwitchMode,
  onLogin,
  onRegister,
  onClearError
}) {
  const dialogRef = useRef(null);

  // 로컬 폼 상태 (순수 입력값 보관용)
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    name: '',
    department: 'HBM패키징개발팀'
  });

  // 다이얼로그 open/close 제어 및 modern-web light-dismiss fallback
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (isOpen) {
      if (!dialog.open) {
        dialog.showModal();
      }
    } else {
      if (dialog.open) {
        dialog.close();
      }
    }

    // Modern Web Guidance: closedby 미지원 브라우저용 백드롭 클릭 폴백
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

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (error || fieldErrors?.[name]) {
      onClearError();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (mode === 'login') {
      onLogin({ username: formData.username, password: formData.password });
    } else {
      onRegister(formData);
    }
  };

  const handleQuickFill = (username, password) => {
    setFormData((prev) => ({ ...prev, username, password }));
    onClearError();
  };

  return (
    <dialog
      ref={dialogRef}
      closedby="any"
      aria-labelledby="authDialogTitle"
      className="native-modal-dialog"
      onClose={onClose}
    >
      <div style={{ padding: '24px' }}>
        {/* 모달 상단 헤더 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h3 id="authDialogTitle" style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              {mode === 'login' ? '사내 엔지니어 로그인' : '사내 엔지니어 회원가입'}
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
              반도체 공정·소자 인과 온톨로지 지식 거버넌스 시스템
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="닫기"
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              padding: '4px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* 탭 전환 (Transitions.dev sliding-tabs) */}
        <div className="sliding-tabs-container" style={{ width: '100%', marginBottom: '20px' }}>
          <button
            type="button"
            className={`sliding-tab-item ${mode === 'login' ? 'active' : ''}`}
            style={{ flex: 1, textAlign: 'center' }}
            onClick={() => onSwitchMode('login')}
          >
            <LogIn size={14} style={{ marginRight: '6px', verticalAlign: '-2px' }} />
            사내 로그인
          </button>
          <button
            type="button"
            className={`sliding-tab-item ${mode === 'register' ? 'active' : ''}`}
            style={{ flex: 1, textAlign: 'center' }}
            onClick={() => onSwitchMode('register')}
          >
            <UserPlus size={14} style={{ marginRight: '6px', verticalAlign: '-2px' }} />
            새 엔지니어 등록
          </button>
        </div>

        {/* 에러 피드백 */}
        {error && (
          <div
            style={{
              background: 'var(--accent-danger-light)',
              color: 'var(--accent-danger)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              borderRadius: '8px',
              padding: '10px 14px',
              fontSize: '0.8125rem',
              marginBottom: '16px'
            }}
          >
            {error}
          </div>
        )}

        {/* 입력 양식 폼 */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
              로그인 아이디 (사번/계정명)
            </label>
            <div style={{ position: 'relative' }}>
              <User size={16} style={{ position: 'absolute', left: '12px', top: '11px', color: 'var(--text-muted)' }} />
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="예: admin, chief_reviewer, engineer1"
                required
                style={{
                  width: '100%',
                  padding: '9px 12px 9px 36px',
                  borderRadius: '6px',
                  border: `1px solid ${fieldErrors?.username ? 'var(--accent-danger)' : 'var(--border-color)'}`,
                  background: 'var(--bg-surface-2)',
                  color: 'var(--text-primary)',
                  fontSize: '0.875rem'
                }}
              />
            </div>
            {fieldErrors?.username && (
              <span style={{ fontSize: '0.75rem', color: 'var(--accent-danger)', marginTop: '4px', display: 'block' }}>
                {fieldErrors.username}
              </span>
            )}
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
              비밀번호
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: '12px', top: '11px', color: 'var(--text-muted)' }} />
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="비밀번호를 입력하세요"
                required
                style={{
                  width: '100%',
                  padding: '9px 12px 9px 36px',
                  borderRadius: '6px',
                  border: `1px solid ${fieldErrors?.password ? 'var(--accent-danger)' : 'var(--border-color)'}`,
                  background: 'var(--bg-surface-2)',
                  color: 'var(--text-primary)',
                  fontSize: '0.875rem'
                }}
              />
            </div>
            {fieldErrors?.password && (
              <span style={{ fontSize: '0.75rem', color: 'var(--accent-danger)', marginTop: '4px', display: 'block' }}>
                {fieldErrors.password}
              </span>
            )}
          </div>

          {/* 회원가입 모드 추가 필드 */}
          {mode === 'register' && (
            <>
              <div>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
                  엔지니어 실명
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="예: 홍길동 책임연구원"
                  required
                  style={{
                    width: '100%',
                    padding: '9px 12px',
                    borderRadius: '6px',
                    border: `1px solid ${fieldErrors?.name ? 'var(--accent-danger)' : 'var(--border-color)'}`,
                    background: 'var(--bg-surface-2)',
                    color: 'var(--text-primary)',
                    fontSize: '0.875rem'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '6px' }}>
                  소속 부서
                </label>
                <div style={{ position: 'relative' }}>
                  <Building size={16} style={{ position: 'absolute', left: '12px', top: '11px', color: 'var(--text-muted)' }} />
                  <input
                    type="text"
                    name="department"
                    value={formData.department}
                    onChange={handleChange}
                    placeholder="예: HBM패키징개발팀, 첨단식각기술팀"
                    required
                    style={{
                      width: '100%',
                      padding: '9px 12px 9px 36px',
                      borderRadius: '6px',
                      border: `1px solid ${fieldErrors?.department ? 'var(--accent-danger)' : 'var(--border-color)'}`,
                      background: 'var(--bg-surface-2)',
                      color: 'var(--text-primary)',
                      fontSize: '0.875rem'
                    }}
                  />
                </div>
              </div>
            </>
          )}

          {/* 제출 버튼 */}
          <button
            type="submit"
            disabled={isLoading}
            style={{
              marginTop: '8px',
              padding: '11px 16px',
              borderRadius: '8px',
              border: 'none',
              background: 'var(--accent-primary)',
              color: '#ffffff',
              fontWeight: 600,
              fontSize: '0.875rem',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              opacity: isLoading ? 0.7 : 1,
              transition: 'background 0.2s ease'
            }}
          >
            {isLoading
              ? '인증 처리 중...'
              : mode === 'login'
              ? '사내 인증 로그인'
              : '새 계정 생성 및 바로 시작'}
          </button>
        </form>

        {/* 빠른 테스트용 프리셋 계정 버튼 (개발 및 검증 편의) */}
        {mode === 'login' && (
          <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border-color)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px', fontWeight: 600 }}>
              ⚡ 빠른 검증용 시딩 계정 원클릭 입력:
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                onClick={() => handleQuickFill('admin', 'admin2026!')}
                style={{
                  flex: 1,
                  padding: '6px 10px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-surface-2)',
                  color: 'var(--text-secondary)',
                  fontSize: '0.75rem',
                  cursor: 'pointer'
                }}
              >
                👑 관리자 (Level 4)
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('chief_reviewer', 'chief2026!')}
                style={{
                  flex: 1,
                  padding: '6px 10px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-surface-2)',
                  color: 'var(--text-secondary)',
                  fontSize: '0.75rem',
                  cursor: 'pointer'
                }}
              >
                🛡️ 수석 검토관 (Level 3)
              </button>
            </div>
          </div>
        )}
      </div>
    </dialog>
  );
}
