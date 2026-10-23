import { comparisonRepo } from '../repositories/comparisonRepo';

export const comparisonService = {
  async start({ targetA, targetB, title, query, domain, axes, answers, draft, userId }) {
    if (!targetA || !targetB || targetA === targetB) throw new Error('서로 다른 비교 대상 두 개를 선택해 주세요.');
    return comparisonRepo.createSession({ title, query: query.trim() || title, userId,
      contextParams: { targetA, targetB, domain, axes, draft, clarificationAnswers: answers } });
  },

  sessionView(session) {
    const snapshot = session.snapshots?.[2] || {};
    return { matrix: snapshot.matrix || [], summary: snapshot.aiCausalNote || '',
      history: (snapshot.deepDiveHistory || []).map((entry) => ({
        question: entry.query, answer: entry.explanation, timestamp: entry.timestamp
      })),
      evidences: [...(snapshot.evidences || []), ...(session.contextParams?.researchEvidence || [])] };
  },

  researchContext(session, gap) {
    return { comparisonSessionId: session.id, originalQuestion: session.query,
      targetA: session.contextParams.targetA, targetB: session.contextParams.targetB,
      targetAName: session.contextParams.targetAName, targetBName: session.contextParams.targetBName,
      axes: session.contextParams.axes || [],
      conditions: session.contextParams.conditions || [], gapAxis: gap?.row?.axis || '',
      targetSide: gap?.targetSide || '' };
  },

  async returnFromResearch({ comparisonSessionId, researchSessionId, selectedEvidenceIds }) {
    if (researchSessionId && selectedEvidenceIds?.length) {
      return comparisonRepo.addResearchEvidence(comparisonSessionId, { researchSessionId, selectedEvidenceIds });
    }
    return comparisonRepo.getSession(comparisonSessionId);
  }
};
