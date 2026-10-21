/**
 * [계층 2] ReviewController Hook
 * Tab 3 검토·승인 거버넌스 센터의 모든 반응형 상태와 10분 Presence Lock 조율기
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { reviewRepo } from '../repositories/reviewRepo';
import { citationIntegrityService } from '../services/citationIntegrityService';
import { semanticVersionService } from '../services/semanticVersionService';

export function useReviewController({ currentUser } = {}) {
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'pending' | 'approved' | 'rejected'
  const [ticketList, setTicketList] = useState([]);
  const [selectedTicketId, setSelectedTicketId] = useState(null);
  const [currentTicket, setCurrentTicket] = useState(null);
  const [workingDraft, setWorkingDraft] = useState('');
  const [auditLogs, setAuditLogs] = useState([]);

  // 로딩 & 피드백 상태
  const [isLoading, setIsLoading] = useState(false);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);

  // 10분 Presence Lock 상태
  const [presenceLock, setPresenceLock] = useState({
    isLocked: false,
    holder: null,
    isHeldByMe: false,
    remainingSeconds: 600,
    maxHoldSeconds: 600
  });
  const [isEditorDisabled, setIsEditorDisabled] = useState(false);

  // 모달 제어 상태
  const [isApproveModalOpen, setIsApproveModalOpen] = useState(false);
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);
  const [isLockoutModalOpen, setIsLockoutModalOpen] = useState(false);

  // 타이머 Refs
  const countdownTimerRef = useRef(null);
  const heartbeatTimerRef = useRef(null);

  const clearTimers = () => {
    if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
    if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);
  };

  /**
   * 10분 초과 시 편집기 잠금 처리 (Lockout)
   */
  const lockoutEditor = useCallback(() => {
    clearTimers();
    setIsEditorDisabled(true);
    setPresenceLock((prev) => ({ ...prev, isHeldByMe: false, isLocked: false, remainingSeconds: 0 }));
    setIsLockoutModalOpen(true);
  }, []);

  /**
   * 타이머 가동 (1초 카운트다운 + 15초 하트비트)
   */
  const startPresenceTimers = useCallback((ticketId) => {
    clearTimers();
    setIsEditorDisabled(false);

    // 1초 카운트다운
    countdownTimerRef.current = setInterval(() => {
      setPresenceLock((prev) => {
        const next = prev.remainingSeconds - 1;
        // 1분 전(60초) 사전 경고
        if (next === 60) {
          setNotification({
            type: 'warning',
            message: '⏳ 1분 후 편집 세션이 자동 만료됩니다. 작업 내용을 저장하세요.'
          });
        }
        // 0초 도달 시 강제 반환
        if (next <= 0) {
          lockoutEditor();
          return { ...prev, remainingSeconds: 0, isHeldByMe: false };
        }
        return { ...prev, remainingSeconds: next };
      });
    }, 1000);

    // 15초 주기 하트비트 갱신
    heartbeatTimerRef.current = setInterval(async () => {
      try {
        await reviewRepo.managePresence(ticketId, {
          action: 'renew',
          userId: currentUser?.username || 'anonymous_reviewer'
        });
      } catch (err) {
        console.warn('Heartbeat renew failed:', err);
      }
    }, 15000);
  }, [currentUser, lockoutEditor]);

  /**
   * 티켓 목록 로드
   */
  const loadTickets = useCallback(async (status = 'all') => {
    setIsLoading(true);
    setError(null);
    try {
      const filterParam = status === 'all' ? undefined : status;
      const res = await reviewRepo.getTickets({ status: filterParam });
      setTicketList(res || []);
      return res || [];
    } catch (err) {
      setError(err.message || '티켓 목록을 불러오지 못했습니다.');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * 락 획득 시도
   */
  const acquireLock = useCallback(async (ticketId) => {
    const userId = currentUser?.username || 'anonymous_reviewer';
    try {
      const res = await reviewRepo.managePresence(ticketId, {
        action: 'acquire',
        userId,
        ttl: 600
      });
      if (res.acquired) {
        setPresenceLock({
          isLocked: true,
          holder: userId,
          isHeldByMe: true,
          remainingSeconds: 600,
          maxHoldSeconds: 600
        });
        startPresenceTimers(ticketId);
      } else {
        setPresenceLock({
          isLocked: true,
          holder: res.holder,
          isHeldByMe: false,
          remainingSeconds: 0,
          maxHoldSeconds: 600
        });
        setIsEditorDisabled(true);
      }
    } catch {
      setIsEditorDisabled(true);
    }
  }, [currentUser, startPresenceTimers]);

  /**
   * 타인 만료 시 편집 락 인계받기 (Steal/Takeover)
   */
  const takeoverLock = useCallback(async () => {
    if (!selectedTicketId) return;
    const userId = currentUser?.username || 'anonymous_reviewer';
    setIsActionLoading(true);
    try {
      const res = await reviewRepo.managePresence(selectedTicketId, {
        action: 'steal',
        userId,
        ttl: 600
      });
      if (res.acquired) {
        setPresenceLock({
          isLocked: true,
          holder: userId,
          isHeldByMe: true,
          remainingSeconds: 600,
          maxHoldSeconds: 600
        });
        startPresenceTimers(selectedTicketId);
        setNotification({ type: 'success', message: '편집 세션을 안전하게 인계받았습니다.' });
      }
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '세션 인계에 실패했습니다.' });
    } finally {
      setIsActionLoading(false);
    }
  }, [selectedTicketId, currentUser, startPresenceTimers]);

  /**
   * 편집 락 명시적 해제
   */
  const releaseLock = useCallback(async () => {
    if (!selectedTicketId) return;
    clearTimers();
    const userId = currentUser?.username || 'anonymous_reviewer';
    try {
      await reviewRepo.managePresence(selectedTicketId, {
        action: 'release',
        userId
      });
    } catch (err) {
      console.warn('Release lock failed:', err);
    }
    setPresenceLock({
      isLocked: false,
      holder: null,
      isHeldByMe: false,
      remainingSeconds: 600,
      maxHoldSeconds: 600
    });
  }, [selectedTicketId, currentUser]);

  /**
   * 티켓 선택
   */
  const selectTicket = useCallback(async (ticketId) => {
    clearTimers();
    setSelectedTicketId(ticketId);
    setIsLoading(true);
    try {
      const [detail, logs] = await Promise.all([
        reviewRepo.getTicketDetail(ticketId),
        reviewRepo.getAuditLogs(ticketId).catch(() => [])
      ]);

      setCurrentTicket(detail);
      setAuditLogs(logs || []);

      // 작업 초안 일원화: humanEdits 우선, 없으면 aiMergedDraft 또는 currentContent
      const initialDraft = detail.humanEdits || detail.aiMergedDraft || detail.currentContent || '';
      setWorkingDraft(initialDraft);

      // 대기 중(pending) 티켓일 때만 락 획득 시도
      if (detail.status === 'pending') {
        await acquireLock(ticketId);
      } else {
        setIsEditorDisabled(true);
        setPresenceLock({ isLocked: false, holder: null, isHeldByMe: false, remainingSeconds: 0, maxHoldSeconds: 600 });
      }
    } catch (err) {
      setError(err.message || '티켓 상세 정보를 불러올 수 없습니다.');
    } finally {
      setIsLoading(false);
    }
  }, [acquireLock]);

  /**
   * 전문가 자연어 보완 지시문 적용
   */
  const applyDirective = useCallback(async (directiveText, overrideReason = '') => {
    if (!selectedTicketId || !directiveText.trim()) return;
    setIsActionLoading(true);
    try {
      const updated = await reviewRepo.applyDirective(selectedTicketId, {
        directiveText: directiveText.trim(),
        overrideReason: overrideReason.trim(),
        allowCitationDeletion: false
      });
      setCurrentTicket(updated);
      setWorkingDraft(updated.humanEdits || updated.aiMergedDraft || workingDraft);
      setNotification({ type: 'success', message: '전문가 지시문이 성공적으로 머지되었습니다.' });
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '지시문 적용에 실패했습니다.' });
    } finally {
      setIsActionLoading(false);
    }
  }, [selectedTicketId, workingDraft]);

  /**
   * 전문가 직접 수정 저장 ([E-01] 인용구 자동 복원 탑재)
   */
  const saveHumanEdits = useCallback(async () => {
    if (!selectedTicketId || !currentTicket) return;
    setIsActionLoading(true);

    // 🌟 [E-01] 공인 출처 누락 검사 및 자동 복원 엔진 가동
    const integrityCheck = citationIntegrityService.validateAndRestore(
      currentTicket.currentContent || '',
      workingDraft,
      false
    );

    let finalContent = workingDraft;
    if (integrityCheck.isRestored) {
      finalContent = integrityCheck.restoredContent;
      setWorkingDraft(finalContent);
      setNotification({
        type: 'warning',
        message: `공인 출처(${integrityCheck.missingCitations.join(', ')}) 누락이 감지되어 원문 인용 근거가 본문 말미에 자동 복원되었습니다.`
      });
    }

    try {
      const updated = await reviewRepo.saveHumanEdits(selectedTicketId, {
        editedContent: finalContent,
        ticketVersion: currentTicket.ticketVersion || 1,
        allowCitationDeletion: false
      });
      setCurrentTicket(updated);
      if (!integrityCheck.isRestored) {
        setNotification({ type: 'success', message: '직접 편집 초안이 성공적으로 저장되었습니다.' });
      }
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '초안 저장에 실패했습니다.' });
    } finally {
      setIsActionLoading(false);
    }
  }, [selectedTicketId, currentTicket, workingDraft]);

  /**
   * 위키 미리보기 모달 열기
   */
  const openWikiPreview = useCallback(async () => {
    if (!selectedTicketId) return;
    setIsActionLoading(true);
    try {
      const prev = await reviewRepo.getWikiPreview(selectedTicketId, true);
      setPreviewData(prev);
      setIsPreviewModalOpen(true);
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '위키 미리보기를 생성하지 못했습니다.' });
    } finally {
      setIsActionLoading(false);
    }
  }, [selectedTicketId]);

  /**
   * 티켓 최종 승인
   */
  const executeApprove = useCallback(async ({ targetVersion, overrideReason }) => {
    if (!selectedTicketId) return;
    setIsActionLoading(true);
    try {
      await reviewRepo.approveTicket(selectedTicketId, {
        approvedBy: currentUser?.name || '수석 검토관',
        targetVersion,
        overrideReason,
        humanEdits: workingDraft,
        allowCitationDeletion: false
      });
      setIsApproveModalOpen(false);
      clearTimers();
      setNotification({ type: 'success', message: `티켓이 승인되어 버전 ${targetVersion}으로 공식 반영되었습니다.` });
      // 티켓 상세 및 목록 갱신
      await selectTicket(selectedTicketId);
      loadTickets(statusFilter);
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '승인 처리에 실패했습니다.' });
    } finally {
      setIsActionLoading(false);
    }
  }, [selectedTicketId, currentUser, workingDraft, selectTicket, loadTickets, statusFilter]);

  /**
   * 티켓 반려 의결
   */
  const executeReject = useCallback(async (rejectReason) => {
    if (!selectedTicketId) return;
    setIsActionLoading(true);
    try {
      await reviewRepo.rejectTicket(selectedTicketId, {
        rejectedBy: currentUser?.name || '수석 검토관',
        rejectReason
      });
      setIsRejectModalOpen(false);
      clearTimers();
      setNotification({ type: 'info', message: '티켓이 반려 의결되었습니다.' });
      await selectTicket(selectedTicketId);
      loadTickets(statusFilter);
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '반려 처리에 실패했습니다.' });
    } finally {
      setIsActionLoading(false);
    }
  }, [selectedTicketId, currentUser, selectTicket, loadTickets, statusFilter]);

  // 세맨틱 버전 자동 계산 속성
  const computedSemanticVersion = useMemo(() => {
    if (!currentTicket) return { targetVersion: 'v1.2.1', bumpType: 'PATCH', reasoning: '기본 보완' };
    return semanticVersionService.computeNextVersion(currentTicket.currentVersion || 'v1.2.0', {
      isNewConcept: currentTicket.reviewType === 'new_concept'
    });
  }, [currentTicket]);

  // 마운트 시 초기 목록 로드
  useEffect(() => {
    loadTickets('all').then((tickets) => {
      if (tickets.length > 0 && !selectedTicketId) {
        selectTicket(tickets[0].id);
      }
    });

    return () => clearTimers();
  }, []);

  return {
    statusFilter,
    setStatusFilter: (status) => {
      setStatusFilter(status);
      loadTickets(status);
    },
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
    releaseLock,
    applyDirective,
    saveHumanEdits,
    openWikiPreview,
    openApproveModal: () => setIsApproveModalOpen(true),
    closeApproveModal: () => setIsApproveModalOpen(false),
    openRejectModal: () => setIsRejectModalOpen(true),
    closeRejectModal: () => setIsRejectModalOpen(false),
    closePreviewModal: () => setIsPreviewModalOpen(false),
    openAuditModal: () => setIsAuditModalOpen(true),
    closeAuditModal: () => setIsAuditModalOpen(false),
    closeLockoutModal: () => setIsLockoutModalOpen(false),
    executeApprove,
    executeReject,
    clearNotification: () => setNotification(null)
  };
}
