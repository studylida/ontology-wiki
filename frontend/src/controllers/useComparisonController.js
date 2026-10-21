/**
 * [계층 2] ComparisonController Hook
 * Tab 2 기술 대안 인과 탐구실의 반응형 상태 및 2-Track 듀얼 흐름 제어기
 */

import { useState, useCallback, useMemo } from 'react';
import { comparisonRepo } from '../repositories/comparisonRepo';
import { physicalSafetyGuardService } from '../services/physicalSafetyGuardService';

export function useComparisonController({ currentUser, onNavigateToTab } = {}) {
  // 화면 단계: 'setup' (화면 2-A: 조건 설정) | 'matrix' (화면 2-B: 매트릭스 결과 리포트)
  const [activeStep, setActiveStep] = useState('setup');
  const [trackMode, setTrackMode] = useState('track1'); // 'track1' | 'track2'

  // Track 1: 자연어 질의 구체화 상태
  const [query, setQuery] = useState('');
  const [isClarifying, setIsClarifying] = useState(false);
  const [clarifyResult, setClarifyResult] = useState(null);

  // Track 2: 대상 A/B 직접 지정 상태
  const [targetA, setTargetA] = useState('concept-mrmuf');
  const [targetB, setTargetB] = useState('concept-tcb');
  const [domain, setDomain] = useState('hbm3e_advanced');

  // Matrix & 세션 상태
  const [currentSession, setCurrentSession] = useState(null);
  const [matrixRows, setMatrixRows] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [activeGapPopover, setActiveGapPopover] = useState(null);
  const [isMatrixLoading, setIsMatrixLoading] = useState(false);

  // 꼬리질문 튜닝 상담 이력
  const [chatHistory, setChatHistory] = useState([]);
  const [isAdvising, setIsAdvising] = useState(false);

  // 모달 및 피드백 상태
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [exportedTicketId, setExportedTicketId] = useState(null);
  const [notification, setNotification] = useState(null);

  /**
   * Track 1: 질문 구체화 API 호출 ➔ 3대 공학 분기 카드 생성
   */
  const handleClarifyQuery = useCallback(async (queryText) => {
    const targetQuery = queryText || query;
    if (!targetQuery.trim()) return;

    setIsClarifying(true);
    setQuery(targetQuery);
    try {
      const res = await comparisonRepo.clarify({ query: targetQuery.trim() });
      setClarifyResult(res);
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '질문 구체화에 실패했습니다.' });
    } finally {
      setIsClarifying(false);
    }
  }, [query]);

  /**
   * 비교 분석 공통 실행 루틴
   */
  const executeComparison = useCallback(async (tA, tB, sessionTitle, dom = 'hbm3e_advanced') => {
    setIsMatrixLoading(true);
    try {
      const userId = currentUser?.username || 'anonymous_engineer';
      // 1. 비교 세션 생성
      const session = await comparisonRepo.createSession({
        title: sessionTitle,
        userId,
        query: `${tA} vs ${tB}`,
        contextParams: {
          targetA: tA,
          targetB: tB,
          domain: dom
        }
      });
      setCurrentSession(session);

      // 2. 다차원 축 비교 매트릭스 계산
      const matrixRes = await comparisonRepo.updateMatrix(session.id, {});
      setMatrixRows(matrixRes.matrix || []);

      // 3. 화면 2-B로 전환
      setActiveStep('matrix');
      setChatHistory([]);
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '비교 분석 매트릭스를 생성하지 못했습니다.' });
    } finally {
      setIsMatrixLoading(false);
    }
  }, [currentUser]);

  /**
   * Track 1 분기 카드 선택 시 바로 비교 실행
   */
  const handleSelectBranch = useCallback((branch) => {
    setTargetA(branch.targetA);
    setTargetB(branch.targetB);
    setDomain(branch.domain || 'hbm3e_advanced');
    executeComparison(branch.targetA, branch.targetB, branch.title, branch.domain || 'hbm3e_advanced');
  }, [executeComparison]);

  /**
   * Track 2 직접 비교 시작 버튼 클릭
   */
  const handleStartDirectComparison = useCallback(() => {
    executeComparison(targetA, targetB, `${targetA} vs ${targetB} 직접 비교`, domain);
  }, [targetA, targetB, domain, executeComparison]);

  /**
   * 조건 수정 클릭 ➔ 화면 2-A로 복귀
   */
  const handleResetToSetup = useCallback(() => {
    setActiveStep('setup');
    setActiveGapPopover(null);
  }, []);

  /**
   * 온디맨드 지식 갭 팝오버 열기/닫기
   */
  const handleOpenGapPopover = useCallback((row, targetSide) => {
    setActiveGapPopover({ row, targetSide });
  }, []);

  const handleCloseGapPopover = useCallback(() => {
    setActiveGapPopover(null);
  }, []);

  /**
   * 지식 갭에서 Tab 4 외부 문헌 조사실로 연계 이동
   */
  const handleNavigateToResearch = useCallback((keyword) => {
    setActiveGapPopover(null);
    if (onNavigateToTab) {
      onNavigateToTab('research', { query: keyword });
    }
  }, [onNavigateToTab]);

  /**
   * 꼬리질문 튜닝 상담 전송 (물리 안전 마진 사전 검증 포함)
   */
  const handleSendTailQuestion = useCallback(async (userPrompt, overrideReason = '') => {
    if (!currentSession || !userPrompt.trim()) return;

    // 1. 물리 안전 마진 사전 검증
    const guard = physicalSafetyGuardService.validateSafetyMargins(userPrompt, overrideReason);
    if (!guard.isSafe && guard.requiresOverride) {
      setNotification({
        type: 'warning',
        message: guard.warningMessage || '물리 안전 마진을 초과하여 예외 사유가 필요합니다.'
      });
      return false;
    }

    setIsAdvising(true);
    try {
      const res = await comparisonRepo.tuneAdvisor(currentSession.id, {
        userPrompt: userPrompt.trim(),
        manualConditions: overrideReason ? { overrideReason } : undefined
      });

      let formattedAdvice = res.advice || '';
      if (!formattedAdvice) {
        const parts = [];
        if (res.riskDetected) {
          parts.push(`⚠️ [위험 감지] ${res.riskDetected}`);
        }
        if (res.advisorRecommendation) {
          const { compensationA, compensationB } = res.advisorRecommendation;
          if (compensationA) {
            parts.push(
              `📌 [추천 보상안 A] ${compensationA.title || compensationA.name || 'Plan A'}\n` +
              `• 개요: ${compensationA.description || ''}\n` +
              (compensationA.tradeOff ? `• 트레이드오프: ${compensationA.tradeOff}\n` : '') +
              (compensationA.processWindowNotice ? `• 공정 윈도우: ${compensationA.processWindowNotice}` : '')
            );
          }
          if (compensationB) {
            parts.push(
              `📌 [대안 보상안 B] ${compensationB.title || compensationB.name || 'Plan B'}\n` +
              `• 개요: ${compensationB.description || ''}\n` +
              (compensationB.tradeOff ? `• 트레이드오프: ${compensationB.tradeOff}\n` : '') +
              (compensationB.processWindowNotice ? `• 공정 윈도우: ${compensationB.processWindowNotice}` : '')
            );
          }
        }
        formattedAdvice = parts.join('\n\n') || '인과 분석 조언이 도출되었습니다.';
      }

      setChatHistory((prev) => [
        ...prev,
        {
          question: userPrompt.trim(),
          answer: formattedAdvice,
          timestamp: new Date().toISOString(),
          warnings: res.physicalGuardWarnings || (res.riskDetected ? [res.riskDetected] : [])
        }
      ]);
      return true;
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '인과 상담 요청에 실패했습니다.' });
      return false;
    } finally {
      setIsAdvising(false);
    }
  }, [currentSession]);

  /**
   * 비교 분석 결과 및 튜닝 상담을 Tab 3 거버넌스 티켓으로 내보내기
   */
  const handleExportReviewTicket = useCallback(async ({ title, overrideReason, reviewType }) => {
    if (!currentSession) return;
    setIsActionLoading(true);
    try {
      const res = await comparisonRepo.exportToReviewTicket(currentSession.id, {
        conceptId: currentSession.contextParams?.targetA || 'concept-tcb',
        title: title || `${currentSession.title} 비교 결과 개정안`,
        overrideReason: overrideReason?.trim() || '비교 매트릭스 다차원 분석 및 엔지니어링 조건 검토에 따른 개정 발의',
        author: currentUser?.name || '현장 엔지니어',
        reviewType: reviewType || 'minor_revision'
      });

      setExportedTicketId(res.ticketId);
      setIsExportModalOpen(false);
      setNotification({
        type: 'success',
        message: `비교 분석 결과가 검토 티켓(${res.ticketId})으로 성공적으로 내보내졌습니다.`
      });

      // 필요 시 Tab 3으로 자동 이동
      if (onNavigateToTab) {
        setTimeout(() => onNavigateToTab('review', { ticketId: res.ticketId }), 1200);
      }
    } catch (err) {
      setNotification({ type: 'error', message: err.message || '티켓 내보내기에 실패했습니다.' });
    } finally {
      setIsActionLoading(false);
    }
  }, [currentSession, currentUser, onNavigateToTab]);

  // 카테고리 필터링된 매트릭스 행 목록
  const filteredMatrixRows = useMemo(() => {
    if (selectedCategory === 'all') return matrixRows;
    return matrixRows.filter((r) => r.axisCategory === selectedCategory);
  }, [matrixRows, selectedCategory]);

  return {
    activeStep,
    trackMode,
    query,
    isClarifying,
    clarifyResult,
    targetA,
    targetB,
    domain,
    currentSession,
    matrixRows: filteredMatrixRows,
    allMatrixCount: matrixRows.length,
    selectedCategory,
    activeGapPopover,
    isMatrixLoading,
    chatHistory,
    isAdvising,
    isExportModalOpen,
    isActionLoading,
    exportedTicketId,
    notification,
    setTrackMode,
    setQuery,
    setTargetA,
    setTargetB,
    setDomain,
    setSelectedCategory,
    handleClarifyQuery,
    handleSelectBranch,
    handleStartDirectComparison,
    handleResetToSetup,
    handleOpenGapPopover,
    handleCloseGapPopover,
    handleNavigateToResearch,
    handleSendTailQuestion,
    handleExportReviewTicket,
    openExportModal: () => setIsExportModalOpen(true),
    closeExportModal: () => setIsExportModalOpen(false),
    clearNotification: () => setNotification(null)
  };
}
