/**
 * [계층 2] ResearchController Hook
 * Tab 4 외부 문헌·백서 조사실의 반응형 상태 및 3단계 파이프라인 제어기
 * (1단계: 주제 검색/필터 ➔ 2단계: 공인 문헌 피드 ➔ 3단계: 종합 리포트 및 지식 후보 발행)
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { researchRepo } from '../repositories/researchRepo';
import { usableEvidenceIds } from '../services/researchService';

const DEFAULT_INSTITUTIONS = [];

export function useResearchController({ currentUser, initialQuery = '', onNavigateToTab } = {}) {
  // 화면 단계: 'search' | 'feed' | 'report'
  const [activeStep, setActiveStep] = useState('search');

  // 검색 주제 및 필터
  const [searchTopic, setSearchTopic] = useState(initialQuery || '');
  const [targetInstitutions, setTargetInstitutions] = useState(DEFAULT_INSTITUTIONS);

  // 세션 목록 및 현재 세션
  const [pastSessions, setPastSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [comparisonContext, setComparisonContext] = useState(null);
  const [discoveryNotice, setDiscoveryNotice] = useState('');
  const discoveryRequest = useRef(0);

  // 문헌 피드 & 종합 리포트 결과
  const [evidenceFeed, setEvidenceFeed] = useState([]);
  const [selectedEvidenceIds, setSelectedEvidenceIds] = useState([]);
  const [synthesisReport, setSynthesisReport] = useState(null);
  const [candidates, setCandidates] = useState([]);

  // 로딩 상태
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  // 모달 및 피드백 상태
  const [isExportCandidateModalOpen, setIsExportCandidateModalOpen] = useState(false);
  const [candidateToExport, setCandidateToExport] = useState(null);
  const [notification, setNotification] = useState(null);

  /**
   * 과거 조사 세션 목록 로드
   */
  const loadSessions = useCallback(async () => {
    setIsLoadingSessions(true);
    try {
      const res = await researchRepo.listSessions({ limit: 15 });
      setPastSessions(res.sessions || []);
    } catch (err) {
      console.warn('Failed to load past research sessions:', err);
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // initialQuery 변경 시 자동 검색어 반영
  useEffect(() => {
    if (initialQuery && initialQuery.trim()) {
      setSearchTopic(initialQuery.trim());
    }
  }, [initialQuery]);

  /**
   * 과거 조사 세션 클릭 ➔ 상세 리포트 및 지식 후보 복원
   */
  const selectPastSession = useCallback(async (sessionId) => {
    const requestId = ++discoveryRequest.current;
    setIsDiscovering(false);
    setIsSynthesizing(true);
    try {
      const res = await researchRepo.getSession(sessionId);
      if (requestId !== discoveryRequest.current) return;
      setCurrentSessionId(res.sessionId);
      setSearchTopic(res.searchTopic || '');
      setEvidenceFeed(res.evidenceFeed || []);
      setSelectedEvidenceIds(usableEvidenceIds(res.evidenceFeed || [], (res.evidenceFeed || []).map((e) => e.id)));
      setComparisonContext(res.comparisonContext || null);
      setDiscoveryNotice(res.notice || '');
      setSynthesisReport(res.synthesisReport || null);
      setCandidates(res.candidates || []);
      setActiveStep(res.synthesisReport ? 'report' : 'feed');
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '세션 정보를 불러오지 못했습니다.' });
    } finally {
      if (requestId === discoveryRequest.current) setIsSynthesizing(false);
    }
  }, []);

  /**
   * 1단계 ➔ 2단계: 실측 문헌 피드 발굴 실행
   */
  const handleDiscover = useCallback(async (overrideTopic, context = comparisonContext) => {
    const topic = (overrideTopic || searchTopic).trim();
    if (topic.length < 2) {
      setNotification({ type: 'warning', message: '조사할 기술 주제를 2자 이상 입력해주세요.' });
      return;
    }

    const requestId = ++discoveryRequest.current;
    setIsDiscovering(true);
    setIsSynthesizing(false);
    setSearchTopic(topic);
    setComparisonContext(context);
    setSynthesisReport(null);
    setCandidates([]);
    setCurrentSessionId(null);
    setEvidenceFeed([]);
    setSelectedEvidenceIds([]);
    setActiveStep('search');
    try {
      const res = await researchRepo.discoverEvidences({
        searchTopic: topic,
        targetInstitutions,
        comparisonContext: context
      });
      if (requestId !== discoveryRequest.current) return;

      setCurrentSessionId(res.sessionId);
      setEvidenceFeed(res.evidenceFeed || []);
      setSelectedEvidenceIds(usableEvidenceIds(res.evidenceFeed || [], (res.evidenceFeed || []).map((e) => e.id)));
      setComparisonContext(res.comparisonContext || null);
      setDiscoveryNotice(res.notice || '');
      setActiveStep('feed');
      // 세션 목록 갱신
      loadSessions();
    } catch (err) {
      if (requestId === discoveryRequest.current) setNotification({ type: 'error', message: err.message || '문헌 발굴 요청에 실패했습니다.' });
    } finally {
      if (requestId === discoveryRequest.current) setIsDiscovering(false);
    }
  }, [searchTopic, targetInstitutions, loadSessions, comparisonContext]);

  /**
   * 문헌 선택 토글
   */
  const toggleEvidenceSelection = useCallback((id) => {
    setSelectedEvidenceIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  }, []);

  const selectAllEvidences = useCallback(() => {
    if (selectedEvidenceIds.length === evidenceFeed.length) {
      setSelectedEvidenceIds([]);
    } else {
      setSelectedEvidenceIds(evidenceFeed.map((e) => e.id));
    }
  }, [evidenceFeed, selectedEvidenceIds]);

  /**
   * 2단계 ➔ 3단계: 선택된 문헌 종합 분석 리포트 생성
   */
  const handleSynthesizeReport = useCallback(async () => {
    if (!currentSessionId) return;
    if (usableEvidenceIds(evidenceFeed, selectedEvidenceIds).length === 0) {
      setNotification({ type: 'warning', message: '종합 분석을 생성할 공인 문헌을 1건 이상 선택해주세요.' });
      return;
    }

    setIsSynthesizing(true);
    try {
      const res = await researchRepo.synthesizeReport(currentSessionId, {
        selectedEvidenceIds: usableEvidenceIds(evidenceFeed, selectedEvidenceIds)
      });

      setSynthesisReport(res.synthesisReport || null);
      setCandidates(res.candidates || []);
      setActiveStep('report');
      loadSessions();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '종합 분석 리포트 생성에 실패했습니다.' });
    } finally {
      setIsSynthesizing(false);
    }
  }, [currentSessionId, selectedEvidenceIds, evidenceFeed, loadSessions]);

  /**
   * 기관 필터 토글
   */
  const toggleInstitution = useCallback((inst) => {
    setTargetInstitutions((prev) =>
      prev.includes(inst) ? prev.filter((i) => i !== inst) : [...prev, inst]
    );
  }, []);

  /**
   * 지식 후보 티켓 내보내기 모달 열기
   */
  const openExportCandidateModal = useCallback((candidate) => {
    // Level 2 이상 권한 가드레일 (게스트 차단 알림)
    if (!currentUser || currentUser.level < 2) {
      setNotification({
        type: 'warning',
        message: '발굴 문헌 지식 티켓 발의 권한은 "현장 엔지니어(Level 2)" 이상만 가능합니다.'
      });
      return;
    }
    setCandidateToExport(candidate);
    setIsExportCandidateModalOpen(true);
  }, [currentUser]);

  const closeExportCandidateModal = useCallback(() => {
    setIsExportCandidateModalOpen(false);
    setCandidateToExport(null);
  }, []);

  /**
   * 지식 후보 ➔ 검토 센터(Tab 3) 티켓 발행 실행
   */
  const handleExportCandidateTicket = useCallback(async ({ userNote }) => {
    if (!candidateToExport || !currentSessionId) return;

    setIsExporting(true);
    try {
      const res = await researchRepo.exportCandidateTicket(candidateToExport.candidateId, {
        sessionId: currentSessionId,
        userNote: userNote || '',
        author: currentUser?.name || '현장 엔지니어',
        department: currentUser?.department || '패키징선행개발팀'
      });

      setIsExportCandidateModalOpen(false);
      setCandidateToExport(null);
      setNotification({
        type: 'success',
        message: `지식 후보가 검토 센터 티켓(${res.ticketId})으로 성공적으로 등록되었습니다.`
      });

      // Tab 3 검토 센터로 자동 이동
      if (onNavigateToTab) {
        setTimeout(() => onNavigateToTab('review', { ticketId: res.ticketId }), 1200);
      }
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '티켓 발행에 실패했습니다.' });
    } finally {
      setIsExporting(false);
    }
  }, [candidateToExport, currentSessionId, currentUser, onNavigateToTab]);

  /**
   * 새 문헌 조사 시작 (검색 단계로 리셋)
   */
  const handleResetSearch = useCallback(() => {
    discoveryRequest.current += 1;
    setIsDiscovering(false);
    setIsSynthesizing(false);
    setActiveStep('search');
    setSearchTopic('');
    setEvidenceFeed([]);
    setSelectedEvidenceIds([]);
    setSynthesisReport(null);
    setCandidates([]);
    setCurrentSessionId(null);
    setComparisonContext(null);
    setDiscoveryNotice('');
  }, []);

  const usableSelectedIds = usableEvidenceIds(evidenceFeed, selectedEvidenceIds);
  const handleReturnToComparison = useCallback((useEvidence = false) => {
    if (!comparisonContext?.comparisonSessionId) return;
    onNavigateToTab?.('comparison', {
      comparisonSessionId: comparisonContext.comparisonSessionId,
      researchSessionId: useEvidence ? currentSessionId : undefined,
      selectedEvidenceIds: useEvidence ? usableEvidenceIds(evidenceFeed, selectedEvidenceIds) : []
    });
  }, [comparisonContext, currentSessionId, evidenceFeed, selectedEvidenceIds, onNavigateToTab]);

  return {
    activeStep,
    searchTopic,
    targetInstitutions,
    pastSessions,
    currentSessionId,
    comparisonContext,
    discoveryNotice,
    usableSelectedIds,
    handleReturnToComparison,
    evidenceFeed,
    selectedEvidenceIds,
    synthesisReport,
    candidates,
    isLoadingSessions,
    isDiscovering,
    isSynthesizing,
    isExporting,
    isExportCandidateModalOpen,
    candidateToExport,
    notification,

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
    clearNotification: () => setNotification(null)
  };
}
