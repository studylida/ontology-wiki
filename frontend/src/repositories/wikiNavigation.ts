import type { WorkspaceTab } from '../types/workspace';
import { wikiPageHref, wikiPageId } from '../services/wikiLinks';
export const currentWikiPage = () => wikiPageId(window.location.pathname);
export function rememberWikiPage(id: string, replace = false) {
  if (!wikiPageId(`/wiki/${id}`)) return;
  const path = wikiPageHref(id);
  if (window.location.pathname !== path) window.history[replace ? 'replaceState' : 'pushState'](null, '', path);
}
export function onWikiNavigation(listener: (id: string | null) => void) {
  const handler = () => listener(currentWikiPage());
  window.addEventListener('popstate', handler);
  return () => window.removeEventListener('popstate', handler);
}

/** Workspace routes share the same history owner as stored wiki links. */
export function currentWorkspaceTab(): WorkspaceTab {
  if (currentWikiPage() || window.location.pathname === '/wiki') return 'wiki';
  return window.location.pathname === '/documents' ? 'documents' : 'chat';
}
export function rememberWorkspaceTab(tab: WorkspaceTab) {
  // Do not replace an existing wiki permalink when its tab is already selected.
  if (currentWorkspaceTab() === tab) return;
  window.history.pushState(null, '', tab === 'chat' ? '/' : `/${tab}`);
}
