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
