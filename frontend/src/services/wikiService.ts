import { newRequestId } from '../repositories/workspaceStorage';
import { wikiRepository } from '../repositories/wikiRepository';
import type { WikiCommand, WikiDetail, WikiDraft, WikiMutation, WikiPending, WikiRevision } from '../types/wiki';
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
/** Notify the controller of a durable receipt before the separate readback. */
export async function applyWikiCommand(command: WikiCommand, acknowledged: WikiMutation | null = null,
  onAcknowledged: (receipt: WikiMutation) => void = () => {}) {
  const receipt = acknowledged || await wikiRepository.mutate(command);
  onAcknowledged(receipt);
  const page = await wikiRepository.detail(receipt.pageId);
  return {receipt, page};
}
export function draftFromPending(pending: WikiPending | null): WikiDraft {
  const command = pending?.command;
  return command && (command.kind === 'create' || command.kind === 'edit') ? {
    title: command.body.title, markdown: command.body.markdown,
    sourceNote: command.body.sourceNote, changeSummary: command.body.changeSummary,
  } : emptyWikiDraft();
}
export function wikiMutationNotice(command: WikiCommand, receipt: WikiMutation, page: WikiDetail): string {
  if (page.version !== receipt.version) return '저장을 확인했습니다. 현재 문서에는 이후의 변경도 포함되어 있습니다.';
  if (command.kind === 'protect') return page.locked ? '관리자가 문서를 보호했습니다.' : '문서 보호를 해제했습니다.';
  return `판본 ${page.revisionNumber}이 저장되었습니다.${receipt.replayed ? ' 기존 요청의 저장 결과를 확인했습니다.' : ''}`;
}
