/**
 * [Application Root Component]
 * 5계층 아키텍처 조율:
 * - Controllers: useAuthController, useTopBarController, useWikiController, useDashboardController, useReviewController
 * - Views: TopBar, DashboardView, WikiView, ReviewCenterView, AuthModal, SpotlightModal
 */

import React, { useState, useEffect } from 'react';
import { useAuthController } from './controllers/useAuthController';
import { useTopBarController } from './controllers/useTopBarController';
import { useWikiController } from './controllers/useWikiController';
import { useDashboardController } from './controllers/useDashboardController';
import { useReviewController } from './controllers/useReviewController';

import { TopBar } from './views/TopBar';
import { DashboardView } from './views/dashboard/DashboardView';
import { WikiView } from './views/wiki/WikiView';
import { ReviewCenterView } from './views/review/ReviewCenterView';
import { AuthModal } from './views/AuthModal';
import { SpotlightModal } from './views/SpotlightModal';

import {
  GitCompare,
  SearchCheck,
  ShieldAlert
} from 'lucide-react';

export default function App() {
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  // 계층 2: 컨트롤러 인스턴스
  const auth = useAuthController();
  const topbar = useTopBarController({ initialTab: 'wiki' });

  const wiki = useWikiController({
    initialConceptId: 'concept-tcb',
    currentUser: auth.currentUser,
    myAccessRequests: auth.myAccessRequests,
    onRefreshAuth: auth.refreshSession
  });

  const dashboard = useDashboardController({
    currentUser: auth.currentUser
  });

  const review = useReviewController({
    currentUser: auth.currentUser
  });

  return (
    <div className="app-container" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* ── 계층 1 View: 글로벌 탑바 ── */}
      <TopBar
        tabs={topbar.tabs}
        activeTab={topbar.activeTab}
        onSelectTab={topbar.setActiveTab}
        onOpenSearch={topbar.openSearch}
        currentUser={auth.currentUser}
        isAuthenticated={auth.isAuthenticated}
        roleBadge={auth.roleBadge}
        canAccessAdmin={auth.canAccessAdmin}
        onOpenLogin={auth.openLoginModal}
        onLogout={auth.logout}
        currentTheme={theme}
        onToggleTheme={toggleTheme}
      />

      {/* ── 메인 컨텐츠 영역 ── */}
      <main style={{ flex: 1, padding: '24px 32px', maxWidth: '1600px', margin: '0 auto', width: '100%' }}>
        {topbar.activeTab === 'home' && (
          <DashboardView
            dashboard={dashboard}
            currentUser={auth.currentUser}
            onNavigateWiki={(facet) => {
              wiki.changeFacet(facet);
              topbar.setActiveTab('wiki');
            }}
          />
        )}

        {topbar.activeTab === 'wiki' && (
          <WikiView
            wiki={wiki}
            currentUser={auth.currentUser}
          />
        )}

        {topbar.activeTab === 'comparison' && (
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '48px', textAlign: 'center' }}>
            <GitCompare size={48} style={{ color: 'var(--accent-primary)', margin: '0 auto 16px auto', display: 'block' }} />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 8px 0' }}>[Tab 2] 기술 대안 인과 탐구실</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Phase 4에서 2-Track 듀얼 입력 및 4단계 비교 매트릭스가 구현됩니다.</p>
          </div>
        )}

        {topbar.activeTab === 'review' && (
          <ReviewCenterView
            review={review}
            currentUser={auth.currentUser}
            wiki={wiki}
          />
        )}

        {topbar.activeTab === 'research' && (
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '48px', textAlign: 'center' }}>
            <SearchCheck size={48} style={{ color: 'var(--accent-primary)', margin: '0 auto 16px auto', display: 'block' }} />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 8px 0' }}>[Tab 4] 외부 문헌·백서 조사실</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Phase 5에서 글로벌 학술지 및 교차 분석 종합 리포트가 구현됩니다.</p>
          </div>
        )}

        {topbar.activeTab === 'admin' && (
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '48px', textAlign: 'center' }}>
            <ShieldAlert size={48} style={{ color: 'var(--accent-danger)', margin: '0 auto 16px auto', display: 'block' }} />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 8px 0' }}>[Admin] 수석 검토관 거버넌스 콘솔</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Phase 6에서 L3 비인가 열람 신청 심사 큐 및 엔지니어 계정 관리가 구현됩니다.</p>
          </div>
        )}
      </main>

      {/* ── 계층 1 View: 인증 모달 ── */}
      <AuthModal
        isOpen={auth.isAuthModalOpen}
        mode={auth.authMode}
        isLoading={auth.isLoading}
        error={auth.error}
        fieldErrors={auth.fieldErrors}
        onClose={auth.closeAuthModal}
        onSwitchMode={auth.switchAuthMode}
        onLogin={auth.login}
        onRegister={auth.register}
        onClearError={auth.clearError}
      />

      {/* ── 계층 1 View: 스포트라이트 검색 모달 ── */}
      <SpotlightModal
        isOpen={topbar.isSearchOpen}
        onClose={topbar.closeSearch}
        onSelectConcept={(conceptId) => {
          wiki.selectConcept(conceptId);
          topbar.setActiveTab('wiki');
        }}
      />
    </div>
  );
}
