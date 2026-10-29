import { http } from './http';
import type { DocumentWikiNotice } from '../types/documentWiki';
export const documentWikiRepository = {
  get: (id: string, signal?: AbortSignal) => http<DocumentWikiNotice>(`/documents/${encodeURIComponent(id)}/wiki-suggestions`, {signal}),
};
