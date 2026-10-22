/**
 * [계층 1] ResearchCenterView (Pure Dumb UI Component)
 * - Tab 4 외부 문헌·백서 조사실 메인 오케스트레이터 뷰
 * - 2-Column 레이아웃: 좌측 히스토리 사이드바 + 우측 3단계 조사 파이프라인
 */

import React from 'react';
import { ResearchSidebar } from './ResearchSidebar';
import { ResearchSearchArea } from './ResearchSearchArea';
import { EvidenceFeedList } from './EvidenceFeedList';
import { SynthesisReportCard } from './SynthesisReportCard';
import { KnowledgeCandidateList } from './KnowledgeCandidateList';
import { ExportCandidateModal } from './ExportCandidateModal';
import { CheckCircle2, AlertTriangle, X } from 'lucide-react';

export function ResearchCenterView({
  activeStep = 'search',
  searchTopic = '',
  targetInstitutions = [],
  pastSessions = [],
  currentSessionId = null,
  evidenceFeed = [],
  selectedEvidenceIds = [],
  synthesisReport = null,
  candidates = [],
  isLoadingSessions = false,
  isDiscovering = false,
  isSynthesizing = false,
  isExporting = false,
  isExportCandidateModalOpen = false,
  candidateToExport = null,
  notification = null,
  currentUser = null,
  comparisonContext = null,
  discoveryNotice = '',
  usableSelectedIds = [],
  handleReturnToComparison,

  setSearchTopic,
  setActiveStep,
  selectPastSession,
  handleDiscover,
  toggleEvidenceSelection,
  selectAllEvidences,
  handleSynthesizeReport,
  toggleInstitution,
  openExportCandidateModal,
  closeExportCandidateModal,
  handleExportCandidateTicket,
  handleResetSearch,
  clearNotification
}) {
  return (
    <div className="tab-pane active" style={{ display: 'flex', gap: '24px', alignItems: 'flex-start' }}>
      {/* ── 글로벌 토스트 알림 ── */}
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

      {/* ── 좌측 과거 세션 사이드바 ── */}
      <ResearchSidebar
        pastSessions={pastSessions}
        currentSessionId={currentSessionId}
        isLoading={isLoadingSessions}
        onSelectSession={selectPastSession}
        onNewSearch={handleResetSearch}
      />

      {/* ── 우측 메인 워크스페이스 ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {comparisonContext && <section style={{ padding: '16px', background: 'var(--bg-surface)', border: '1px solid var(--accent-primary)', borderRadius: '10px' }}>
          <strong>비교를 보강하는 문헌 조사</strong>
          <p>{comparisonContext.originalQuestion}</p>
          <p>{comparisonContext.targetAName} / {comparisonContext.targetBName}{comparisonContext.gapAxis ? ` · 조사 항목: ${comparisonContext.gapAxis}` : ''}</p>
          {comparisonContext.conditions?.length > 0 && <p>추가 조건·질문: {comparisonContext.conditions.join(' / ')}</p>}
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button type="button" onClick={() => handleReturnToComparison(false)}
              style={{ padding: '8px 14px', border: '1px solid var(--border-color)', borderRadius: '6px', background: 'var(--bg-surface-2)', color: 'var(--text-primary)', cursor: 'pointer' }}>원래 비교로 돌아가기</button>
            <button type="button" disabled={isDiscovering || isSynthesizing || !usableSelectedIds.length} onClick={() => handleReturnToComparison(true)}
              style={{ padding: '8px 14px', border: '1px solid var(--accent-primary)', borderRadius: '6px', background: 'var(--accent-primary-light)', color: 'var(--accent-primary)', fontWeight: 600, cursor: 'pointer' }}>
              선택한 자료로 비교 보강 ({usableSelectedIds.length})
            </button>
          </div>
        </section>}
        {isDiscovering && <p role="status">관련 문헌을 조사하고 있습니다. 다른 탭으로 이동해도 이 화면의 요청은 계속됩니다.</p>}
        {discoveryNotice && <p role="status">{discoveryNotice}</p>}
        {/* 1단계: 검색 주제 및 필터 영역 */}
        {activeStep === 'search' && (
          <ResearchSearchArea
            searchTopic={searchTopic}
            targetInstitutions={targetInstitutions}
            isDiscovering={isDiscovering}
            onChangeSearchTopic={setSearchTopic}
            onToggleInstitution={toggleInstitution}
            onDiscover={handleDiscover}
          />
        )}

        {/* 2단계: 실측 문헌 피드 목록 */}
        {activeStep === 'feed' && (
          <EvidenceFeedList
            evidenceFeed={evidenceFeed}
            selectedEvidenceIds={selectedEvidenceIds}
            searchTopic={searchTopic}
            isSynthesizing={isSynthesizing}
            onToggleEvidence={toggleEvidenceSelection}
            onSelectAll={selectAllEvidences}
            onSynthesize={handleSynthesizeReport}
            onBackToSearch={() => setActiveStep('search')}
          />
        )}

        {/* 3단계: 종합 분석 리포트 & 온톨로지 지식 후보 */}
        {activeStep === 'report' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <button type="button" onClick={() => setActiveStep('feed')}>문헌 선택으로 돌아가기</button>
            <SynthesisReportCard synthesisReport={synthesisReport} />
            <KnowledgeCandidateList
              candidates={candidates}
              currentUser={currentUser}
              onOpenExportModal={openExportCandidateModal}
            />
          </div>
        )}
      </div>

      {/* ── 지식 후보 검토 티켓 발행 모달 ── */}
      <ExportCandidateModal
        isOpen={isExportCandidateModalOpen}
        candidate={candidateToExport}
        currentUser={currentUser}
        isLoading={isExporting}
        onClose={closeExportCandidateModal}
        onSubmit={handleExportCandidateTicket}
      />
    </div>
  );
}
