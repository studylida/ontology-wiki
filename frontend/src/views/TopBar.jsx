/**
 * [계층 1] TopBar View (Pure Dumb UI Component)
 * - 비즈니스 로직 0줄: 모든 상태와 액션은 Controller에서 주입받음
 * - transitions.dev sliding-tabs-container 표준 적용
 * - 관리자 콘솔 양방향 자동 토글 및 RBAC 배지 렌더링
 */

import React from 'react';
import { Search, LogIn, LogOut, Settings, ArrowLeft, Sun, Moon, Cpu } from 'lucide-react';

export function TopBar({
  tabs,
  activeTab,
  onSelectTab,
  onOpenSearch,
  currentUser,
  isAuthenticated,
  roleBadge,
  canAccessAdmin,
  onOpenLogin,
  onLogout,
  currentTheme = 'light',
  onToggleTheme
}) {
  return (
    <header className="topbar">
      {/* ── 좌측: 브랜드 로고 & 버전 ── */}
      <div className="topbar-left">
        <div
          className="brand-logo"
          style={{ cursor: 'pointer' }}
          onClick={() => onSelectTab('wiki')}
        >
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              background: 'var(--accent-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff'
            }}
          >
            <Cpu size={18} />
          </div>
          <span>Ontology Wiki</span>
        </div>

        {/* ── 중앙: 4대 작업 공간 탭 스위처 (Transitions.dev sliding-tabs) ── */}
        <nav className="sliding-tabs-container" aria-label="작업 공간 내비게이션">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                className={`sliding-tab-item ${isActive ? 'active' : ''}`}
                onClick={() => onSelectTab(tab.id)}
              >
                {tab.badge && (
                  <span
                    style={{
                      fontSize: '0.6875rem',
                      padding: '1px 5px',
                      borderRadius: '4px',
                      background: isActive ? 'var(--accent-primary-light)' : 'var(--bg-surface-3)',
                      color: isActive ? 'var(--accent-primary)' : 'var(--text-muted)',
                      marginRight: '6px',
                      fontWeight: 600
                    }}
                  >
                    {tab.badge}
                  </span>
                )}
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* ── 우측: 검색, 관리자 콘솔 토글, 테마, 사용자 프로필/인증 ── */}
      <div className="topbar-right">
        {/* Spotlight 검색 트리거 버튼 */}
        <button
          type="button"
          className="search-trigger-btn"
          onClick={onOpenSearch}
          title="단축키: Ctrl+K / ⌘K"
        >
          <Search size={14} />
          <span>지식·수식 검색...</span>
          <kbd
            style={{
              fontSize: '0.6875rem',
              padding: '1px 5px',
              background: 'var(--bg-surface-3)',
              borderRadius: '4px',
              color: 'var(--text-muted)'
            }}
          >
            ⌘K
          </kbd>
        </button>

        {/* Level >= 3 관리자 콘솔 양방향 토글 버튼 */}
        {canAccessAdmin && (
          <button
            type="button"
            className="settings-trigger-btn"
            onClick={() => onSelectTab(activeTab === 'admin' ? 'wiki' : 'admin')}
            style={{
              borderColor: activeTab === 'admin' ? 'var(--accent-primary)' : 'var(--border-color)',
              background: activeTab === 'admin' ? 'var(--accent-primary-light)' : 'var(--bg-surface-2)'
            }}
          >
            {activeTab === 'admin' ? (
              <>
                <ArrowLeft size={14} />
                <span>사용자 화면 ➔</span>
              </>
            ) : (
              <>
                <Settings size={14} />
                <span>관리자 콘솔</span>
              </>
            )}
          </button>
        )}

        {/* 다크/라이트 테마 토글 버튼 */}
        {onToggleTheme && (
          <button
            type="button"
            onClick={onToggleTheme}
            aria-label="테마 전환"
            style={{
              background: 'var(--bg-surface-2)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              padding: '6px 8px',
              cursor: 'pointer',
              color: 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            {currentTheme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
          </button>
        )}

        {/* 사용자 인증 상태 분기 */}
        {isAuthenticated && currentUser ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* RBAC 권한 배지 */}
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '3px 8px',
                borderRadius: '6px',
                fontSize: '0.75rem',
                fontWeight: 600,
                background: roleBadge.bgStyle,
                color: roleBadge.textStyle,
                border: `1px solid ${roleBadge.borderStyle}`
              }}
            >
              <span>{roleBadge.icon}</span>
              <span>{roleBadge.label}</span>
            </div>

            {/* 사용자 이름 및 부서 */}
            <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
              <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                {currentUser.name}
              </span>
              <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                {currentUser.department}
              </span>
            </div>

            {/* 로그아웃 버튼 */}
            <button
              type="button"
              onClick={onLogout}
              title="로그아웃"
              style={{
                background: 'transparent',
                border: '1px solid var(--border-color)',
                borderRadius: '6px',
                padding: '6px',
                cursor: 'pointer',
                color: 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                marginLeft: '4px'
              }}
            >
              <LogOut size={14} />
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={onOpenLogin}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'var(--accent-primary)',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 14px',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'background 0.2s ease'
            }}
          >
            <LogIn size={14} />
            <span>로그인 / 등록</span>
          </button>
        )}
      </div>
    </header>
  );
}
