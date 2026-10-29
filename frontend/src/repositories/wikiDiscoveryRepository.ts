import { http } from './http';
import type { WikiAlternative, WikiIndexStatus, WikiSearchResult } from '../types/wikiDiscovery';
const path = (id: string) => `/wiki/pages/${encodeURIComponent(id)}`;
export const wikiDiscoveryRepository = {
  search: (query: string, signal?: AbortSignal) => http<WikiSearchResult>('/wiki/search', {method: 'POST', body: {query}, signal}),
  similar: (title: string, markdown: string, excludePageId?: string, signal?: AbortSignal) =>
    http<WikiSearchResult>('/wiki/similar', {method: 'POST', body: {title, markdown, excludePageId}, signal}),
  alternatives: (id: string, signal?: AbortSignal) => http<WikiAlternative[]>(`${path(id)}/alternatives`, {signal}),
  index: (id: string, signal?: AbortSignal) => http<WikiIndexStatus>(`${path(id)}/index`, {signal}),
  retryIndex: (id: string, baseVersion: number, signal?: AbortSignal) => http<WikiIndexStatus>(`${path(id)}/index/retry`, {method: 'POST', body: {baseVersion}, signal}),
};
