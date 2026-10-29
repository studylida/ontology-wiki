/** Canonical identity links only. No arbitrary relative URLs, traversal or protocol-relative hosts. */
const pagePath = /^\/wiki\/(wpg_[a-f0-9]{32})$/;
export function wikiPageId(href?: string): string | null {
  return href ? pagePath.exec(href)?.[1] || null : null;
}
export function wikiPageHref(id: string): string {
  const path = `/wiki/${id}`;
  if (!wikiPageId(path)) throw new Error('올바르지 않은 위키 문서 ID입니다.');
  return path;
}
