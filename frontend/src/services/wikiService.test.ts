import { expect, it, vi } from 'vitest';
import { draftFromRevision, emptyWikiDraft, saveWikiCommand, validWikiDraft, wikiMutationNotice } from './wikiService';
import type { WikiDetail, WikiRevision } from '../types/wiki';
vi.mock('../repositories/workspaceStorage', () => ({newRequestId: () => 'same-test-request'}));
const revision: WikiRevision = {id: 'r1', pageId: 'p1', number: 1, title: '개념', markdown: '  code  \n', sourceNote: '경험',
  editor: {id: 'u1', username: 'alice'}, createdAt: '2026-10-29', changeSummary: '처음', restoredFromId: null};
it('keeps exact Markdown whitespace and clears only the next change summary', () => {
  expect(draftFromRevision(revision)).toEqual({title: '개념', markdown: '  code  \n', sourceNote: '경험', changeSummary: '', aliasesText: '', meaning: ''});
});
it('rejects empty drafts without requiring a source file', () => {
  expect(validWikiDraft(emptyWikiDraft())).toBe(false);
  expect(validWikiDraft({...emptyWikiDraft(), title: '개념', markdown: '본문'})).toBe(true);
});
it('captures a fixed create payload rather than holding a mutable draft', () => {
  const draft = draftFromRevision(revision), command = saveWikiCommand(draft, null, null);
  draft.markdown = 'changed later';
  expect(command.kind).toBe('create'); expect(command.body.requestId).toBe('same-test-request');
  expect('markdown' in command.body && command.body.markdown).toBe('  code  \n');
});
it('keeps the original edit base even when the latest page has changed', () => {
  const page = {id: 'p1', version: 3} as WikiDetail;
  const command = saveWikiCommand(draftFromRevision(revision), page, 1);
  expect(command.kind === 'edit' && command.body.baseVersion).toBe(1);
  expect(() => saveWikiCommand(draftFromRevision(revision), page, null)).toThrow();
});

it("does not label another editor's subsequent revision as this request result", () => {
  const command = saveWikiCommand(draftFromRevision(revision), null, null);
  const notice = wikiMutationNotice(command, {pageId: 'p1', revisionId: 'r1', version: 1, replayed: false},
    {version: 3, revisionNumber: 3} as WikiDetail);
  expect(notice).toContain('이후의 변경');
  expect(notice).not.toContain('판본 3이 저장');
});
it('stores aliases and meaning while preserving markdown exactly', () => {
  const draft = {...emptyWikiDraft(), title: 'RUL', markdown: '  unchanged  \n', aliasesText: '잔여 수명\nRemaining Useful Life', meaning: '설비 상태'};
  const cmd = saveWikiCommand(draft, null, null);
  expect(cmd.kind).toBe('create');
  if (cmd.kind === 'create') {
    expect(cmd.body.aliases).toEqual(['잔여 수명', 'Remaining Useful Life']);
    expect(cmd.body).not.toHaveProperty('aliasesText'); expect(cmd.body.markdown).toBe(draft.markdown);
  }
});
