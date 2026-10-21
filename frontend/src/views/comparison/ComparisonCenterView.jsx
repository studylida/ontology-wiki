/**
 * [계층 1] ComparisonCenterView (Pure Dumb UI Component)
 * - Tab 2 기술 대안 인과 탐구실 메인 오케스트레이터 뷰
 * - 화면 2-A (SetupTrackSelector) vs 화면 2-B (ComparisonHeaderBar + ComparisonMatrixTable + TailQuestionAdvisor)
 * - KnowledgeGapPopover & ExportTicketModal 포함
 */

import React from 'react';
import { SetupTrackSelector } from './SetupTrackSelector';
import { ComparisonHeaderBar } from './ComparisonHeaderBar';
import { ComparisonMatrixTable } from './ComparisonMatrixTable';
import { TailQuestionAdvisor } from './TailQuestionAdvisor';
import { KnowledgeGapPopover } from './KnowledgeGapPopover';
import { ExportTicketModal } from './ExportTicketModal';
import { CheckCircle2, AlertTriangle, X } from 'lucide-react';

const CONCEPT_NAME_MAP = {
  'concept-mrmuf': 'MR-MUF (매스 리플로우 몰디드 언더필)',
  'concept-tcb': 'TCB (열압착 본딩)',
  'concept-hybrid-bonding': '하이브리드 본딩 (Cu-Cu 다이렉트)',
  'concept-cowos': 'CoWoS (Chip-on-Wafer-on-Substrate)'
};

export function ComparisonCenterView({
  activeStep = 'setup',
  trackMode = 'track1',
  query = '',
  isClarifying = false,
  clarifyResult = null,
  targetA = 'concept-mrmuf',
  targetB = 'concept-tcb',
  domain = 'hbm3e_advanced',
  currentSession = null,
  matrixRows = [],
  selectedCategory = 'all',
  activeGapPopover = null,
  isMatrixLoading = false,
  chatHistory = [],
  isAdvising = false,
  isExportModalOpen = false,
  isActionLoading = false,
  notification = null,
  currentUser = null,

  setTrackMode,
  setQuery,
  setTargetA,
  setTargetB,
  setDomain,
  setSelectedCategory,
  handleClarifyQuery,
  handleSelectBranch,
  handleStartDirectComparison,
  handleResetToSetup,
  handleOpenGapPopover,
  handleCloseGapPopover,
  handleNavigateToResearch,
  handleSendTailQuestion,
  handleExportReviewTicket,
  openExportModal,
  closeExportModal,
  clearNotification
}) {
  const targetAName = CONCEPT_NAME_MAP[currentSession?.contextParams?.targetA || targetA] || targetA;
  const targetBName = CONCEPT_NAME_MAP[currentSession?.contextParams?.targetB || targetB] || targetB;

  return (
    <div className="tab-pane active" style={{ padding: '24px 32px', maxWidth: '1440px', margin: '0 auto' }}>
      {/* ── 상단 토스트 알림 (transitions.dev .toast-notification) ── */}
      {notification && (
        <div
          className="toast-notification show"
          style={{
            position: 'fixed',
            top: '80px',
            right: '24px',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 18px',
            borderRadius: '8px',
            fontSize: '0.8125rem',
            fontWeight: 600,
            boxShadow: '0 8px 24px rgba(0,0,0,0.18)',
            background: notification.type === 'error' ? '#ef4444' : notification.type === 'warning' ? '#f59e0b' : '#10b981',
            color: '#fff'
          }}
        >
          {notification.type === 'error' || notification.type === 'warning' ? (
            <AlertTriangle size={18} />
          ) : (
            <CheckCircle2 size={18} />
          )}
          <span>{notification.message}</span>
          <button
            type="button"
            onClick={clearNotification}
            style={{
              background: 'none',
              border: 'none',
              color: '#fff',
              cursor: 'pointer',
              marginLeft: '8px',
              padding: '2px'
            }}
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* ── 화면 2-A: 비교 조건 설정 (2-Track 듀얼 인터페이스) ── */}
      {activeStep === 'setup' && (
        <SetupTrackSelector
          trackMode={trackMode}
          query={query}
          isClarifying={isClarifying}
          clarifyResult={clarifyResult}
          targetA={targetA}
          targetB={targetB}
          domain={domain}
          isStartingComparison={isMatrixLoading}
          onSelectTrackMode={setTrackMode}
          onChangeQuery={setQuery}
          onClarifyQuery={handleClarifyQuery}
          onSelectBranch={handleSelectBranch}
          onChangeTargetA={setTargetA}
          onChangeTargetB={setTargetB}
          onChangeDomain={setDomain}
          onStartDirectComparison={handleStartDirectComparison}
        />
      )}

      {/* ── 화면 2-B: 심층 인과 비교 매트릭스 결과 뷰 ── */}
      {activeStep === 'matrix' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* 상단 조건 요약 바 */}
          <ComparisonHeaderBar
            currentSession={currentSession}
            targetAName={targetAName}
            targetBName={targetBName}
            onResetConditions={handleResetToSetup}
          />

          {/* 4단계 다차원 심층 인과 비교 매트릭스 */}
          <ComparisonMatrixTable
            matrixRows={matrixRows}
            selectedCategory={selectedCategory}
            targetAName={targetAName}
            targetBName={targetBName}
            isLoading={isMatrixLoading}
            onSelectCategory={setSelectedCategory}
            onOpenGapPopover={handleOpenGapPopover}
          />

          {/* 하단 대화형 꼬리질문 & 조건 튜닝 상담 */}
          <TailQuestionAdvisor
            chatHistory={chatHistory}
            isAdvising={isAdvising}
            onSendTailQuestion={handleSendTailQuestion}
            onOpenExportModal={openExportModal}
          />
        </div>
      )}

      {/* ── 모달 및 팝오버 ── */}
      <KnowledgeGapPopover
        activeGap={activeGapPopover}
        targetAName={targetAName}
        targetBName={targetBName}
        onClose={handleCloseGapPopover}
        onNavigateToResearch={handleNavigateToResearch}
      />

      <ExportTicketModal
        isOpen={isExportModalOpen}
        currentSession={currentSession}
        currentUser={currentUser}
        isLoading={isActionLoading}
        onClose={closeExportModal}
        onSubmit={handleExportReviewTicket}
      />
    </div>
  );
}
