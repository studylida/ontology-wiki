import { http } from './http';
import type { WikiCommand, WikiComparison, WikiDetail, WikiList, WikiMutation, WikiPage, WikiRevision, WikiRevisionSummary } from '../types/wiki';
const root = '/wiki/pages';
const pagePath = (id: string) => `${root}/${encodeURIComponent(id)}`;
export const wikiRepository = {
  list: (query: string, offset = 0, signal?: AbortSignal) => http<WikiList<WikiPage>>(`${root}?${new URLSearchParams({q: query, offset: String(offset)})}`, {signal}),
  detail: (id: string, signal?: AbortSignal) => http<WikiDetail>(pagePath(id), {signal}),
  history: (id: string, offset = 0, signal?: AbortSignal) => http<WikiList<WikiRevisionSummary>>(`${pagePath(id)}/revisions?offset=${offset}`, {signal}),
  revision: (id: string, revision: string, signal?: AbortSignal) => http<WikiRevision>(`${pagePath(id)}/revisions/${encodeURIComponent(revision)}`, {signal}),
  compare: (id: string, before: string, after: string, signal?: AbortSignal) => http<WikiComparison>(`${pagePath(id)}/compare?${new URLSearchParams({fromRevisionId: before, toRevisionId: after})}`, {signal}),
  mutate: (command: WikiCommand) => {
    const path = command.kind === 'create' ? root : pagePath(command.pageId) +
      ({edit: '/revisions', restore: '/restore', protect: '/protection'} as const)[command.kind];
    return http<WikiMutation>(path, {method: command.kind === 'protect' ? 'PATCH' : 'POST', body: command.body});
  },
};
export function guardWikiUnload(enabled: boolean) {
  const handler = (event: BeforeUnloadEvent) => {event.preventDefault(); event.returnValue = '';};
  if (enabled) window.addEventListener('beforeunload', handler);
  return () => window.removeEventListener('beforeunload', handler);
}
