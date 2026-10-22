/** Tab 2 state: purpose → comparison → follow-up → research → same comparison. */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { comparisonRepo } from '../repositories/comparisonRepo';
import { comparisonService } from '../services/comparisonService';

export function useComparisonController({ currentUser, onNavigateToTab } = {}) {
  const [activeStep, setActiveStep] = useState('setup');
  const [trackMode, setTrackMode] = useState('track1');
  const [query, setQuery] = useState('');
  const [isClarifying, setIsClarifying] = useState(false);
  const [clarifyResult, setClarifyResult] = useState(null);
  const [concepts, setConcepts] = useState([]);
  const [targetA, setTargetA] = useState('');
  const [targetB, setTargetB] = useState('');
  const [domain, setDomain] = useState('');
  const [currentSession, setCurrentSession] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [activeGapPopover, setActiveGapPopover] = useState(null);
  const [isMatrixLoading, setIsMatrixLoading] = useState(false);
  const [isAdvising, setIsAdvising] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [exportedTicketId, setExportedTicketId] = useState(null);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    let mounted = true;
    comparisonRepo.listConcepts().then((data) => { if (mounted) setConcepts(data); })
      .catch((err) => { if (mounted) setNotification({ type: 'error', message: err.message }); });
    return () => { mounted = false; };
  }, []);

  const applySession = useCallback((session) => {
    setCurrentSession(session);
    setQuery(session.query);
    setTargetA(session.contextParams.targetA);
    setTargetB(session.contextParams.targetB);
    setDomain(session.contextParams.domain || '');
    setSelectedCategory('all');
    setActiveStep('matrix');
  }, []);

  const handleClarifyQuery = useCallback(async (text) => {
    const question = (text || query).trim();
    if (!question) return;
    setQuery(question);
    setIsClarifying(true);
    try { setClarifyResult(await comparisonRepo.clarify({ query: question })); }
    catch (err) { setNotification({ type: 'error', message: err.message }); }
    finally { setIsClarifying(false); }
  }, [query]);

  const executeComparison = useCallback(async (a, b, title, comparisonDomain = '', purpose = query) => {
    setIsMatrixLoading(true);
    try {
      applySession(await comparisonService.start({ targetA: a, targetB: b, title,
        query: purpose, domain: comparisonDomain, userId: currentUser?.id || 'anonymous' }));
    } catch (err) { setNotification({ type: 'error', message: err.message }); }
    finally { setIsMatrixLoading(false); }
  }, [query, currentUser, applySession]);

  const handleSelectBranch = useCallback((branch) => {
    return executeComparison(branch.targetA, branch.targetB, branch.title, branch.domain);
  }, [executeComparison]);

  const handleDirectCompare = useCallback((a, b, purpose = '') => {
    const name = (id) => concepts.find((c) => c.id === id)?.title || id;
    return executeComparison(a, b, `${name(a)} / ${name(b)} 비교`, domain, purpose);
  }, [concepts, domain, executeComparison]);

  const handleNavigateToResearch = useCallback((keyword) => {
    if (!currentSession) return;
    const comparisonContext = comparisonService.researchContext(currentSession, activeGapPopover);
    setActiveGapPopover(null);
    onNavigateToTab?.('research', { query: keyword || currentSession.query, comparisonContext });
  }, [currentSession, activeGapPopover, onNavigateToTab]);

  const handleUseResearchEvidence = useCallback(async (params) => {
    setIsMatrixLoading(true);
    try {
      applySession(await comparisonService.returnFromResearch(params));
      if (params.selectedEvidenceIds?.length) setNotification({ type: 'success', message: '기존 질문과 대화를 유지하고 선택한 문헌으로 비교 해설을 보강했습니다.' });
    } catch (err) { setNotification({ type: 'error', message: err.message }); }
    finally { setIsMatrixLoading(false); }
  }, [applySession]);

  const handleSendTailQuestion = useCallback(async (question) => {
    if (!currentSession || !question.trim() || isAdvising) return false;
    setIsAdvising(true);
    try {
      const result = await comparisonRepo.tuneAdvisor(currentSession.id, { userPrompt: question.trim() });
      applySession(result.session);
      return true;
    } catch (err) { setNotification({ type: 'error', message: err.message }); return false; }
    finally { setIsAdvising(false); }
  }, [currentSession, isAdvising, applySession]);

  const handleExportReviewTicket = useCallback(async ({ title, overrideReason, reviewType }) => {
    if (!currentSession) return;
    setIsActionLoading(true);
    try {
      const result = await comparisonRepo.exportToReviewTicket(currentSession.id, {
        conceptId: currentSession.contextParams.targetA,
        title: title || `${currentSession.title} 검토 제안`, overrideReason: overrideReason?.trim() || '',
        reviewType: reviewType || '비교 검토', author: currentUser?.name || ''
      });
      setExportedTicketId(result.ticketId);
      setIsExportModalOpen(false);
      onNavigateToTab?.('review', { ticketId: result.ticketId });
    } catch (err) { setNotification({ type: 'error', message: err.message }); }
    finally { setIsActionLoading(false); }
  }, [currentSession, currentUser, onNavigateToTab]);

  const result = useMemo(() => currentSession ? comparisonService.sessionView(currentSession)
    : { matrix: [], summary: '', history: [], evidences: [] }, [currentSession]);
  const categories = useMemo(() => [{ id: 'all', label: '전체 축' },
    ...Array.from(new Map(result.matrix.map((row) => [row.axisCategory,
      { id: row.axisCategory, label: row.categoryLabel }])).values())], [result.matrix]);

  return {
    activeStep, trackMode, query, isClarifying, clarifyResult, concepts, targetA, targetB, domain,
    currentSession, matrixRows: selectedCategory === 'all' ? result.matrix : result.matrix.filter((r) => r.axisCategory === selectedCategory),
    categories, comparisonSummary: result.summary, comparisonEvidences: result.evidences,
    allMatrixCount: result.matrix.length, selectedCategory, activeGapPopover, isMatrixLoading,
    chatHistory: result.history, isAdvising, isExportModalOpen, isActionLoading, exportedTicketId, notification,
    setTrackMode, setQuery, setTargetA, setTargetB, setDomain, setSelectedCategory,
    handleClarifyQuery, handleSelectBranch, handleDirectCompare,
    handleStartDirectComparison: () => handleDirectCompare(targetA, targetB, query),
    handleResetToSetup: () => { setActiveStep('setup'); setActiveGapPopover(null); },
    handleOpenGapPopover: (row, targetSide) => setActiveGapPopover({ row, targetSide }),
    handleCloseGapPopover: () => setActiveGapPopover(null),
    handleNavigateToResearch, handleUseResearchEvidence, handleSendTailQuestion, handleExportReviewTicket,
    openExportModal: () => {
      if (!currentUser || currentUser.level < 2) {
        setNotification({ type: 'warning', message: '로그인한 현장 엔지니어(Level 2) 이상만 검토 티켓을 발의할 수 있습니다.' });
      } else setIsExportModalOpen(true);
    },
    closeExportModal: () => setIsExportModalOpen(false), clearNotification: () => setNotification(null)
  };
}
