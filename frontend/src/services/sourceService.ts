import type { Citation, SourceSelection } from '../types/contracts';
import { sourceRepository } from '../repositories/sourceRepository';
export const sourceSelection = (citation: Citation): SourceSelection => ({revisionId: citation.sourceRevisionId,
  title: citation.title, citation, ...(citation.sourceKind === 'wiki' ? {sourceKind: 'wiki' as const, pageId: citation.pageId}
    : {sourceKind: 'document' as const, documentId: citation.documentId})});
export const sourceKey = (s: SourceSelection) => `${s.sourceKind || 'document'}:${s.sourceKind === 'wiki' ? s.pageId : s.documentId}:${s.revisionId}:${s.citation?.passageId || ''}`;
export async function readSource(selection: SourceSelection, signal?: AbortSignal) {
  const value = await sourceRepository.read(selection, signal);
  if (value.revisionId !== selection.revisionId || (selection.sourceKind === 'wiki'
    ? !('pageId' in value) || value.pageId !== selection.pageId
    : !('documentId' in value) || value.documentId !== selection.documentId)) throw new Error('요청한 출처 판본과 응답이 일치하지 않습니다.');
  if (selection.citation && !value.passages.some(p => p.id === selection.citation?.passageId && !p.excluded))
    throw new Error('인용한 구간을 해당 판본에서 확인할 수 없습니다.');
  return value;
}
export const downloadEvidence = sourceRepository.download;
