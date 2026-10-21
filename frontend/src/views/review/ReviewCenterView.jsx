/**
 * [계층 1] ReviewCenterView Orchestrator (Pure Dumb UI Component)
 * - Tab 3 지식 검토·승인 거버넌스 센터 종합 화면
 * - 비즈니스 로직 0줄: useReviewController에서 주입받은 상태와 핸들러만 바인딩
 */

import React from 'react';
import { TicketQueueSidebar } from './TicketQueueSidebar';
import { PresenceBanner } from './PresenceBanner';
import { TwoSegmentEditor } from './TwoSegmentEditor';
import { DirectiveInputBar } from './DirectiveInputBar';
import { SemanticApprovalModal } from './SemanticApprovalModal';
import { RejectModal } from './RejectModal';
import { WikiPreviewModal } from './WikiPreviewModal';
import { AuditTrailModal } from './AuditTrailModal';
import { LockoutModal } from './LockoutModal';
import { NewConceptModal } from '../wiki/NewConceptModal';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

export function ReviewCenterView({
  review,
  currentUser,
  wiki
}) {
  const {
    statusFilter,
    setStatusFilter,
    ticketList,
    selectedTicketId,
    currentTicket,
    workingDraft,
    setWorkingDraft,
    auditLogs,
    presenceLock,
    isEditorDisabled,
    computedSemanticVersion,
    isLoading,
    isActionLoading,
    error,
    notification,
    isApproveModalOpen,
    isRejectModalOpen,
    isPreviewModalOpen,
    previewData,
    isAuditModalOpen,
    isLockoutModalOpen,
    selectTicket,
    takeoverLock,
    applyDirective,
    saveHumanEdits,
    openWikiPreview,
    openApproveModal,
    closeApproveModal,
    openRejectModal,
    closeRejectModal,
    closePreviewModal,
    openAuditModal,
    closeAuditModal,
    closeLockoutModal,
    executeApprove,
    executeReject,
    clearNotification
  } = review;

  return (
    <div style={{ display: 'flex', gap: '24px', alignItems: 'flex-start' }}>
      {/* ── 좌측 패널: 거버넌스 티켓 큐 사이드바 ── */}
      <TicketQueueSidebar
        ticketList={ticketList}
        selectedTicketId={selectedTicketId}
        statusFilter={statusFilter}
        isLoading={isLoading}
        onSelectStatus={setStatusFilter}
        onSelectTicket={selectTicket}
      />

      {/* ── 중앙 본문 패널: 2-Segment 편집기 및 거버넌스 제어 ── */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* 알림 토스트 / 피드백 배너 */}
        {notification && (
          <div
            style={{
              padding: '12px 18px',
              borderRadius: '8px',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '0.8125rem',
              fontWeight: 500,
              background:
                notification.type === 'error'
                  ? 'var(--accent-danger-light)'
                  : notification.type === 'warning'
                  ? 'var(--accent-warning-light)'
                  : 'var(--accent-success-light)',
              color:
                notification.type === 'error'
                  ? 'var(--accent-danger)'
                  : notification.type === 'warning'
                  ? 'var(--accent-warning)'
                  : 'var(--accent-success)',
              border: `1px solid ${
                notification.type === 'error'
                  ? 'rgba(239, 68, 68, 0.25)'
                  : notification.type === 'warning'
                  ? 'rgba(245, 158, 11, 0.25)'
                  : 'rgba(16, 185, 129, 0.25)'
              }`
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {notification.type === 'error' ? (
                <AlertCircle size={16} />
              ) : (
                <CheckCircle2 size={16} />
              )}
              <span>{notification.message}</span>
            </div>
            <button
              type="button"
              onClick={clearNotification}
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'inherit', fontWeight: 700 }}
            >
              ✕
            </button>
          </div>
        )}

        {/* 10분 Presence Lock 상단 배너 */}
        <PresenceBanner
          presenceLock={presenceLock}
          isEditorDisabled={isEditorDisabled}
          currentUser={currentUser}
          ticketStatus={currentTicket?.status}
          onTakeoverLock={takeoverLock}
          onOpenAuditModal={openAuditModal}
          onOpenNewConceptModal={wiki?.openNewConceptModal}
        />

        {/* 2-Segment 편집기 */}
        <TwoSegmentEditor
          currentTicket={currentTicket}
          workingDraft={workingDraft}
          isEditorDisabled={isEditorDisabled}
          isActionLoading={isActionLoading}
          onDraftChange={setWorkingDraft}
          onSaveDraft={saveHumanEdits}
          onOpenWikiPreview={openWikiPreview}
          onOpenApproveModal={openApproveModal}
          onOpenRejectModal={openRejectModal}
        />

        {/* 전문가 자연어 보완 지시문 입력 바 & 3대 무결성 진단 지표 */}
        <DirectiveInputBar
          integrityReport={currentTicket?.integrityReport}
          directiveHistory={currentTicket?.directiveHistory}
          isActionLoading={isActionLoading}
          isEditorDisabled={isEditorDisabled}
          onApplyDirective={applyDirective}
        />
      </div>

      {/* ── 전역 모달 팝업들 ── */}
      <SemanticApprovalModal
        isOpen={isApproveModalOpen}
        currentVersion={currentTicket?.currentVersion || 'v1.2.0'}
        computedSemanticVersion={computedSemanticVersion}
        onClose={closeApproveModal}
        onApprove={executeApprove}
      />

      <RejectModal
        isOpen={isRejectModalOpen}
        ticketTitle={currentTicket?.title || selectedTicketId}
        onClose={closeRejectModal}
        onReject={executeReject}
      />

      <WikiPreviewModal
        isOpen={isPreviewModalOpen}
        previewData={previewData}
        onClose={closePreviewModal}
      />

      <AuditTrailModal
        isOpen={isAuditModalOpen}
        ticketId={selectedTicketId}
        auditLogs={auditLogs}
        onClose={closeAuditModal}
      />

      <LockoutModal
        isOpen={isLockoutModalOpen}
        onClose={closeLockoutModal}
      />

      {wiki && (
        <NewConceptModal
          isOpen={wiki.isNewConceptModalOpen}
          currentUser={currentUser}
          isRecommending={wiki.isRecommendingPlacement}
          placementRecommendation={wiki.placementRecommendation}
          onClose={wiki.closeNewConceptModal}
          onRequestRecommendation={wiki.requestPlacementRecommendation}
          onSubmit={wiki.submitNewConceptTicket}
        />
      )}
    </div>
  );
}
