import { newRequestId } from '../repositories/workspaceStorage';
import { wikiRepository } from '../repositories/wikiRepository';
import type { WikiCommand, WikiDetail, WikiDraft, WikiRevision } from '../types/wiki';
export const emptyWikiDraft = (): WikiDraft => ({title: '', markdown: '', sourceNote: '', changeSummary: ''});
export const draftFromRevision = (revision: WikiRevision): WikiDraft => ({title: revision.title,
  markdown: revision.markdown, sourceNote: revision.sourceNote, changeSummary: ''});
export function saveWikiCommand(draft: WikiDraft, page: WikiDetail | null, baseVersion: number | null): WikiCommand {
  const body = {...draft, requestId: newRequestId()};
  if (!page) return {kind: 'create', body};
  if (baseVersion === null) throw new Error('편집 기준 판본이 없습니다. 문서를 다시 확인해 주세요.');
  return {kind: 'edit', pageId: page.id, body: {...body, baseVersion}};
}
export const restoreWikiCommand = (page: WikiDetail, revisionId: string): WikiCommand => ({kind: 'restore',
  pageId: page.id, body: {requestId: newRequestId(), baseVersion: page.version, revisionId}});
export const protectWikiCommand = (page: WikiDetail): WikiCommand => ({kind: 'protect', pageId: page.id,
  body: {requestId: newRequestId(), baseVersion: page.version, locked: !page.locked}});
export const validWikiDraft = (draft: WikiDraft) => !!draft.title.trim() && !!draft.markdown.trim();
export async function applyWikiCommand(command: WikiCommand) {
  const receipt = await wikiRepository.mutate(command);
  // A successful write is not an AI answer or a search-index completion.
  const page = await wikiRepository.detail(receipt.pageId);
  return {receipt, page};
}
