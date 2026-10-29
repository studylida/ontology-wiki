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
beforeEach(() => {sessionStorage.clear(); vi.clearAllMocks(); vi.mocked(wikiRepository.list).mockResolvedValue({items: [], total: 0, offset: 0, limit: 30});
  vi.mocked(wikiRepository.detail).mockResolvedValue(original);});
afterEach(cleanup);
it('keeps the user draft on conflict and does not silently adopt a new base', async () => {
  const hook = renderHook(() => useWikiController('u1'));
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
  const hook = renderHook(() => useWikiController('u1'));
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

it('retains an acknowledged mutation when the follow-up read fails, and retries GET only', async () => {
  const hook = renderHook(() => useWikiController('u1'));
  act(() => hook.result.current.startNew());
  act(() => {hook.result.current.change('title', '제목'); hook.result.current.change('markdown', '본문');});
  vi.mocked(wikiRepository.mutate).mockResolvedValueOnce({pageId: 'p1', revisionId: 'r1', version: 1, replayed: false});
  vi.mocked(wikiRepository.detail).mockRejectedValueOnce(new ApiError(404, 'temporary_read', '조회 실패'));
  act(() => hook.result.current.save());
  await waitFor(() => expect(hook.result.current.busy).toBe(false));
  expect(hook.result.current.pending).not.toBeNull();
  act(() => hook.result.current.resend());
  await waitFor(() => expect(hook.result.current.pending).toBeNull());
  expect(wikiRepository.mutate).toHaveBeenCalledTimes(1);
});
it('recovers an unacknowledged command after remount without automatically writing', async () => {
  const hook = renderHook(() => useWikiController('u1'));
  act(() => hook.result.current.startNew());
  act(() => {hook.result.current.change('title', '새 개념'); hook.result.current.change('markdown', '보존할 요청');});
  vi.mocked(wikiRepository.mutate).mockRejectedValueOnce(new ApiError(0, 'NETWORK_UNAVAILABLE', '응답 유실'));
  act(() => hook.result.current.save());
  await waitFor(() => expect(hook.result.current.busy).toBe(false));
  const submitted = vi.mocked(wikiRepository.mutate).mock.calls[0][0];
  hook.unmount();
  const restored = renderHook(() => useWikiController('u1'));
  expect(restored.result.current.pending).not.toBeNull();
  expect(restored.result.current.draft.markdown).toBe('보존할 요청');
  expect(wikiRepository.mutate).toHaveBeenCalledTimes(1);
  vi.mocked(wikiRepository.mutate).mockResolvedValueOnce({pageId: 'p1', revisionId: 'r1', version: 1, replayed: true});
  act(() => restored.result.current.resend());
  await waitFor(() => expect(restored.result.current.pending).toBeNull());
  expect(vi.mocked(wikiRepository.mutate).mock.calls[1][0]).toEqual(submitted);
});
it('restores a confirmed receipt after refresh and only fetches the page', async () => {
  const hook = renderHook(() => useWikiController('u1'));
  act(() => hook.result.current.startNew());
  act(() => {hook.result.current.change('title', '제목'); hook.result.current.change('markdown', '본문');});
  vi.mocked(wikiRepository.mutate).mockResolvedValueOnce({pageId: 'p1', revisionId: 'r1', version: 1, replayed: false});
  vi.mocked(wikiRepository.detail).mockRejectedValueOnce(new ApiError(503, 'read_failed', '조회 실패'));
  act(() => hook.result.current.save());
  await waitFor(() => expect(hook.result.current.busy).toBe(false));
  expect(hook.result.current.pending?.receipt?.pageId).toBe('p1');
  hook.unmount();
  const restored = renderHook(() => useWikiController('u1'));
  expect(restored.result.current.pending?.receipt?.pageId).toBe('p1');
  act(() => restored.result.current.resend());
  await waitFor(() => expect(restored.result.current.pending).toBeNull());
  expect(wikiRepository.mutate).toHaveBeenCalledTimes(1);
});
it('recovers stale protection/restore without silently retrying the operation', async () => {
  const hook = renderHook(() => useWikiController('u1'));
  await act(async () => {await hook.result.current.select('p1');});
  vi.mocked(wikiRepository.mutate).mockRejectedValueOnce(new ApiError(409, 'wiki_version_conflict', '변경됨'));
  act(() => hook.result.current.protect());
  await waitFor(() => expect(hook.result.current.conflicted).toBe(true));
  const locked = {...original, version: 2, locked: true, canEdit: false};
  vi.mocked(wikiRepository.detail).mockResolvedValueOnce(locked);
  await act(async () => {await hook.result.current.inspectLatest();});
  act(() => hook.result.current.acceptLatestBase());
  expect(hook.result.current.page).toEqual(locked);
  expect(hook.result.current.conflicted).toBe(false);
  expect(hook.result.current.historical).toBeNull();
  await waitFor(() => expect(wikiRepository.list).toHaveBeenCalledTimes(2));
  expect(wikiRepository.mutate).toHaveBeenCalledTimes(1);
});
it('does not publish an error from an obsolete history request into a different page', async () => {
  let reject!: (reason: unknown) => void;
  vi.mocked(wikiRepository.history).mockImplementationOnce(() => new Promise((_resolve, failure) => {reject = failure;}));
  const hook = renderHook(() => useWikiController('u1'));
  await act(async () => {await hook.result.current.select('p1');});
  act(() => {void hook.result.current.showHistory();});
  vi.mocked(wikiRepository.detail).mockResolvedValueOnce({...original, id: 'p2', title: '다른 문서'});
  await act(async () => {await hook.result.current.select('p2');});
  await act(async () => {reject(new Error('이전 문서 오류'));});
  expect(hook.result.current.page?.id).toBe('p2');
  expect(hook.result.current.error).toBe('');
});
