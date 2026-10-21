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
            onBackToSearch={handleResetSearch}
          />
        )}

        {/* 3단계: 종합 분석 리포트 & 온톨로지 지식 후보 */}
        {activeStep === 'report' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
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
