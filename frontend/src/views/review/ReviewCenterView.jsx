/**
 * [계층 1] ReviewCenterView Orchestrator (Pure Dumb UI Component)
 * - Tab 3 지식 검토·승인 거버넌스 센터 종합 화면
 * - 비즈니스 로직 0줄: useReviewController에서 주입받은 상태와 핸들러만 바인딩
 */

import React, {useRef,useEffect} from 'react';
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
    reviewContent,
    isContentLoading,
    contentError,
    refreshReviewContent,
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
    undoDirective,
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
    <div className="review-center-layout" style={{ display: 'flex', gap: '24px', alignItems: 'flex-start' }}>
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
          reviewContent={reviewContent}
          isContentLoading={isContentLoading}
          contentError={contentError}
          onRetryContent={refreshReviewContent}
          currentUser={currentUser}
          workingDraft={workingDraft}
          activeSection={review.activeSection}
          onSectionChange={review.setActiveSection}
          isDirty={review.isDirty}
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
          canUndo={currentTicket?.canUndo}
          isActionLoading={isActionLoading}
          isEditorDisabled={isEditorDisabled}
          onApplyDirective={applyDirective}
          onUndoDirective={undoDirective}
        />
      </div>

      {review.pendingTicketId && <TicketSwitchPrompt review={review} busy={isActionLoading}/>}

      {/* ── 전역 모달 팝업들 ── */}
      <SemanticApprovalModal
        isOpen={isApproveModalOpen}
        currentVersion={currentTicket?.currentVersion || 'v1.2.0'}
        computedSemanticVersion={computedSemanticVersion}
        researchPlacement={currentTicket?.originType === '문헌조사' ? currentTicket.structuredPatches?.find((patch) => patch.path === '/concept')?.value : null}
        onClose={closeApproveModal}
        onApprove={executeApprove}
        isActionLoading={isActionLoading}
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
        currentUser={currentUser}
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

function TicketSwitchPrompt({review,busy}) {
  const ref=useRef(null);
  useEffect(()=>{ref.current.showModal();},[]);
  return <dialog ref={ref} className="native-modal-dialog" role="alertdialog" aria-label="미저장 작업본" onCancel={e=>{e.preventDefault();review.cancelTicketSwitch();}}>
    <div style={{padding:24}}><h3>저장하지 않은 변경이 있습니다.</h3><p>모든 목차의 변경을 저장한 뒤 이동할 수 있습니다.</p>
      <button type="button" disabled={busy} onClick={review.saveAndSwitch}>저장 후 이동</button><button type="button" disabled={busy} onClick={review.discardAndSwitch}>변경 버리고 이동</button><button type="button" disabled={busy} onClick={review.cancelTicketSwitch}>계속 편집</button>
    </div>
  </dialog>;
}
