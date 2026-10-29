// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { clearWorkspace, pendingWikiMutation, savePendingWikiMutation } from './workspaceStorage';
import { isWikiPending, type WikiPending } from '../types/wiki';
const pending: WikiPending = {command: {kind: 'create', body: {requestId: 'unique-request-id', title: '제목',
  markdown: '보존할 내용  \n', sourceNote: '경험', changeSummary: ''}}, receipt: null};
beforeEach(() => sessionStorage.clear());
afterEach(() => vi.restoreAllMocks());
it('retains only submitted requests, isolates users and clears them at logout', () => {
  expect(pendingWikiMutation('alice')).toBeNull();
  expect(savePendingWikiMutation('alice', pending)).toBe(true);
  expect(pendingWikiMutation('alice')).toEqual(pending);
  expect(pendingWikiMutation('bob')).toBeNull();
  clearWorkspace('bob'); expect(pendingWikiMutation('alice')).toEqual(pending);
  clearWorkspace('alice'); expect(pendingWikiMutation('alice')).toBeNull();
});
it('ignores malformed state and never converts old drafts to commands', () => {
  for (const value of ['bad json', '{"kind":"draft"}', '{"command":{},"receipt":null}']) {
    sessionStorage.setItem('knowledge-assistant.v3.alice.wiki-pending', value);
    expect(pendingWikiMutation('alice')).toBeNull();
  }
  expect(isWikiPending({...pending, command: {...pending.command, kind: 'delete'}})).toBe(false);
  expect(isWikiPending({command: {kind: 'restore', pageId: 'p1', body: {requestId: 'request-id', baseVersion: 1, revisionId: 'r1'}},
    receipt: {pageId: 'another-page', revisionId: 'r1', version: 2, replayed: false}})).toBe(false);
});
it('reports storage failure instead of promising persistence', () => {
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {throw new Error('quota');});
  expect(savePendingWikiMutation('alice', pending)).toBe(false);
});
