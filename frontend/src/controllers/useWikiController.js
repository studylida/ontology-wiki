/**
 * [계층 2] Wiki Controller Hook
 * Tab 1 위키 브라우저 화면의 모든 반응형 상태와 사용자 액션을 캡슐화
 */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { conceptRepo } from '../repositories/conceptRepo';
import { authRepo } from '../repositories/authRepo';
import { reviewRepo } from '../repositories/reviewRepo';
import { authService } from '../services/authService';
import { createSelectionMatcher } from '../services/textSelectionService';

export function useWikiController({ initialConceptId = null, currentUser, myAccessRequests = [], onRefreshAuth } = {}) {
  const [navMode, setNavMode] = useState('domain'); // 'domain' | 'scale'
  const [activeFacet, setActiveFacet] = useState('unit_process');
  const [activeScale, setActiveScale] = useState(3);
  const [activeConceptId, setActiveConceptId] = useState(initialConceptId);
  const requestedConceptId = useRef(initialConceptId);

  // 데이터 상태
  const [treeData, setTreeData] = useState(null);
  const [conceptDetail, setConceptDetail] = useState(null);
  const [explainerPopover, setExplainerPopover] = useState({ isOpen: false, position: null, data: null });
  const explainerRequest = useRef(null);
  const findSelectionRange = useMemo(() => createSelectionMatcher(conceptDetail?.selectionTerms || []), [conceptDetail?.selectionTerms]);

  // 로딩 & 에러
  const [isTreeLoading, setIsTreeLoading] = useState(false);
  const [isConceptLoading, setIsConceptLoading] = useState(false);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);

  // 모달 제어 상태
  const [isAccessModalOpen, setIsAccessModalOpen] = useState(false);
  const [isRevisionModalOpen, setIsRevisionModalOpen] = useState(false);
  const [isNewConceptModalOpen, setIsNewConceptModalOpen] = useState(false);
  const [newConceptInitialData, setNewConceptInitialData] = useState(null);
  const [isRecommendingPlacement, setIsRecommendingPlacement] = useState(false);
  const [placementRecommendation, setPlacementRecommendation] = useState(null);
  const [placementRecommendationError, setPlacementRecommendationError] = useState(null);
  const placementRequest = useRef(0);
  const [caseExplanationRequests, setCaseExplanationRequests] = useState({});
  const conceptRequest = useRef(0);
  const detailRef = useRef(null);
  const selectedConceptRef = useRef(initialConceptId);
  const explanationRequests = useRef(new Set());

  /**
   * 온톨로지 네비게이션 트리 로드 (실무분야 또는 물리규모 필터 지원)
   */
  const loadTree = useCallback(async (optionsOrFacet = 'unit_process', expandedId = null) => {
    setIsTreeLoading(true);
    try {
      const res = await conceptRepo.getTree(optionsOrFacet, expandedId);
      setTreeData(res);
      return res;
    } catch (err) {
      console.error('Failed to load concept tree:', err);
    } finally {
      setIsTreeLoading(false);
    }
  }, []);

  /**
   * 특정 개념 상세 로드
   */
  const loadConcept = useCallback(async (conceptId) => {
    if (!conceptId) return;
    requestedConceptId.current = conceptId;
    const request = ++conceptRequest.current;
    selectedConceptRef.current = conceptId;
    setCaseExplanationRequests({});
    explainerRequest.current = null;
    setExplainerPopover({ isOpen: false, position: null, data: null });
    setIsConceptLoading(true);
    setError(null);
    try {
      const detail = await conceptRepo.getConceptDetail(conceptId);
      if (request !== conceptRequest.current) return;
      detailRef.current = detail;
      setConceptDetail(detail);
      setActiveConceptId(conceptId);
    } catch (err) {
      if (request === conceptRequest.current) setError(err.message || '개념 상세 정보를 불러올 수 없습니다.');
    } finally {
      if (request === conceptRequest.current) setIsConceptLoading(false);
    }
  }, []);

  const generateCaseContextExplanation = useCallback(async (caseId) => {
    const detail = detailRef.current;
    const target = detail?.perspectives?.find(item => item.id === caseId);
    if (!target || !(currentUser?.level >= 3) || selectedConceptRef.current !== detail.id) return;
    const request = conceptRequest.current;
    const key = `${request}:${caseId}`;
    if (explanationRequests.current.has(key)) return;
    const basisHash = target.contextExplanationBasisHash;
    const isCurrent = () => request === conceptRequest.current && selectedConceptRef.current === detail.id &&
      detailRef.current?.perspectives?.some(item => item.id === caseId && item.contextExplanationBasisHash === basisHash);
    explanationRequests.current.add(key);
    setCaseExplanationRequests(state => ({...state, [caseId]: {loading: true}}));
    try {
      await conceptRepo.generateCaseContextExplanation(detail.id, caseId);
      if (!isCurrent()) return;
      const updated = await conceptRepo.getConceptDetail(detail.id);
      if (!isCurrent()) return;
      detailRef.current = updated;
      setConceptDetail(updated);
      setCaseExplanationRequests(state => ({...state, [caseId]: {loading: false}}));
    } catch (err) {
      if (!isCurrent()) return;
      setCaseExplanationRequests(state => ({...state, [caseId]: {
        loading: false,
        error: err.status === 409 ? '사례 내용이 변경되었습니다. 최신 내용을 다시 불러온 뒤 시도해 주세요.' : '쉬운 해설을 준비하지 못했습니다. 잠시 후 다시 시도해 주세요.'
      }}));
    } finally {
      explanationRequests.current.delete(key);
    }
  }, [currentUser?.level]);

  const generatingCases = (conceptDetail?.perspectives || [])
    .filter(item => item.contextExplanationState === 'generating')
    .map(item => `${item.id}:${item.contextExplanationBasisHash || ''}`).join('|');
  useEffect(() => {
    if (!generatingCases || isConceptLoading) return;
    const request = conceptRequest.current;
    const conceptId = conceptDetail.id;
    let cancelled = false;
    let timer;
    let attempts = 0;
    const poll = async () => {
      try {
        const updated = await conceptRepo.getConceptDetail(conceptId);
        if (cancelled || request !== conceptRequest.current || selectedConceptRef.current !== conceptId) return;
        const currentGenerating = (detailRef.current?.perspectives || [])
          .filter(item => item.contextExplanationState === 'generating')
          .map(item => `${item.id}:${item.contextExplanationBasisHash || ''}`).join('|');
        if (currentGenerating !== generatingCases) return;
        detailRef.current = updated;
        setConceptDetail(updated);
        // shortcut: 단일 페이지에서 1분까지만 재확인하며, 장시간 작업 알림이 필요할 때 확장한다.
        if (updated.perspectives?.some(item => item.contextExplanationState === 'generating') && ++attempts < 20) {
          timer = setTimeout(poll, 3000);
        }
      } catch {
        // 원문 화면은 유지하고 다음 페이지 조회나 수동 재시도로 복구한다.
      }
    };
    timer = setTimeout(poll, 3000);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [generatingCases, conceptDetail?.id, isConceptLoading]);

  useEffect(() => () => { conceptRequest.current += 1; }, []);

  // 패싯(실무분야) 변경 액션
  const changeFacet = useCallback((facet) => {
    setActiveFacet(facet);
    setNavMode('domain');
    loadTree({ facet });
  }, [loadTree]);

  // 물리적 규모(Scale 1~5) 변경 액션
  const changeScale = useCallback((scale) => {
    setActiveScale(scale);
    setNavMode('scale');
    loadTree({ scale });
  }, [loadTree]);

  // 관점 모드(실무분야 vs 물리규모) 토글 액션
  const changeNavMode = useCallback((mode) => {
    setNavMode(mode);
    if (mode === 'scale') {
      loadTree({ scale: activeScale });
    } else {
      loadTree({ facet: activeFacet });
    }
  }, [activeScale, activeFacet, loadTree]);

  // 개념 선택 액션
  const selectConcept = useCallback((conceptId) => {
    loadConcept(conceptId);
  }, [loadConcept]);

  const closeExplainer = useCallback(() => {
    explainerRequest.current = null;
    setExplainerPopover({ isOpen: false, position: null, data: null });
  }, []);

  const openExplainer = useCallback((text, position, continuation = false, context = '') => {
    if (!conceptDetail) return;
    const previous = explainerRequest.current;
    if (continuation && previous?.parentId === conceptDetail.id && previous.text === text && previous.context === context) {
      setExplainerPopover((current) => ({ ...current, position }));
      return;
    }
    const request = { parentId: conceptDetail.id, text, context };
    explainerRequest.current = request;
    const pre = !context && conceptDetail.preloadedExplainers?.[text.toLowerCase()];
    setExplainerPopover({ isOpen: true, position, data: {
      title: pre?.title || text, term: text,
      definition: pre?.definition,
      contextSentence: pre?.contextSentence,
      conceptId: pre?.childConceptId || pre?.targetConceptId || null, isLoading: !pre
    } });
    if (pre) return;
    conceptRepo.getContextualExplainer(conceptDetail.id, text, 'default', context)
      .then((res) => {
        if (explainerRequest.current !== request) return;
        setExplainerPopover({ isOpen: true, position, data: {
          title: res.title || text, term: text, definition: res.definition,
          contextSentence: res.contextSentence, conceptId: res.childConceptId || null, isLoading: false
        } });
      })
      .catch((error) => {
        if (explainerRequest.current !== request) return;
        const message = {
          0: '서버에 연결하지 못했습니다. 연결 상태를 확인해 주세요.',
          401: '로그인이 만료되었습니다. 다시 로그인해 주세요.',
          403: '비공개 내용은 문맥 해설에 사용할 수 없습니다.',
          404: '설명할 위키를 찾을 수 없습니다. 문서를 다시 열어 주세요.',
          405: '문맥 해설 API를 사용할 수 없습니다. 서버 버전을 확인해 주세요.',
          422: '선택 내용 또는 문맥을 처리할 수 없습니다. 범위를 다시 선택해 주세요.',
          503: '문맥 해설을 생성하지 못했습니다. 잠시 후 다시 선택해 주세요.'
        }[error.status] || '문맥 해설 요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.';
        setExplainerPopover({ isOpen: true, position, data: {
          title: text, term: text, error: message,
          conceptId: null, isLoading: false
        } });
      });
  }, [conceptDetail]);

  useEffect(() => () => { explainerRequest.current = null; }, []);

  // L3 극비 파라미터 4단계 열람 인가 판정
  const l3AccessStatus = useMemo(() => {
    return authService.checkL3Access(currentUser, myAccessRequests, activeConceptId);
  }, [currentUser, myAccessRequests, activeConceptId]);

  // L3 열람 신청 제출 액션
  const submitAccessRequest = useCallback(async (reason) => {
    if (!activeConceptId) return;
    try {
      await authRepo.createAccessRequest({ conceptId: activeConceptId, reason });
      setIsAccessModalOpen(false);
      setNotification({ type: 'success', message: 'L3 대외비 열람 권한 신청이 접수되었습니다. (심사 대기)' });
      if (onRefreshAuth) onRefreshAuth();
      loadConcept(activeConceptId);
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '열람 신청 접수에 실패했습니다.' });
    }
  }, [activeConceptId, onRefreshAuth, loadConcept]);

  // L3 열람 신청 취소 액션
  const cancelAccessRequest = useCallback(async (requestId) => {
    try {
      await authRepo.cancelAccessRequest(requestId);
      setNotification({ type: 'info', message: '열람 권한 신청이 취소되었습니다.' });
      if (onRefreshAuth) onRefreshAuth();
      if (activeConceptId) loadConcept(activeConceptId);
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '신청 취소에 실패했습니다.' });
    }
  }, [activeConceptId, onRefreshAuth, loadConcept]);

  // 기존 문서 개정 발의 티켓 등록
  const submitRevisionTicket = useCallback(async (ticketData) => {
    try {
      await reviewRepo.createTicket({
        ...ticketData,
        conceptId: activeConceptId,
        isNewConcept: false
      });
      setIsRevisionModalOpen(false);
      setNotification({ type: 'success', message: '개정안 발의 티켓이 Tab 3 검토 센터 대기열에 등록되었습니다.' });
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '개정안 발의에 실패했습니다.' });
    }
  }, [activeConceptId]);

  // AI 에이전트 온톨로지 편입 위치 추천 요청
  const requestPlacementRecommendation = useCallback(async (title, summary) => {
    const request = ++placementRequest.current;
    setIsRecommendingPlacement(true);
    setPlacementRecommendation(null);
    setPlacementRecommendationError(null);
    try {
      const rec = await conceptRepo.recommendPlacement({ title, summary });
      if (request === placementRequest.current) setPlacementRecommendation(rec);
    } catch (err) {
      if (request === placementRequest.current) setPlacementRecommendationError(err.message || '위치 추천에 실패했습니다. 세 분류 항목을 직접 입력해 주세요.');
    } finally {
      if (request === placementRequest.current) setIsRecommendingPlacement(false);
    }
  }, []);

  // 완전 신규 문서/개념 추가 발의 티켓 등록
  const submitNewConceptTicket = useCallback(async (newConceptPayload) => {
    try {
      await reviewRepo.createTicket({
        ...newConceptPayload,
        isNewConcept: true
      });
      placementRequest.current += 1;
      setIsRecommendingPlacement(false);
      setPlacementRecommendationError(null);
      setIsNewConceptModalOpen(false);
      setPlacementRecommendation(null);
      setNotification({ type: 'success', message: '신규 개념 편입 발의 티켓이 Tab 3 검토 대기열에 등록되었습니다.' });
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '신규 개념 발의에 실패했습니다.' });
    }
  }, []);

  // 마운트 시 초기 트리 및 개념 로드
  useEffect(() => {
    loadTree({ facet: activeFacet }, initialConceptId).then((tree) => {
      if (requestedConceptId.current) return;
      const nodes = [...(tree?.tree || [])];
      while (nodes.length) {
        const node = nodes.shift();
        if (node.type === 'concept') { loadConcept(node.id); break; }
        nodes.unshift(...(node.children || []));
      }
    });
    if (initialConceptId) loadConcept(initialConceptId);
  }, []);

  // 🌟 사용자 로그인/인가 변경 시(Level 4 관리자 전환 등) 활성 문서 자동 재조회
  useEffect(() => {
    if (activeConceptId) {
      loadConcept(activeConceptId);
    }
  }, [currentUser?.id, currentUser?.level]);

  return {
    navMode,
    activeScale,
    activeFacet,
    activeConceptId,
    treeData,
    conceptDetail,
    explainerPopover,
    findSelectionRange,
    caseExplanationRequests,
    generateCaseContextExplanation,
    isTreeLoading,
    isConceptLoading,
    error,
    notification,
    l3AccessStatus,
    isAccessModalOpen,
    isRevisionModalOpen,
    isNewConceptModalOpen,
    newConceptInitialData,
    isRecommendingPlacement,
    placementRecommendation,
    placementRecommendationError,
    changeFacet,
    changeScale,
    changeNavMode,
    selectConcept,
    refreshWiki: () => {
      loadTree(navMode === 'scale' ? { scale: activeScale } : { facet: activeFacet }, activeConceptId);
      if (activeConceptId) loadConcept(activeConceptId);
    },
    openExplainer,
    closeExplainer,
    openAccessModal: () => setIsAccessModalOpen(true),
    closeAccessModal: () => setIsAccessModalOpen(false),
    openRevisionModal: () => setIsRevisionModalOpen(true),
    closeRevisionModal: () => setIsRevisionModalOpen(false),
    openNewConceptModal: (initialData = null) => {
      placementRequest.current += 1;
      setIsRecommendingPlacement(false);
      setPlacementRecommendation(null);
      setPlacementRecommendationError(null);
      setNewConceptInitialData(initialData);
      setIsNewConceptModalOpen(true);
    },
    closeNewConceptModal: () => {
      placementRequest.current += 1;
      setIsRecommendingPlacement(false);
      setPlacementRecommendationError(null);
      setIsNewConceptModalOpen(false);
      setNewConceptInitialData(null);
      setPlacementRecommendation(null);
    },
    submitAccessRequest,
    cancelAccessRequest,
    submitRevisionTicket,
    requestPlacementRecommendation,
    submitNewConceptTicket,
    clearNotification: () => setNotification(null)
  };
}
