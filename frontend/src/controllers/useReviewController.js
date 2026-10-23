import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { reviewRepo } from '../repositories/reviewRepo';
import { semanticVersionService } from '../services/semanticVersionService';
import { draftChanges, equal, removedCitations } from '../services/reviewDraftService';

export function useReviewController({currentUser}={}) {
  const [statusFilter,setStatusFilter]=useState('all'), [ticketList,setTicketList]=useState([]);
  const [selectedTicketId,setSelectedTicketId]=useState(null), [currentTicket,setCurrentTicket]=useState(null);
  const [workingDraft,setDraft]=useState(null), [savedDraft,setSavedDraft]=useState(null);
  const [activeSection,setActiveSection]=useState('summary'), [pendingTicketId,setPendingTicketId]=useState(null);
  const [auditLogs,setAuditLogs]=useState([]), [reviewContent,setReviewContent]=useState(null);
  const [isContentLoading,setIsContentLoading]=useState(false), [contentError,setContentError]=useState(null);
  const selectedTicketRef=useRef(null), selectionRef=useRef(0), contentRequestRef=useRef(0), draftRef=useRef(null), savedRef=useRef(null);
  const contentViewer=`${currentUser?.id || currentUser?.username || 'anonymous'}:${currentUser?.level || 0}`;
  const viewerRef=useRef(contentViewer); viewerRef.current=contentViewer;
  const [draftViewer,setDraftViewer]=useState(null);
  const changes=useMemo(()=>draftChanges(savedDraft,workingDraft),[savedDraft,workingDraft]);
  const isDirty=Object.keys(changes).length>0;
  const valid=(id,viewer,generation)=>selectedTicketRef.current===id && viewerRef.current===viewer && selectionRef.current===generation;
  function installDraft(value) {
    const next=value?.content;
    if(!next) throw new Error('전체 편집 계약을 불러오지 못했습니다. 서버 코드 적용 상태를 확인하세요.');
    draftRef.current=savedRef.current=next;setDraft(next);setSavedDraft(next);setDraftViewer(viewerRef.current);
  }
  function setWorkingDraft(next) {draftRef.current=next;setDraft(next);setPreviewData(null);}
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
  const startPresenceTimers = useCallback((ticketId,generation) => {
    const viewer=contentViewer;
    clearTimers();
    setIsEditorDisabled(false);

    // 1초 카운트다운
    countdownTimerRef.current = setInterval(() => {
      if(!valid(ticketId,viewer,generation)) return;
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
        const res=await reviewRepo.managePresence(ticketId, {
          action: 'renew',
          userId: currentUser?.username || 'anonymous_reviewer'
        });
        if(valid(ticketId,viewer,generation) && !res.acquired) lockoutEditor();
      } catch (err) {
        if(valid(ticketId,viewer,generation)) lockoutEditor();
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
  const acquireLock = useCallback(async (ticketId,generation) => {
    const viewer=contentViewer;
    const userId = currentUser?.username || 'anonymous_reviewer';
    try {
      const res = await reviewRepo.managePresence(ticketId, {
        action: 'acquire',
        userId,
        ttl: 600
      });
      if(!valid(ticketId,viewer,generation)) return;
      if (res.acquired) {
        setPresenceLock({
          isLocked: true,
          holder: userId,
          isHeldByMe: true,
          remainingSeconds: 600,
          maxHoldSeconds: 600
        });
        startPresenceTimers(ticketId,generation);
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
      if(valid(ticketId,viewer,generation)) setIsEditorDisabled(true);
    }
  }, [currentUser, startPresenceTimers]);

  /**
   * 타인 만료 시 편집 락 인계받기 (Steal/Takeover)
   */
  const takeoverLock = useCallback(async () => {
    const ticketId=selectedTicketId,viewer=contentViewer,generation=selectionRef.current;
    if (!selectedTicketId) return;
    const userId = currentUser?.username || 'anonymous_reviewer';
    setIsActionLoading(true);
    try {
      const res = await reviewRepo.managePresence(selectedTicketId, {
        action: 'steal',
        userId,
        ttl: 600
      });
      if(!valid(ticketId,viewer,generation)) return;
      if (res.acquired) {
        setPresenceLock({
          isLocked: true,
          holder: userId,
          isHeldByMe: true,
          remainingSeconds: 600,
          maxHoldSeconds: 600
        });
        startPresenceTimers(selectedTicketId,generation);
        setNotification({ type: 'success', message: '편집 세션을 안전하게 인계받았습니다.' });
      }
    } catch (err) {
      if(!valid(ticketId,viewer,generation)) return;
      setNotification({ type: 'error', message: err.message || '세션 인계에 실패했습니다.' });
    } finally {
      if(valid(ticketId,viewer,generation)) setIsActionLoading(false);
    }
  }, [selectedTicketId, currentUser, startPresenceTimers]);

  /**
   * 편집 락 명시적 해제
   */
  const releaseLock = useCallback(async () => {
    if (!selectedTicketId) return;
    const generation=selectionRef.current,viewer=contentViewer;
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
    if(!valid(selectedTicketId,viewer,generation)) return;
    setPresenceLock({
      isLocked: false,
      holder: null,
      isHeldByMe: false,
      remainingSeconds: 600,
      maxHoldSeconds: 600
    });
  }, [selectedTicketId, currentUser]);


  async function refreshReviewContent() {
    const id=selectedTicketRef.current, viewer=contentViewer, generation=selectionRef.current, request=++contentRequestRef.current;
    if(!id) return;
    setIsContentLoading(true);setContentError(null);
    try {
      const result=await reviewRepo.getWikiPreview(id,{});
      if(!valid(id,viewer,generation)||request!==contentRequestRef.current) return;
      if(!result.baselineConcept) throw new Error('현재 위키를 불러오지 못했습니다. 서버 코드 적용 상태를 확인하세요.');
      setReviewContent({...result,viewerKey:viewer});
    } catch(err) {if(valid(id,viewer,generation)&&request===contentRequestRef.current) setContentError(err.message);}
    finally {if(valid(id,viewer,generation)&&request===contentRequestRef.current) setIsContentLoading(false);}
  }
  async function selectTicket(id,force=false) {
    if(!force && selectedTicketRef.current===id) return;
    if(!force&&selectedTicketRef.current!==id&&Object.keys(draftChanges(savedRef.current,draftRef.current)).length) {setPendingTicketId(id);return;}
    const generation=++selectionRef.current;setIsActionLoading(false);
    clearTimers();selectedTicketRef.current=id;setSelectedTicketId(id);setReviewContent(null);setPreviewData(null);
    const viewer=contentViewer;setIsLoading(true);setContentError(null);setIsEditorDisabled(true);
    try {
      const [detail,logs]=await Promise.all([reviewRepo.getTicketDetail(id),reviewRepo.getAuditLogs(id).catch(()=>[])]);
      if(!valid(id,viewer,generation)) return;
      installDraft(detail.workingDraft);setCurrentTicket(detail);setAuditLogs(logs);setError(null);setIsLoading(false);
      if(detail.status==='pending') await acquireLock(id,generation);
      else setIsEditorDisabled(true);
      if(valid(id,viewer,generation)) await refreshReviewContent();
    } catch(err) {if(valid(id,viewer,generation)){setError(err.message);setContentError(err.message);}}
    finally {if(valid(id,viewer,generation))setIsLoading(false);}
  }
  async function persistDraft() {
    const id=selectedTicketId, viewer=contentViewer,generation=selectionRef.current;
    if(!id||!currentTicket||!workingDraft) throw new Error('편집 잠금과 권한을 먼저 확인해 주세요.');
    const changes=draftChanges(savedRef.current,draftRef.current);
    if(!Object.keys(changes).length && (currentTicket.editingMode==='structured'||isEditorDisabled)) return currentTicket;
    if(isEditorDisabled) throw new Error('작업본을 저장하려면 편집 잠금을 확인해 주세요.');
    const deprecation=draftRef.current.citationDeprecation;
    const deprecatedCitations=removedCitations(savedRef.current,draftRef.current);
    const result=await reviewRepo.saveHumanEdits(id,{ticketVersion:currentTicket.ticketVersion,changes,
      ...(deprecation?.allow?{allowCitationDeletion:true,deprecatedCitations,overrideReason:deprecation.reason}: {})});
    if(!valid(id,viewer,generation)) return null;
    installDraft(result.workingDraft);
    const ticket={...currentTicket,...result,id,editingMode:'structured'};setCurrentTicket(ticket);setPreviewData(null);
    return ticket;
  }
  async function saveHumanEdits() {
    const id=selectedTicketId, viewer=contentViewer,generation=selectionRef.current;setIsActionLoading(true);
    try {const ticket=await persistDraft();if(ticket){setNotification({type:'success',message:'모든 목차의 작업본을 저장했습니다.'});await refreshReviewContent();}return !!ticket;}
    catch(err){if(valid(id,viewer,generation))setNotification({type:'error',message:err.message});return false;}
    finally {if(valid(id,viewer,generation))setIsActionLoading(false);}
  }
  async function applyDirective(text,reason='',undo=false,scope='all') {
    const id=selectedTicketId, viewer=contentViewer,generation=selectionRef.current;setIsActionLoading(true);
    try {
      const ticket=await persistDraft();if(!ticket) return false;
      const updated=await reviewRepo.applyDirective(id,{directiveText:text,overrideReason:reason,undoLast:undo,structuredDraft:true,ticketVersion:ticket.ticketVersion,...(scope==='current'?{targetSections:[activeSection]}:{})});
      if(!valid(id,viewer,generation)) return false;
      const detail=await reviewRepo.getTicketDetail(id);if(!valid(id,viewer,generation))return false;
      installDraft(detail.workingDraft);setCurrentTicket({...detail,...updated,workingDraft:detail.workingDraft});
      await refreshReviewContent();setNotification({type:'success',message:undo?'지시문 이전 작업본으로 되돌렸습니다.':'보강 결과를 작업본에 반영했습니다. 각 목차와 출처를 확인하세요.'});return true;
    } catch(err){if(valid(id,viewer,generation))setNotification({type:'error',message:err.message});return false;}
    finally {if(valid(id,viewer,generation))setIsActionLoading(false);}
  }
  async function openWikiPreview(section=activeSection) {
    const id=selectedTicketId,viewer=contentViewer,generation=selectionRef.current;setIsActionLoading(true);
    try {
      const ticket=await persistDraft();if(!ticket)return;
      const data=await reviewRepo.getWikiPreview(id,{ticketVersion:ticket.ticketVersion});
      if(valid(id,viewer,generation)){setPreviewData({...data,viewerKey:viewer,focusSection:typeof section==='string'?section:activeSection});setIsPreviewModalOpen(true);}
    } catch(err){if(valid(id,viewer,generation))setNotification({type:'error',message:err.message});}
    finally {if(valid(id,viewer,generation))setIsActionLoading(false);}
  }
  async function executeApprove(options) {
    const id=selectedTicketId,viewer=contentViewer,generation=selectionRef.current;setIsActionLoading(true);
    try {
      const ticket=await persistDraft();if(!ticket)return;
      if(!previewData?.approvalOptions || previewData.ticketVersion!==ticket.ticketVersion || !equal(previewData.approvalOptions,options)) {
        const data=await reviewRepo.getWikiPreview(id,{ticketVersion:ticket.ticketVersion,targetVersion:options.targetVersion,...(options.conceptPlacement?{conceptPlacement:options.conceptPlacement}:{})});
        if(!valid(id,viewer,generation))return;
        setPreviewData({...data,viewerKey:viewer,focusSection:'summary',approvalOptions:options});setIsPreviewModalOpen(true);
        setNotification({type:'info',message:'선택한 승인 조건의 미리보기를 확인한 뒤 승인 버튼을 다시 눌러주세요.'});return;
      }
      await reviewRepo.approveTicket(id,{...options,ticketVersion:ticket.ticketVersion,previewSignature:previewData.previewSignature,allowCitationDeletion:false});
      if(!valid(id,viewer,generation))return;
      setIsApproveModalOpen(false);setPreviewData(null);await selectTicket(id,true);await loadTickets(statusFilter);setNotification({type:'success',message:'위키에 승인 내용을 반영했습니다.'});
    } catch(err){if(valid(id,viewer,generation))setNotification({type:'error',message:err.message});}
    finally {if(valid(id,viewer,generation))setIsActionLoading(false);}
  }
  async function executeReject(rejectReason) {
    const id=selectedTicketId,viewer=contentViewer,generation=selectionRef.current;setIsActionLoading(true);
    try {await reviewRepo.rejectTicket(id,{rejectReason,rejectedBy:currentUser?.name});if(valid(id,viewer,generation)){setIsRejectModalOpen(false);await selectTicket(id,true);await loadTickets(statusFilter);}}
    catch(err){if(valid(id,viewer,generation))setNotification({type:'error',message:err.message});}
    finally {if(valid(id,viewer,generation))setIsActionLoading(false);}
  }
  const computedSemanticVersion=useMemo(()=>semanticVersionService.computeNextVersion(currentTicket?.currentVersion||'v1.2.0',{isNewConcept:currentTicket?.reviewType==='new_concept'}),[currentTicket]);
  useEffect(()=>{
    selectionRef.current++;contentRequestRef.current++;clearTimers();setDraft(null);setSavedDraft(null);draftRef.current=savedRef.current=null;
    setCurrentTicket(null);setAuditLogs([]);setReviewContent(null);setPreviewData(null);setIsApproveModalOpen(false);setIsRejectModalOpen(false);setIsAuditModalOpen(false);setIsActionLoading(false);setPendingTicketId(null);
    if(currentUser?.level>=2) loadTickets('all').then(list=>{if(viewerRef.current===contentViewer&&list.length)selectTicket(selectedTicketRef.current||list[0].id,true);});
    return clearTimers;
  },[contentViewer]);
  useEffect(()=>{const guard=e=>{if(Object.keys(draftChanges(savedRef.current,draftRef.current)).length){e.preventDefault();e.returnValue='';}};window.addEventListener('beforeunload',guard);return()=>window.removeEventListener('beforeunload',guard);},[]);
  return {statusFilter,setStatusFilter:status=>{setStatusFilter(status);loadTickets(status);},ticketList,selectedTicketId,
    currentTicket:draftViewer===contentViewer?currentTicket:null,workingDraft:draftViewer===contentViewer?workingDraft:null,
    setWorkingDraft,activeSection,setActiveSection,isDirty,pendingTicketId,cancelTicketSwitch:()=>setPendingTicketId(null),
    discardAndSwitch:()=>{const id=pendingTicketId;setPendingTicketId(null);selectTicket(id,true);},
    saveAndSwitch:async()=>{if(await saveHumanEdits()){const id=pendingTicketId;setPendingTicketId(null);selectTicket(id,true);}},
    reviewContent:reviewContent?.viewerKey===contentViewer&&reviewContent.ticketId===selectedTicketId?reviewContent:null,
    isContentLoading,contentError,refreshReviewContent,auditLogs,presenceLock,isEditorDisabled,computedSemanticVersion,isLoading,isActionLoading,error,notification,
    isApproveModalOpen,isRejectModalOpen,isPreviewModalOpen:isPreviewModalOpen&&previewData?.viewerKey===contentViewer,
    previewData:previewData?.viewerKey===contentViewer?previewData:null,isAuditModalOpen,isLockoutModalOpen,
    selectTicket,takeoverLock,releaseLock,applyDirective,undoDirective:()=>applyDirective('이전 지시 되돌리기','',true),saveHumanEdits,openWikiPreview,
    openApproveModal:()=>setIsApproveModalOpen(true),closeApproveModal:()=>setIsApproveModalOpen(false),openRejectModal:()=>setIsRejectModalOpen(true),closeRejectModal:()=>setIsRejectModalOpen(false),
    closePreviewModal:()=>setIsPreviewModalOpen(false),openAuditModal:()=>setIsAuditModalOpen(true),closeAuditModal:()=>setIsAuditModalOpen(false),closeLockoutModal:()=>setIsLockoutModalOpen(false),executeApprove,executeReject,clearNotification:()=>setNotification(null)};
}
