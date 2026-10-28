import { isCitation, type Citation } from '../types/contracts';

/** One mapping for body, source list and source panel. Never renumber server citations. */
export function citationIndex(citations: Citation[]) {
  const map = new Map<string, Citation>(), numbers = new Set<number>();
  for (const citation of citations) {
    if (!isCitation(citation) || map.has(citation.passageId) || numbers.has(citation.number)) continue;
    map.set(citation.passageId, citation); numbers.add(citation.number);
  }
  return map;
}
export const orderedCitations = (citations: Citation[]) => [...citationIndex(citations).values()].sort((a, b) => a.number - b.number);
export function safeUrl(raw?: string): string | undefined {
  if (!raw) return undefined;
  try { const url = new URL(raw); return ['https:', 'http:'].includes(url.protocol) ? url.href : undefined; }
  catch { return undefined; }
}
