/**
 * [계층 2] Wiki Controller Hook
 * Tab 1 위키 브라우저 화면의 모든 반응형 상태와 사용자 액션을 캡슐화
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { conceptRepo } from '../repositories/conceptRepo';
import { authRepo } from '../repositories/authRepo';
import { reviewRepo } from '../repositories/reviewRepo';
import { authService } from '../services/authService';

export function useWikiController({ initialConceptId = 'concept-tcb', currentUser, myAccessRequests = [], onRefreshAuth } = {}) {
  const [activeFacet, setActiveFacet] = useState('unit_process');
  const [activeConceptId, setActiveConceptId] = useState(initialConceptId);

  // 데이터 상태
  const [treeData, setTreeData] = useState(null);
  const [conceptDetail, setConceptDetail] = useState(null);
  const [subgraphData, setSubgraphData] = useState(null);
  const [subgraphDepth, setSubgraphDepth] = useState(2);
  const [subgraphDirection, setSubgraphDirection] = useState('both');
  const [explainerCard, setExplainerCard] = useState(null);

  // 로딩 & 에러
  const [isTreeLoading, setIsTreeLoading] = useState(false);
  const [isConceptLoading, setIsConceptLoading] = useState(false);
  const [isSubgraphLoading, setIsSubgraphLoading] = useState(false);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);

  // 모달 제어 상태
  const [isAccessModalOpen, setIsAccessModalOpen] = useState(false);
  const [isRevisionModalOpen, setIsRevisionModalOpen] = useState(false);
  const [isNewConceptModalOpen, setIsNewConceptModalOpen] = useState(false);
  const [isRecommendingPlacement, setIsRecommendingPlacement] = useState(false);
  const [placementRecommendation, setPlacementRecommendation] = useState(null);

  /**
   * 온톨로지 네비게이션 트리 로드
   */
  const loadTree = useCallback(async (facet, expandedId = null) => {
    setIsTreeLoading(true);
    try {
      const res = await conceptRepo.getTree(facet, expandedId);
      setTreeData(res);
    } catch (err) {
      console.error('Failed to load concept tree:', err);
    } finally {
      setIsTreeLoading(false);
    }
  }, []);

  /**
   * 인과 서브그래프 로드
   */
  const loadSubgraph = useCallback(async (conceptId, depth = 2, direction = 'both') => {
    setIsSubgraphLoading(true);
    try {
      const res = await conceptRepo.getSubgraph(conceptId, depth, direction);
      setSubgraphData(res);
    } catch (err) {
      console.error('Failed to load causal subgraph:', err);
    } finally {
      setIsSubgraphLoading(false);
    }
  }, []);

  /**
   * 특정 개념 상세 로드
   */
  const loadConcept = useCallback(async (conceptId) => {
    setIsConceptLoading(true);
    setError(null);
    try {
      const detail = await conceptRepo.getConceptDetail(conceptId);
      setConceptDetail(detail);
      setActiveConceptId(conceptId);
      // 서브그래프 동시 적재
      loadSubgraph(conceptId, subgraphDepth, subgraphDirection);
    } catch (err) {
      setError(err.message || '개념 상세 정보를 불러올 수 없습니다.');
    } finally {
      setIsConceptLoading(false);
    }
  }, [loadSubgraph, subgraphDepth, subgraphDirection]);

  // 패싯 변경 액션
  const changeFacet = useCallback((facet) => {
    setActiveFacet(facet);
    loadTree(facet);
  }, [loadTree]);

  // 개념 선택 액션
  const selectConcept = useCallback((conceptId) => {
    loadConcept(conceptId);
  }, [loadConcept]);

  // 서브그래프 홉/방향 변경
  const changeSubgraphDepth = useCallback((depth) => {
    setSubgraphDepth(depth);
    if (activeConceptId) {
      loadSubgraph(activeConceptId, depth, subgraphDirection);
    }
  }, [activeConceptId, loadSubgraph, subgraphDirection]);

  const changeSubgraphDirection = useCallback((dir) => {
    setSubgraphDirection(dir);
    if (activeConceptId) {
      loadSubgraph(activeConceptId, subgraphDepth, dir);
    }
  }, [activeConceptId, loadSubgraph, subgraphDepth]);

  // 0ms 인라인 문맥 해설 조회
  const openExplainer = useCallback((termId) => {
    if (!conceptDetail) return;

    // 1. 사전 적재(Preloaded Explainers)에서 0ms 탐색
    if (conceptDetail.preloadedExplainers && conceptDetail.preloadedExplainers[termId]) {
      setExplainerCard(conceptDetail.preloadedExplainers[termId]);
      return;
    }

    // 2. 캐시 미스 시 실시간 API 호출
    conceptRepo.getContextualExplainer(conceptDetail.id, termId)
      .then((data) => setExplainerCard(data))
      .catch(() => {
        setExplainerCard({
          childConceptId: termId,
          parentConceptId: conceptDetail.id,
          title: termId,
          definition: '온톨로지 인과 지식 그래프에 등록된 공학적 연관 개념입니다.',
          contextSentence: `${conceptDetail.title}와의 인과 메커니즘을 공유합니다.`,
          cached: false,
          deepLink: `/wiki?concept=${termId}`
        });
      });
  }, [conceptDetail]);

  const closeExplainer = useCallback(() => {
    setExplainerCard(null);
  }, []);

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
    setIsRecommendingPlacement(true);
    try {
      const rec = await conceptRepo.recommendPlacement({ title, summary });
      setPlacementRecommendation(rec);
    } catch (err) {
      console.error('Failed to get recommendation:', err);
    } finally {
      setIsRecommendingPlacement(false);
    }
  }, []);

  // 완전 신규 문서/개념 추가 발의 티켓 등록
  const submitNewConceptTicket = useCallback(async (newConceptPayload) => {
    try {
      await reviewRepo.createTicket({
        ...newConceptPayload,
        isNewConcept: true
      });
      setIsNewConceptModalOpen(false);
      setPlacementRecommendation(null);
      setNotification({ type: 'success', message: '신규 개념 편입 발의 티켓이 Tab 3 검토 대기열에 등록되었습니다.' });
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '신규 개념 발의에 실패했습니다.' });
    }
  }, []);

  // 마운트 시 초기 트리 및 개념 로드
  useEffect(() => {
    loadTree(activeFacet, initialConceptId);
    loadConcept(initialConceptId);
  }, []);

  return {
    activeFacet,
    activeConceptId,
    treeData,
    conceptDetail,
    subgraphData,
    subgraphDepth,
    subgraphDirection,
    explainerCard,
    isTreeLoading,
    isConceptLoading,
    isSubgraphLoading,
    error,
    notification,
    l3AccessStatus,
    isAccessModalOpen,
    isRevisionModalOpen,
    isNewConceptModalOpen,
    isRecommendingPlacement,
    placementRecommendation,
    changeFacet,
    selectConcept,
    changeSubgraphDepth,
    changeSubgraphDirection,
    openExplainer,
    closeExplainer,
    openAccessModal: () => setIsAccessModalOpen(true),
    closeAccessModal: () => setIsAccessModalOpen(false),
    openRevisionModal: () => setIsRevisionModalOpen(true),
    closeRevisionModal: () => setIsRevisionModalOpen(false),
    openNewConceptModal: () => setIsNewConceptModalOpen(true),
    closeNewConceptModal: () => {
      setIsNewConceptModalOpen(false);
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
