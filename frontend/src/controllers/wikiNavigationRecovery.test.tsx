// @vitest-environment jsdom
import { act, cleanup, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { useWikiController } from './useWikiController';
import { wikiRepository } from '../repositories/wikiRepository';
import type { WikiDetail } from '../types/wiki';
vi.mock('../repositories/wikiRepository', () => ({guardWikiUnload: () => () => {}, wikiRepository: {
  list: vi.fn(), detail: vi.fn(),
}}));
const original = {id: 'p1', title: '내용', version: 1, revisionNumber: 1, currentRevisionId: 'r1', canEdit: true,
  revision: {id: 'r1', number: 1, title: '내용', markdown: '본문', sourceNote: ''}} as WikiDetail;
beforeEach(() => {
  sessionStorage.clear(); window.history.replaceState(null, '', '/'); vi.clearAllMocks();
  vi.mocked(wikiRepository.list).mockResolvedValue({items: [], total: 0, offset: 0, limit: 30});
});
afterEach(() => {cleanup(); window.history.replaceState(null, '', '/');});
it('a late wiki response does not change another tab URL and restores the permalink only on return', async () => {
  const id = 'wpg_' + 'b'.repeat(32);
  let resolve!: (value: WikiDetail) => void;
  vi.mocked(wikiRepository.detail).mockImplementationOnce(() => new Promise(r => {resolve = r;}));
  const hook = renderHook(({active}) => useWikiController('u1', active), {initialProps: {active: true}});
  act(() => {void hook.result.current.select(id);});
  expect(window.location.pathname).toBe('/wiki/' + id);
  window.history.pushState(null, '', '/');
  hook.rerender({active: false});
  await act(async () => resolve({...original, id}));
  expect(window.location.pathname).toBe('/');
  expect(hook.result.current.page?.id).toBe(id);
  window.history.pushState(null, '', '/wiki');
  hook.rerender({active: true});
  expect(window.location.pathname).toBe('/wiki/' + id);
});
