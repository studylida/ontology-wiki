/** Acquisition and selection rules mirror the server; historical sessions stay selectable. */
export function safeSourceUrl(value) {
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url.href : ''; }
  catch { return ''; }
}

export function usableEvidenceIds(feed, selectedIds) {
  return feed.filter((item) => selectedIds.includes(item.id) && item.quote?.trim()
    && ['registered_excerpt', 'source_excerpt', 'abstract', 'external_excerpt'].includes(item.retrievalStatus)
    && item.assessmentCurrent !== false
    && (!item.assessment || item.assessment.decision === 'included')).map((item) => item.id);
}

export function recommendedEvidenceIds(feed) {
  return usableEvidenceIds(feed, feed.filter((item) => item.assessment?.decision === 'included').map((item) => item.id));
}

export function evidenceState(item) {
  if (item.assessmentCurrent === false) return item.deferReason || 'not_assessed';
  if (item.assessment?.decision === 'deferred') return item.deferReason || (item.retrievalStatus === 'metadata' ? 'content_unavailable' : 'insufficient_content');
  return item.assessment?.decision || 'unverified';
}

export function researchCounts(feed) {
  return feed.reduce((counts, item) => { const state = evidenceState(item); counts[state] = (counts[state] || 0) + 1; return counts; }, {});
}

export function visibleResearchEvidence(feed, filter, limit) {
  const order = { included: 0, content_unavailable: 1, insufficient_content: 2, not_assessed: 3, assessment_failed: 4, unverified: 5, excluded: 6 };
  return feed.filter((item) => filter === 'all' || evidenceState(item) === filter)
    .sort((a, b) => (order[evidenceState(a)] ?? 5) - (order[evidenceState(b)] ?? 5)).slice(0, limit);
}
