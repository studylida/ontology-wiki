// @vitest-environment jsdom
import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { useWikiController } from './useWikiController';
import { wikiRepository } from '../repositories/wikiRepository';
import { ApiError } from '../repositories/http';
import type { WikiDetail } from '../types/wiki';
vi.mock('../repositories/wikiRepository', () => ({guardWikiUnload: () => () => {}, wikiRepository: {
  list: vi.fn(), detail: vi.fn(), history: vi.fn(), revision: vi.fn(), compare: vi.fn(), mutate: vi.fn(),
}}));
const original = {id: 'p1', title: '원래 제목', version: 1, revisionNumber: 1, currentRevisionId: 'r1', canEdit: true, canProtect: false,
  revision: {id: 'r1', number: 1, title: '원래 제목', markdown: '원래 내용', sourceNote: '', changeSummary: ''}} as WikiDetail;
beforeEach(() => {vi.clearAllMocks(); vi.mocked(wikiRepository.list).mockResolvedValue({items: [], total: 0, offset: 0, limit: 30});
  vi.mocked(wikiRepository.detail).mockResolvedValue(original);});
afterEach(cleanup);
it('keeps the user draft on conflict and does not silently adopt a new base', async () => {
  const hook = renderHook(useWikiController);
  await act(async () => {await hook.result.current.select('p1');});
  act(() => hook.result.current.startEdit()); act(() => hook.result.current.change('markdown', '내 변경'));
  vi.mocked(wikiRepository.mutate).mockRejectedValue(new ApiError(409, 'wiki_version_conflict', '변경됨'));
  act(() => hook.result.current.save());
  await waitFor(() => expect(hook.result.current.conflicted).toBe(true));
  expect(hook.result.current.draft.markdown).toBe('내 변경');
  expect(hook.result.current.editing).toBe(true); expect(hook.result.current.page?.version).toBe(1);
  expect(hook.result.current.pending).toBeNull();
});
it('reuses the same payload and request id after unknown delivery', async () => {
  const hook = renderHook(useWikiController);
  act(() => hook.result.current.startNew());
  act(() => {hook.result.current.change('title', '제목'); hook.result.current.change('markdown', '본문');});
  vi.mocked(wikiRepository.mutate).mockRejectedValueOnce(new ApiError(0, 'NETWORK_UNAVAILABLE', '연결 끊김'))
    .mockResolvedValueOnce({pageId: 'p1', revisionId: 'r1', version: 1, replayed: true});
  act(() => hook.result.current.save());
  await waitFor(() => expect(hook.result.current.pending).not.toBeNull());
  await waitFor(() => expect(hook.result.current.busy).toBe(false));
  const first = vi.mocked(wikiRepository.mutate).mock.calls[0][0];
  act(() => hook.result.current.resend());
  await waitFor(() => expect(hook.result.current.pending).toBeNull());
  expect(vi.mocked(wikiRepository.mutate).mock.calls[1][0]).toEqual(first);
  expect(hook.result.current.notice).toContain('기존 요청');
});
