import { api } from './api';
import { downloadSource, http, saveBlob } from './http';
import type { EvidenceSource, SourceSelection, WikiSource } from '../types/contracts';
const id = encodeURIComponent;
export const sourceRepository = {
  read: (selection: SourceSelection, signal?: AbortSignal): Promise<EvidenceSource> => selection.sourceKind === 'wiki'
    ? http<WikiSource>(`/wiki/pages/${id(selection.pageId)}/passages?revisionId=${id(selection.revisionId)}`, {signal})
    : api.source(selection.documentId, selection.revisionId, signal),
  download: async (selection: SourceSelection) => {
    if (selection.sourceKind !== 'wiki') return downloadSource(selection.documentId, selection.revisionId);
    const blob = await http<Blob>(`/wiki/pages/${id(selection.pageId)}/markdown?revisionId=${id(selection.revisionId)}`, {binary: true});
    saveBlob(blob, `wiki-${selection.pageId}-${selection.revisionId}.md`);
  },
};
