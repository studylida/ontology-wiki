// @vitest-environment jsdom
import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { useWikiSearch } from './useWikiDiscovery';
import { wikiDiscoveryService } from '../services/wikiDiscoveryService';
import { emptyWikiDraft } from '../services/wikiService';
import type { WikiSearchResult } from '../types/wikiDiscovery';
vi.mock('../services/wikiDiscoveryService', () => ({wikiDiscoveryService: {similar: vi.fn(), search: vi.fn()}, isIndexPending: vi.fn()}));
afterEach(() => {cleanup(); vi.clearAllMocks();});
const result: WikiSearchResult = {items: [], warnings: [], semanticStatus: 'unavailable', embeddingProfile: 'fixture', reranking: {status: 'disabled'}};
it('does not call semantic search during typing or reading', async () => {
  const hook = renderHook(() => useWikiSearch());
  act(() => hook.result.current.setQuery('RUL'));
  expect(wikiDiscoveryService.search).not.toHaveBeenCalled();
  vi.mocked(wikiDiscoveryService.search).mockResolvedValue(result);
  await act(() => hook.result.current.run());
  expect(wikiDiscoveryService.search).toHaveBeenCalledTimes(1);
  expect(hook.result.current.result).toEqual(result);
});
it('discards a similarity result after the draft changes and keeps draft editing independent', async () => {
  let resolve!: (value: WikiSearchResult) => void;
  vi.mocked(wikiDiscoveryService.similar).mockImplementation(() => new Promise(r => {resolve = r;}));
  const draft = {...emptyWikiDraft(), title: 'RUL', markdown: '원래 본문'};
  const hook = renderHook(({value}) => useWikiSearch(value), {initialProps: {value: draft}});
  act(() => {void hook.result.current.run();});
  hook.rerender({value: {...draft, markdown: '수정된 본문'}});
  await act(async () => {resolve(result);});
  expect(hook.result.current.result).toBeNull();
  expect(hook.result.current.busy).toBe(false);
});
it('reports a search outage without showing an empty successful result', async () => {
  vi.mocked(wikiDiscoveryService.search).mockRejectedValue(new Error('search unavailable'));
  const hook = renderHook(() => useWikiSearch());
  act(() => hook.result.current.setQuery('RUL'));
  await act(() => hook.result.current.run());
  await waitFor(() => expect(hook.result.current.error).not.toBe(''));
  expect(hook.result.current.result).toBeNull();
});
