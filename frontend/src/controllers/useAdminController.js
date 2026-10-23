/**
 * [계층 2] AdminController Hook
 * [Admin] 수석 검토관 거버넌스 콘솔의 반응형 상태 및 심사/계정 관리 조율기
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { adminRepo } from '../repositories/adminRepo';
import { DOMAIN_FACET_LABELS } from '../types/concept.dto';

function prepareClassification(concepts) {
  const metadata = {};
  const defaults = {};
  for (const concept of concepts) {
    if (concept.classificationConflict && !concept.existingClassification && !concept.classificationConfirmed) {
      return { error: `${concept.title}: 원문 구간별 분류안을 확인하고 확정해주세요.`, metadata: {} };
    }
    if (concept.applyBlockers?.length) {
      return { error: concept.title + ': ' + concept.applyBlockers.join(' '), metadata: {} };
    }
    const item = { domainFacet: concept.domainFacet, category: (concept.category || '').trim(), scaleLevel: concept.scaleLevel };
    if (!DOMAIN_FACET_LABELS[item.domainFacet] || !Number.isInteger(item.scaleLevel) || item.scaleLevel < 1 || item.scaleLevel > 5 || !item.category || item.category.length > 64) {
      return { error: `${concept.title}: 분야·분류·규모를 확인해주세요.`, metadata: {} };
    }
    if (defaults[concept.conceptId] && JSON.stringify(defaults[concept.conceptId]) !== JSON.stringify(item)) {
      return { error: `${concept.title}: 문서별 분류안이 다릅니다. 분류를 정정하면 같은 개념의 모든 제안에 반영됩니다.`, metadata: {} };
    }
    defaults[concept.conceptId] = item;
    if (concept.classificationConfirmed) metadata[concept.conceptId] = item;
  }
  return { error: null, metadata };
}

export function useAdminController({ currentUser, onWikiApplied } = {}) {
  const [activeSubTab, setActiveSubTab] = useState('requests'); // 'requests' | 'users'
  const [accessRequests, setAccessRequests] = useState([]);
  const [users, setUsers] = useState([]);
  const [filterStatus, setFilterStatus] = useState('all');

  const [isLoading, setIsLoading] = useState(false);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  /**
   * L3 열람 신청 큐 로드
   */
  const loadAccessRequests = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await adminRepo.listAccessRequests();
      setAccessRequests(Array.isArray(res) ? res : []);
    } catch (err) {
      console.warn('Failed to load access requests:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * 엔지니어 계정 목록 로드
   */
  const loadUsers = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await adminRepo.listUsers({ limit: 50 });
      setUsers(Array.isArray(res) ? res : []);
    } catch (err) {
      console.warn('Failed to load users:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (currentUser?.level >= 3) {
      loadAccessRequests();
      loadUsers();
    }
  }, [currentUser, loadAccessRequests, loadUsers]);

  /**
   * L3 열람 신청 승인
   */
  const handleApproveRequest = useCallback(async (requestId) => {
    setIsActionLoading(true);
    try {
      await adminRepo.approveAccessRequest(requestId);
      setNotification({ type: 'success', message: 'L3 보안 문서 열람 신청이 승인되었습니다.' });
      loadAccessRequests();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '승인 처리에 실패했습니다.' });
    } finally {
      setIsActionLoading(false);
    }
  }, [loadAccessRequests]);

  /**
   * L3 열람 신청 반려
   */
  const handleRejectRequest = useCallback(async (requestId, reason = '') => {
    setIsActionLoading(true);
    try {
      await adminRepo.rejectAccessRequest(requestId, { reason });
      setNotification({ type: 'success', message: 'L3 보안 문서 열람 신청이 반려되었습니다.' });
      loadAccessRequests();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '반려 처리에 실패했습니다.' });
    } finally {
      setIsActionLoading(false);
    }
  }, [loadAccessRequests]);

  /**
   * 권한 레벨 변경 (승격/강등)
   */
  const handleUpdateUserLevel = useCallback(async (userId, newLevel) => {
    setIsActionLoading(true);
    try {
      await adminRepo.updateUserLevel(userId, { level: newLevel });
      setNotification({ type: 'success', message: `엔지니어 권한 레벨이 Level ${newLevel}로 변경되었습니다.` });
      loadUsers();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '권한 변경에 실패했습니다.' });
    } finally {
      setIsActionLoading(false);
    }
  }, [loadUsers]);

  /**
   * 계정 활성/비활성 토글
   */
  const handleToggleUserActive = useCallback(async (userId, currentActive, userLevel) => {
    setIsActionLoading(true);
    try {
      await adminRepo.updateUserLevel(userId, { level: userLevel, isActive: !currentActive });
      setNotification({
        type: 'success',
        message: !currentActive ? '계정이 활성화되었습니다.' : '계정이 비활성화되었습니다.'
      });
      loadUsers();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '계정 상태 변경에 실패했습니다.' });
    } finally {
      setIsActionLoading(false);
    }
  }, [loadUsers]);

  // -------------------------------------------------------------------------
  // [관리자 전용] 원천 기술 백서(Sources) 인제스천 및 지식 추출 상태
  // -------------------------------------------------------------------------
  const [sources, setSources] = useState([]);
  const [sourceSummary, setSourceSummary] = useState({ totalCount: 0, succeededCount: 0, pendingCount: 0, modifiedCount: 0 });
  const [selectedDocIds, setSelectedDocIds] = useState(new Set());
  const [isSourceLoading, setIsSourceLoading] = useState(false);

  // 추출 진행 모달 상태 (SSE 스트림)
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionConfirmation, setExtractionConfirmation] = useState(null);
  const [extractionRecovery, setExtractionRecovery] = useState(null);
  const extractionStreamActive = useRef(false);
  const extractionStreamVersion = useRef(0);
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);
  const [extractionProgress, setExtractionProgress] = useState({ current: 0, total: 0, currentTitle: '', currentPublisher: '', step: '대기 중' });
  const [extractionLogs, setExtractionLogs] = useState([]);
  const [isExtractionFinished, setIsExtractionFinished] = useState(false);
  const [extractionError, setExtractionError] = useState(null);

  // 위키 DTO 변경 미리보기 모달 상태
  const [previewData, setPreviewData] = useState(null);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [isApplying, setIsApplying] = useState(false);

  /**
   * sources/ 디렉터리 기술 백서 목록 로드
   */
  const loadSourceDocuments = useCallback(async () => {
    setIsSourceLoading(true);
    try {
      const res = await adminRepo.listSourceDocuments();
      if (res) {
        setSources(res.documents || []);
        setSourceSummary({
          totalCount: res.totalCount || 0,
          succeededCount: res.succeededCount || 0,
          pendingCount: res.pendingCount || 0,
          modifiedCount: res.modifiedCount || 0
        });
      }
    } catch (err) {
      console.warn('Failed to load source documents:', err);
    } finally {
      setIsSourceLoading(false);
    }
  }, []);

  // activeSubTab 변경 시 소스 목록 자동 로드
  useEffect(() => {
    if (activeSubTab === 'sources' && currentUser?.level >= 4) {
      loadSourceDocuments();
    }
  }, [activeSubTab, currentUser, loadSourceDocuments]);

  const handleToggleSelectDoc = useCallback((docId) => {
    setSelectedDocIds((prev) => {
      const next = new Set(prev);
      if (next.has(docId)) next.delete(docId);
      else next.add(docId);
      return next;
    });
  }, []);

  const handleSelectAllDocs = useCallback((docIds, isSelect) => {
    setSelectedDocIds((prev) => {
      const next = new Set(prev);
      if (isSelect) {
        docIds.forEach((id) => next.add(id));
      } else {
        docIds.forEach((id) => next.delete(id));
      }
      return next;
    });
  }, []);

  const handleClearDocSelection = useCallback(() => {
    setSelectedDocIds(new Set());
  }, []);

  /**
   * 확정된 실행 범위로 기존 SSE 추출을 시작한다.
   */
  const startExtraction = useCallback(async (docIds, forceReextract = false, { runId = null, resumeInterrupted = false, openProgress = true } = {}) => {
    if (extractionStreamActive.current || !docIds?.length) return;
    extractionStreamActive.current = true;
    extractionStreamVersion.current += 1;
    setExtractionRecovery(null);

    setIsExtracting(true);
    setIsExtractionFinished(false);
    setExtractionError(null);
    setPreviewData(null);
    setIsProgressModalOpen(openProgress);
    setExtractionLogs([]);
    setExtractionProgress({
      current: 0,
      total: docIds.length,
      currentTitle: '추출 준비 중...',
      currentPublisher: '',
      step: '추출 준비 중'
    });

    try {
      await adminRepo.streamExtractSources(
        { docIds, forceReextract, runId, resumeInterrupted },
        {
          onStart: (data) => {
            setExtractionProgress((prev) => ({
              ...prev,
              total: data.total || docIds.length,
              step: '2단계: 텍스트 정제 및 LLM 구조화 추출'
            }));
          },
          onProgress: (data) => {
            setExtractionProgress({
              current: Math.max(0, (data.current || 1) - 1),
              total: data.total || docIds.length,
              currentTitle: data.title || '',
              currentPublisher: data.publisher || '',
              step: data.step || 'LLM 지식 분석 중...'
            });
            setExtractionLogs((prev) => [
              ...prev,
              {
                docId: data.docId,
                title: data.title,
                type: 'info',
                message: `${data.publisher}: 지식 구조화 진행 중...`
              }
            ]);
          },
          onDocSuccess: (data) => {
            setExtractionProgress((prev) => ({ ...prev, current: data.current }));
            setExtractionLogs((prev) => [
              ...prev,
              {
                docId: data.docId,
                title: data.title,
                type: 'success',
                message: data.preserved ? '이전에 완료한 추출 결과를 그대로 유지했습니다.' : `개념 후보 ${data.conceptsCount || 0}개, 관계 후보 ${data.relationsCount || 0}개 추출 완료`
              }
            ]);
          },
          onDocError: (data) => {
            setExtractionProgress((prev) => ({ ...prev, current: data.current }));
            setExtractionLogs((prev) => [
              ...prev,
              {
                docId: data.docId,
                title: data.title,
                type: 'error',
                message: data.errorMessage || data.message || '추출 실패'
              }
            ]);
          },
          onDocSkipped: (data) => {
            setExtractionProgress((prev) => ({ ...prev, current: data.current }));
            setExtractionLogs((prev) => [...prev, { docId: data.docId, title: data.title, type: 'skipped', message: '이전 추출 성공 결과가 있어 건너뛰었습니다.' }]);
          },
          onFinished: (data) => {
            setIsExtracting(false);
            setIsExtractionFinished(true);
            setPreviewData(data);
            setExtractionProgress((prev) => ({
              ...prev,
              current: prev.total,
              step: `성공 ${data.totalSucceeded || 0}건 · 실패 ${data.totalFailed || 0}건 · 건너뜀 ${data.totalSkipped || 0}건`
            }));
            loadSourceDocuments();
          },
          onError: (err) => {
            setIsExtracting(false);
            setExtractionError(err.message || '추출 중 오류 발생');
            loadSourceDocuments();
            setNotification({ type: 'error', message: err.message || '추출 중 오류 발생' });
          }
        }
      );
    } catch (err) {
      setIsExtracting(false);
      setExtractionError(err.message || '추출 실행 실패');
      setNotification({ type: 'error', message: err.message || '추출 실행 실패' });
    } finally {
      extractionStreamActive.current = false;
    }
  }, [loadSourceDocuments]);

  const restoreExtraction = useCallback(async (openProgress = false) => {
    if (extractionStreamActive.current) return;
    const version = extractionStreamVersion.current;
    try {
      const state = await adminRepo.getExtractionState();
      if (extractionStreamActive.current || version !== extractionStreamVersion.current) return;
      if (state.state === 'interrupted') {
        setExtractionRecovery(state);
        setExtractionError('이전 추출이 중단되었습니다. 완료된 결과를 유지하고 이어할 수 있습니다.');
        setExtractionProgress({ current: state.preservedCount, total: state.docIds.length, currentTitle: '', currentPublisher: '', step: '이전 추출 중단' });
      } else if (state.runId) {
        return startExtraction(state.docIds, false, { runId: state.runId, openProgress });
      }
    } catch (error) {
      setNotification({ type: 'warning', message: error.message || '추출 진행 상태를 확인하지 못했습니다.' });
    }
  }, [startExtraction]);

  useEffect(() => {
    if (currentUser?.level >= 4) restoreExtraction();
  }, [currentUser?.level, restoreExtraction]);

  const handleResumeExtraction = useCallback(() => {
    if (extractionRecovery?.docIds.length) {
      return startExtraction(extractionRecovery.docIds, true, { resumeInterrupted: true });
    }
  }, [extractionRecovery, startExtraction]);

  const handleRunExtraction = useCallback((docIds) => {
    if (isExtracting || extractionConfirmation || !docIds?.length) return;
    const selected = sources.filter((doc) => docIds.includes(doc.docId) && (doc.attemptStatus !== 'running' || extractionRecovery?.interruptedDocId === doc.docId));
    if (!selected.length) return;
    const pendingIds = selected.filter((doc) => !doc.lastSucceededAt).map((doc) => doc.docId);
    if (pendingIds.length < selected.length) {
      setExtractionConfirmation({ docIds: selected.map((doc) => doc.docId), pendingIds });
      return;
    }
    return startExtraction(pendingIds, false);
  }, [isExtracting, extractionConfirmation, extractionRecovery, sources, startExtraction]);

  const handleConfirmExtraction = useCallback((includeReextraction) => {
    if (isExtracting || !extractionConfirmation) return;
    const docIds = includeReextraction ? extractionConfirmation.docIds : extractionConfirmation.pendingIds;
    setExtractionConfirmation(null);
    return startExtraction(docIds, includeReextraction);
  }, [isExtracting, extractionConfirmation, startExtraction]);

  /**
   * 단건 문서 미리보기 로드
   */
  const handleOpenDocPreview = useCallback(async (docId) => {
    try {
      const res = await adminRepo.getDocumentPreview(docId);
      if (res) {
        setPreviewData({
          aggregatedConcepts: res.preview || [],
          results: [{ docId: res.docId, title: res.title, filePath: res.filePath, succeeded: res.attemptStatus === 'success' && !res.isApplied }]
        });
        setIsPreviewModalOpen(true);
      }
    } catch (err) {
      setNotification({ type: 'error', message: '미리보기 데이터를 불러오지 못했습니다.' });
    }
  }, []);

  /**
   * 관리자 검토 완료 후 위키 최종 원자적 적용 (Apply to Wiki)
   */
  const classification = prepareClassification(previewData?.aggregatedConcepts || []);
  const handleChangeClassification = useCallback((conceptId, values) => {
    setPreviewData((prev) => ({ ...prev, aggregatedConcepts: (prev?.aggregatedConcepts || []).map((item) =>
      item.conceptId === conceptId ? { ...item, ...values, classificationConfirmed: true } : item) }));
  }, []);
  const handleApplyWiki = useCallback(async () => {
    if (!previewData) return;
    const docIds = (previewData.results || []).filter((r) => r.succeeded).map((r) => r.docId).filter(Boolean);
    if (docIds.length === 0) return;
    const prepared = prepareClassification(previewData.aggregatedConcepts || []);
    if (prepared.error) {
      setNotification({ type: 'error', message: prepared.error });
      return;
    }

    setIsApplying(true);
    try {
      const res = await adminRepo.applyExtractionsToWiki({ docIds, conceptMetadata: prepared.metadata });
      onWikiApplied?.();
      setNotification({
        type: 'success',
        message: res.message || `${docIds.length}개 문서의 지식이 위키에 성공적으로 적용되었습니다.`
      });
      setIsPreviewModalOpen(false);
      setPreviewData((prev) => ({ ...prev, results: (prev.results || []).map((r) => ({ ...r, succeeded: false })) }));
      loadSourceDocuments();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '위키 적용에 실패했습니다.' });
    } finally {
      setIsApplying(false);
    }
  }, [previewData, loadSourceDocuments, onWikiApplied]);

  // 필터링된 열람 신청 목록
  const filteredRequests = accessRequests.filter((r) => {
    if (filterStatus === 'all') return true;
    return r.status === filterStatus;
  });

  return {
    activeSubTab,
    accessRequests: filteredRequests,
    totalRequestsCount: accessRequests.length,
    users,
    filterStatus,
    isLoading,
    isActionLoading,
    notification,

    // 소스 인제스천 상태 & 액션
    sources: sources.map((doc) => extractionRecovery?.interruptedDocId === doc.docId ? { ...doc, attemptStatus: 'interrupted' } : doc),
    extractionRecovery,
    handleResumeExtraction,
    sourceSummary,
    selectedDocIds,
    isSourceLoading,
    isExtracting,
    isProgressModalOpen,
    extractionConfirmation,
    extractionProgress,
    extractionLogs,
    isExtractionFinished,
    extractionError,
    previewData,
    isPreviewModalOpen,
    isApplying,

    setActiveSubTab,
    setFilterStatus,
    loadAccessRequests,
    loadUsers,
    handleApproveRequest,
    handleRejectRequest,
    handleUpdateUserLevel,
    handleToggleUserActive,
    loadSourceDocuments,
    handleToggleSelectDoc,
    handleSelectAllDocs,
    handleClearDocSelection,
    handleRunExtraction,
    handleRunReextraction: handleRunExtraction,
    handleConfirmExtraction,
    cancelExtractionConfirmation: () => setExtractionConfirmation(null),
    handleOpenDocPreview,
    openProgressModal: () => {
      setIsProgressModalOpen(true);
      if (!isExtractionFinished) restoreExtraction(true);
    },
    handleOpenProgressPreview: () => {
      setIsProgressModalOpen(false);
      setIsPreviewModalOpen(true);
    },
    closeProgressModal: () => setIsProgressModalOpen(false),
    closePreviewModal: () => {
      setIsPreviewModalOpen(false);
    },
    handleApplyWiki,
    handleChangeClassification,
    classificationError: classification.error,
    clearNotification: () => setNotification(null)
  };
}
