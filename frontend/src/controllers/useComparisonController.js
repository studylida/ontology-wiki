/** Tab 2 state: purpose → comparison → follow-up → research → same comparison. */
import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { comparisonRepo } from '../repositories/comparisonRepo';
import { comparisonService } from '../services/comparisonService';

export function useComparisonController({ currentUser, onNavigateToTab } = {}) {
  const [activeStep, setActiveStep] = useState('setup');
  const [trackMode, setTrackMode] = useState('track1');
  const [query, setQuery] = useState('');
  const [isClarifying, setIsClarifying] = useState(false);
  const [clarifyResult, setClarifyResult] = useState(null);
  const [concepts, setConcepts] = useState([]);
  const [axisCandidates, setAxisCandidates] = useState([]);
  const [selectedAxes, setSelectedAxes] = useState([]);
  const [customAxisText, setCustomAxisText] = useState('');
  const [answers, setAnswers] = useState({});
  const [targetA, setTargetA] = useState('');
  const [targetB, setTargetB] = useState('');
  const [domain, setDomain] = useState('');
  const [draft, setDraft] = useState({targetAName: '', targetBName: '', purpose: ''});
  const [currentSession, setCurrentSession] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [activeGapPopover, setActiveGapPopover] = useState(null);
  const [isMatrixLoading, setIsMatrixLoading] = useState(false);
  const [isAdvising, setIsAdvising] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [exportedTicketId, setExportedTicketId] = useState(null);
  const [notification, setNotification] = useState(null);
  const requestVersion = useRef(0);

  useEffect(() => {
    let mounted = true;
    comparisonRepo.listConcepts().then((data) => { if (mounted) setConcepts(data); })
      .catch((err) => { if (mounted) setNotification({ type: 'error', message: err.message }); });
    return () => { mounted = false; requestVersion.current += 1; };
  }, []);

  const applySession = useCallback((session) => {
    setCurrentSession(session);
    setQuery(session.query);
    setTargetA(session.contextParams.targetA);
    setTargetB(session.contextParams.targetB);
    setDomain(session.contextParams.domain || '');
    setDraft({...session.contextParams.draft,
      targetAName: session.contextParams.draft?.targetAName || session.contextParams.targetAName,
      targetBName: session.contextParams.draft?.targetBName || session.contextParams.targetBName,
      purpose: session.contextParams.draft?.purpose || session.query});
    setAnswers(session.contextParams.clarificationAnswers || {});
    setSelectedCategory(session.snapshots?.[2]?.matrix?.some(row => row.axisCategory === 'purpose') ? 'purpose' : 'all');
    setAxisCandidates(session.contextParams.axes || []);
    setSelectedAxes(session.contextParams.axes || []);
    setActiveStep('matrix');
  }, []);

  const handleQueryChange = useCallback((value) => {
    requestVersion.current += 1;
    setQuery(value); setClarifyResult(null); setAxisCandidates([]); setSelectedAxes([]); setAnswers({}); setIsClarifying(false);
    setIsMatrixLoading(false); setIsActionLoading(false); setIsAdvising(false);
    if (trackMode === 'track1') {setTargetA(''); setTargetB(''); setDraft({targetAName: '', targetBName: '', purpose: ''}); setDomain(''); setCustomAxisText('');}
  }, [trackMode]);

  const draftAxes = useMemo(() => [...selectedAxes, ...customAxisText.split(/[,\n]/)
    .map(label => label.trim()).filter(Boolean).map(label => ({axisId: label, label, category: 'purpose', categoryLabel: '목적별 평가', terms: [label]}))], [selectedAxes, customAxisText]);

  const invalidateDraftRequest = () => {
    requestVersion.current += 1;
    setIsClarifying(false); setIsMatrixLoading(false);
    setClarifyResult(previous => previous ? {...previous, branches: []} : null);
  };
  const changeDraft = (field, value) => {
    invalidateDraftRequest();
    if (field === 'applicationContext') setDomain(value);
    else setDraft(previous => ({...previous, [field]: value}));
    if (['targetAName', 'targetBName', 'purpose'].includes(field)) {setAxisCandidates([]); setSelectedAxes([]);}
    if (field === 'targetAName') setTargetA('');
    if (field === 'targetBName') setTargetB('');
  };
  const changeTarget = (setter, field, value) => {
    invalidateDraftRequest(); setter(value);
    const concept = concepts.find(c => c.id === value);
    if (concept) setDraft(previous => ({...previous, [field]: previous[field] || concept.title}));
  };

  const handleClarifyQuery = useCallback(async (text) => {
    const question = (text || query || draft.purpose).trim();
    if (!question) return;
    const requestId = ++requestVersion.current;
    setQuery(question); setIsClarifying(true);
    try {
      const result = await comparisonRepo.clarify({query: question, targetA: targetA || null, targetB: targetB || null,
        answers, draft: {...draft, applicationContext: domain, axes: draftAxes}});
      if (requestId === requestVersion.current) {
        setClarifyResult(result); setTargetA(result.targetA || ''); setTargetB(result.targetB || '');
        if (result.draft) {setDraft(result.draft); setDomain(result.draft.applicationContext || '');}
        setAxisCandidates(result.dynamicAxesPool || []); setSelectedAxes(result.dynamicAxesPool || []); setCustomAxisText('');
      }
    }
    catch (err) { if (requestId === requestVersion.current) setNotification({ type: 'error', message: err.message }); }
    finally { if (requestId === requestVersion.current) setIsClarifying(false); }
  }, [query, targetA, targetB, answers, draft, domain, draftAxes]);

  const executeComparison = useCallback(async (a, b, title, comparisonDomain = '', purpose = query || draft.purpose) => {
    const requestId = ++requestVersion.current;
    setIsMatrixLoading(true);
    setIsActionLoading(false);
    setIsExportModalOpen(false);
    setExportedTicketId(null);
    setIsAdvising(false);
    setIsClarifying(false);
    try {
      let axes = draftAxes;
      let comparisonDraft = {...draft, applicationContext: comparisonDomain, axes};
      if (!axes.length) {
        const plan = await comparisonRepo.clarify({query: purpose, targetA: a, targetB: b, answers, draft: {...draft, applicationContext: comparisonDomain, axes: []}});
        if (requestId !== requestVersion.current) return;
        axes = plan.dynamicAxesPool || []; setAxisCandidates(axes); setSelectedAxes(axes);
        if (!axes.length) throw new Error(plan.message || '비교할 평가 항목을 입력해 주세요.');
        comparisonDraft = plan.draft || comparisonDraft;
      }
      const session = await comparisonService.start({ targetA: a, targetB: b, title,
        query: purpose, domain: comparisonDraft.applicationContext || comparisonDomain, axes, answers, draft: {...comparisonDraft, axes}, userId: currentUser?.id || 'anonymous' });
      if (requestId === requestVersion.current) applySession(session);
    } catch (err) { if (requestId === requestVersion.current) setNotification({ type: 'error', message: err.message }); }
    finally { if (requestId === requestVersion.current) setIsMatrixLoading(false); }
  }, [query, currentUser, applySession, draftAxes, answers, draft]);

  const handleDirectCompare = useCallback((a, b, purpose = '') => {
    const name = (id) => concepts.find((c) => c.id === id)?.title || id;
    return executeComparison(a, b, `${name(a)} / ${name(b)} 비교`, domain, purpose);
  }, [concepts, domain, executeComparison]);

  const handleNavigateToResearch = useCallback((keyword) => {
    if (activeStep === 'setup') {
      const topic = keyword || [draft.targetAName, draft.targetBName, draft.purpose, domain, ...draftAxes.map(a => a.label)].filter(Boolean).join(' / ') || query;
      if (topic) onNavigateToTab?.('research', {query: topic});
      return;
    }
    if (!currentSession) return;
    const comparisonContext = comparisonService.researchContext(currentSession, activeGapPopover);
    setActiveGapPopover(null);
    onNavigateToTab?.('research', { query: keyword || currentSession.contextParams?.draft?.purpose || currentSession.query, comparisonContext });
  }, [currentSession, activeGapPopover, onNavigateToTab, activeStep, draft, domain, draftAxes, query]);

  const handleUseResearchEvidence = useCallback(async (params) => {
    const requestId = ++requestVersion.current;
    setIsMatrixLoading(true);
    setIsActionLoading(false);
    setIsExportModalOpen(false);
    setIsAdvising(false);
    setIsClarifying(false);
    try {
      const session = await comparisonService.returnFromResearch(params);
      if (requestId !== requestVersion.current) return;
      applySession(session);
      if (params.selectedEvidenceIds?.length) setNotification({ type: 'success', message: '기존 질문과 대화를 유지하고 선택한 문헌으로 비교 해설을 보강했습니다.' });
    } catch (err) { if (requestId === requestVersion.current) setNotification({ type: 'error', message: err.message }); }
    finally { if (requestId === requestVersion.current) setIsMatrixLoading(false); }
  }, [applySession]);

  const handleSendTailQuestion = useCallback(async (question) => {
    if (!currentSession || !question.trim() || isAdvising) return false;
    const requestId = ++requestVersion.current;
    setIsAdvising(true);
    try {
      const result = await comparisonRepo.tuneAdvisor(currentSession.id, { userPrompt: question.trim() });
      if (requestId !== requestVersion.current) return false;
      applySession(result.session);
      return true;
    } catch (err) { if (requestId === requestVersion.current) setNotification({ type: 'error', message: err.message }); return false; }
    finally { if (requestId === requestVersion.current) setIsAdvising(false); }
  }, [currentSession, isAdvising, applySession]);

  const handleExportReviewTicket = useCallback(async ({ title, overrideReason, reviewType }) => {
    if (!currentSession) return;
    const requestId = requestVersion.current;
    setIsActionLoading(true);
    try {
      const result = await comparisonRepo.exportToReviewTicket(currentSession.id, {
        conceptId: currentSession.contextParams.targetA,
        title: title || `${currentSession.title} 검토 제안`, overrideReason: overrideReason?.trim() || '',
        reviewType: reviewType || '비교 검토', author: currentUser?.name || ''
      });
      if (requestId !== requestVersion.current) return;
      setExportedTicketId(result.ticketId);
      setIsExportModalOpen(false);
      onNavigateToTab?.('review', { ticketId: result.ticketId });
    } catch (err) { if (requestId === requestVersion.current) setNotification({ type: 'error', message: err.message }); }
    finally { if (requestId === requestVersion.current) setIsActionLoading(false); }
  }, [currentSession, currentUser, onNavigateToTab]);

  const result = useMemo(() => currentSession ? comparisonService.sessionView(currentSession)
    : { matrix: [], summary: '', history: [], evidences: [] }, [currentSession]);
  const categories = useMemo(() => [{ id: 'all', label: '전체 자료' },
    ...Array.from(new Map(result.matrix.map((row) => [row.axisCategory,
      { id: row.axisCategory, label: row.categoryLabel }])).values())], [result.matrix]);

  return {
    activeStep, trackMode, query, isClarifying, clarifyResult, concepts, targetA, targetB, domain,
    currentSession, matrixRows: selectedCategory === 'all' ? result.matrix : result.matrix.filter((r) => r.axisCategory === selectedCategory),
    categories, comparisonSummary: result.summary, comparisonEvidences: result.evidences,
    allMatrixCount: result.matrix.length, selectedCategory, activeGapPopover, isMatrixLoading,
    chatHistory: result.history, isAdvising, isExportModalOpen, isActionLoading, exportedTicketId, notification,
    setTrackMode, setQuery: handleQueryChange,
    setTargetA: value => changeTarget(setTargetA, 'targetAName', value), setTargetB: value => changeTarget(setTargetB, 'targetBName', value),
    draft, setDraftField: changeDraft, setDomain: value => changeDraft('applicationContext', value), setSelectedCategory,
    axisCandidates, selectedAxes, customAxisText, setCustomAxisText, answers,
    setAnswer: (id, value) => setAnswers(previous => ({...previous, [id]: value})),
    toggleAxis: (axis) => setSelectedAxes(previous => previous.some(a => a.label === axis.label) ? previous.filter(a => a.label !== axis.label) : [...previous, axis]),
    handleConfirmTargets: () => handleClarifyQuery(query),
    handleApplyDraft: () => setTrackMode('track2'),
    handleClarifyQuery, handleDirectCompare,
    handleStartDirectComparison: () => handleDirectCompare(targetA, targetB, query || draft.purpose),
    handleResetToSetup: () => {
      requestVersion.current += 1;
      setIsMatrixLoading(false);
      setIsAdvising(false);
      setIsClarifying(false);
      setIsActionLoading(false);
      setIsExportModalOpen(false);
      setActiveStep('setup');
      setActiveGapPopover(null);
    },
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
