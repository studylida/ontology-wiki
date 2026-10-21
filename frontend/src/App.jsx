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
import { useComparisonController } from './controllers/useComparisonController';
import { useResearchController } from './controllers/useResearchController';
import { useChatbotController } from './controllers/useChatbotController';
import { useAdminController } from './controllers/useAdminController';

import { TopBar } from './views/TopBar';
import { DashboardView } from './views/dashboard/DashboardView';
import { WikiView } from './views/wiki/WikiView';
import { ReviewCenterView } from './views/review/ReviewCenterView';
import { ComparisonCenterView } from './views/comparison/ComparisonCenterView';
import { ResearchCenterView } from './views/research/ResearchCenterView';
import { AdminConsoleView } from './views/admin/AdminConsoleView';
import { FloatingChatbotButton } from './views/chatbot/FloatingChatbotButton';
import { ChatbotDrawer } from './views/chatbot/ChatbotDrawer';
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

  const research = useResearchController({
    currentUser: auth.currentUser,
    onNavigateToTab: (targetTab, params) => {
      topbar.setActiveTab(targetTab);
      if (targetTab === 'review' && params?.ticketId) {
        review.selectTicket(params.ticketId);
      }
    }
  });

  const comparison = useComparisonController({
    currentUser: auth.currentUser,
    onNavigateToTab: (targetTab, params) => {
      topbar.setActiveTab(targetTab);
      if (targetTab === 'review' && params?.ticketId) {
        review.selectTicket(params.ticketId);
      } else if (targetTab === 'research' && params?.query) {
        research.setSearchTopic(params.query);
        research.handleDiscover(params.query);
      }
    }
  });

  const admin = useAdminController({
    currentUser: auth.currentUser
  });

  const chatbot = useChatbotController({
    currentConceptId: wiki.selectedConceptId,
    activeTab: topbar.activeTab,
    onNavigateToTab: (targetTab, params) => {
      topbar.setActiveTab(targetTab);
      if (targetTab === 'review' && params?.ticketId) {
        review.selectTicket(params.ticketId);
      }
    },
    onSelectConcept: (conceptId) => {
      wiki.selectConcept(conceptId);
      topbar.setActiveTab('wiki');
    }
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
          <ComparisonCenterView
            {...comparison}
            currentUser={auth.currentUser}
          />
        )}

        {topbar.activeTab === 'review' && (
          <ReviewCenterView
            review={review}
            currentUser={auth.currentUser}
            wiki={wiki}
          />
        )}

        {topbar.activeTab === 'research' && (
          <ResearchCenterView
            {...research}
            currentUser={auth.currentUser}
          />
        )}

        {topbar.activeTab === 'admin' && (
          <AdminConsoleView
            {...admin}
            currentUser={auth.currentUser}
          />
        )}
      </main>

      {/* ── 계층 1 View: [F-01] 플로팅 실시간 챗봇 ── */}
      <FloatingChatbotButton
        isOpen={chatbot.isOpen}
        onToggle={chatbot.toggleOpen}
      />
      <ChatbotDrawer
        {...chatbot}
        onClose={chatbot.closeChatbot}
      />

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
