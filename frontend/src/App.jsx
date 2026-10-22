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

  // ── History API 동기화 (브라우저 앞으로가기/뒤로가기 완벽 지원) ──
  const navigateTab = (targetTab, params = null, push = true) => {
    topbar.setActiveTab(targetTab);
    if (targetTab === 'comparison' && params?.comparisonSessionId) {
      comparison.handleUseResearchEvidence(params);
    } else if (targetTab === 'comparison' && params?.targetA && params?.targetB) {
      comparison.handleDirectCompare(params.targetA, params.targetB);
    } else if (targetTab === 'research' && params?.query) {
      research.handleDiscover(params.query, params.comparisonContext || null);
    } else if (targetTab === 'review' && params?.ticketId) {
      review.selectTicket(params.ticketId);
    }
    const hash = targetTab === 'wiki' && wiki.activeConceptId ? `#concept/${wiki.activeConceptId}` : `#${targetTab}`;
    if (push && window.location.hash !== hash) {
      window.history.pushState({ tab: targetTab, conceptId: wiki.activeConceptId, params }, '', hash);
    }
  };

  const navigateConcept = (conceptId, push = true) => {
    wiki.selectConcept(conceptId);
    topbar.setActiveTab('wiki');
    const hash = `#concept/${conceptId}`;
    if (push && window.location.hash !== hash) {
      window.history.pushState({ tab: 'wiki', conceptId }, '', hash);
    }
  };

  useEffect(() => {
    // 1. 초기 URL 해시 복원
    const hash = window.location.hash;
    if (hash.startsWith('#concept/')) {
      const cid = hash.replace('#concept/', '').trim();
      if (cid) {
        wiki.selectConcept(cid);
        topbar.setActiveTab('wiki');
      }
    } else if (hash.startsWith('#')) {
      const tab = hash.replace('#', '').trim();
      if (['home', 'wiki', 'comparison', 'review', 'research', 'admin'].includes(tab)) {
        topbar.setActiveTab(tab);
      }
    }

    // 2. 브라우저 뒤로가기 / 앞으로가기 (popstate) 이벤트 핸들러
    const handlePopState = (e) => {
      const state = e.state;
      if (state?.tab) {
        topbar.setActiveTab(state.tab);
        if (state.tab === 'wiki' && state.conceptId) {
          wiki.selectConcept(state.conceptId);
        }
      } else {
        const currentHash = window.location.hash;
        if (currentHash.startsWith('#concept/')) {
          const cid = currentHash.replace('#concept/', '').trim();
          if (cid) {
            wiki.selectConcept(cid);
            topbar.setActiveTab('wiki');
          }
        } else if (currentHash.startsWith('#')) {
          const tab = currentHash.replace('#', '').trim();
          if (tab) topbar.setActiveTab(tab);
        }
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const research = useResearchController({
    currentUser: auth.currentUser,
    onNavigateToTab: navigateTab
  });

  const comparison = useComparisonController({
    currentUser: auth.currentUser,
    onNavigateToTab: navigateTab
  });

  const admin = useAdminController({
    currentUser: auth.currentUser
  });

  const chatbot = useChatbotController({
    currentConceptId: wiki.selectedConceptId,
    activeTab: topbar.activeTab,
    onNavigateToTab: (targetTab, params) => {
      navigateTab(targetTab, params);
      if (targetTab === 'review' && params?.ticketId) {
        review.selectTicket(params.ticketId);
      }
    },
    onSelectConcept: (conceptId) => {
      navigateConcept(conceptId);
    }
  });

  return (
    <div className="app-container" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* ── 계층 1 View: 글로벌 탑바 ── */}
      <TopBar
        tabs={topbar.tabs}
        activeTab={topbar.activeTab}
        onSelectTab={navigateTab}
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
            onAskChatbot={(text) => {
              chatbot.sendWithText(`'${text}' 개념의 공정상 역할과 주요 인과 메커니즘을 설명해주세요.`);
            }}
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
          navigateConcept(conceptId);
        }}
      />
    </div>
  );
}
