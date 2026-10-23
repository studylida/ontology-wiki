import {ComparisonMarkdown, evidenceAnchor} from './ComparisonMarkdown';
import './comparison.css';
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

export function ComparisonCenterView({
  activeStep = 'setup',
  trackMode = 'track1',
  query = '',
  isClarifying = false,
  clarifyResult = null,
  targetA = '',
  targetB = '',
  domain = '',
  concepts = [],
  axisCandidates = [], selectedAxes = [], customAxisText = '', answers = {},
  setCustomAxisText, toggleAxis, setAnswer, handleConfirmTargets, draft, setDraftField, handleApplyDraft,
  categories = [],
  comparisonSummary = '',
  comparisonEvidences = [],
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
  const targetAName = currentSession?.contextParams?.targetAName || concepts.find((c) => c.id === targetA)?.title || targetA;
  const targetBName = currentSession?.contextParams?.targetBName || concepts.find((c) => c.id === targetB)?.title || targetB;

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
          concepts={concepts}
          isStartingComparison={isMatrixLoading}
          axisCandidates={axisCandidates} selectedAxes={selectedAxes} customAxisText={customAxisText}
          answers={answers} onCustomAxisTextChange={setCustomAxisText} onToggleAxis={toggleAxis}
          onAnswerChange={setAnswer} onConfirmTargets={handleConfirmTargets}
          draft={draft} onDraftFieldChange={setDraftField} onApplyDraft={handleApplyDraft} onResearch={handleNavigateToResearch}
          onSelectTrackMode={setTrackMode}
          onQueryChange={setQuery}
          onClarifyQuery={handleClarifyQuery}
          onTargetAChange={setTargetA}
          onTargetBChange={setTargetB}
          onDomainChange={setDomain}
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
            onResetToSetup={handleResetToSetup}
          />

          <section style={{ padding: '20px', background: 'var(--bg-surface)', border: '1px solid var(--border-color)', borderRadius: '12px' }} aria-busy={isMatrixLoading}>
            <h3>목적에 따른 비교 해설</h3>
            <ComparisonMarkdown evidences={comparisonEvidences}>{comparisonSummary}</ComparisonMarkdown>
            <button type="button" disabled={isMatrixLoading || isAdvising} onClick={() => handleNavigateToResearch()}
              style={{ padding: '8px 14px', border: '1px solid var(--accent-primary)', borderRadius: '6px', background: 'var(--accent-primary-light)', color: 'var(--accent-primary)', fontWeight: 600, cursor: 'pointer' }}>
              필요한 문헌 조사하기
            </button>
            {comparisonEvidences.length > 0 && <details style={{ marginTop: '12px' }}>
              <summary>비교에 사용한 자료 ({comparisonEvidences.length})</summary>
              {comparisonEvidences.map((item, index) => <p key={`${item.id}-${index}`} id={evidenceAnchor(item.id)}>
                [{item.id}] {item.sourceName} {item.retrievalStatus === 'metadata' ? '(서지정보만 확보)' : ''}<br />
                {item.externalUrl && <a href={item.externalUrl} target="_blank" rel="noopener noreferrer">출처 확인</a>}
                <span style={{ display: 'block', whiteSpace: 'pre-wrap' }}>{item.quote}</span>
              </p>)}
            </details>}
          </section>

          {/* 4단계 다차원 심층 인과 비교 매트릭스 */}
          <ComparisonMatrixTable
            matrixRows={matrixRows}
            categories={categories}
            selectedCategory={selectedCategory}
            targetAName={targetAName}
            targetBName={targetBName}
            isLoading={isMatrixLoading}
            onSelectCategory={setSelectedCategory}
            onOpenGapPopover={handleOpenGapPopover}
          />
          <p>목적별 평가는 관련 등록 설명과 공개 사양을 모아 보여줍니다. 조사에서 연결한 미검토 문헌은 해설 자료이며, 승인된 위키 사양으로 자동 반영하지 않습니다.</p>

          {/* 하단 대화형 꼬리질문 & 조건 튜닝 상담 */}
          <TailQuestionAdvisor
            evidences={comparisonEvidences}
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
