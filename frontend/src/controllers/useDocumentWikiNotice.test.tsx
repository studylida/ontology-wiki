// @vitest-environment jsdom
import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { useDocumentWikiNotice } from './useDocumentWikiNotice';
import { loadDocumentWikiNotice } from '../services/documentWikiService';
import type { DocumentWikiNotice } from '../types/documentWiki';
vi.mock('../services/documentWikiService', () => ({loadDocumentWikiNotice: vi.fn()}));
afterEach(() => {cleanup(); vi.clearAllMocks(); vi.useRealTimers();});
const value: DocumentWikiNotice = {documentId:'doc', revisionId:'rev', enabled:true, status:'pending', result:{}, error:null, items:[]};
it('reads contextual status without submitting a job and cleans up polling', async () => {
  vi.useFakeTimers(); vi.mocked(loadDocumentWikiNotice).mockResolvedValue(value);
  const hook=renderHook(() => useDocumentWikiNotice('doc','rev'));
  await act(async () => {await Promise.resolve();});
  expect(hook.result.current.value).toEqual(value);
  await act(async () => {vi.advanceTimersByTime(3500);});
  expect(loadDocumentWikiNotice).toHaveBeenCalledTimes(2);
  hook.unmount(); await act(async () => {vi.advanceTimersByTime(7000);});
  expect(loadDocumentWikiNotice).toHaveBeenCalledTimes(2);
});
it('does not replace a new document notice with an obsolete read', async () => {
  let resolve!: (v:DocumentWikiNotice)=>void;
  vi.mocked(loadDocumentWikiNotice).mockImplementationOnce(() => new Promise(r=>{resolve=r;}));
  const hook=renderHook(({id}) => useDocumentWikiNotice(id,'rev'),{initialProps:{id:'first'}});
  vi.mocked(loadDocumentWikiNotice).mockResolvedValue({...value,documentId:'second'});
  hook.rerender({id:'second'}); await waitFor(() => expect(hook.result.current.value?.documentId).toBe('second'));
  await act(async () => {resolve({...value,documentId:'first'});});
  expect(hook.result.current.value?.documentId).toBe('second');
});
it('reports optional failure rather than a false zero-proposal success', async () => {
  vi.mocked(loadDocumentWikiNotice).mockRejectedValue(new Error('optional status failed'));
  const hook=renderHook(() => useDocumentWikiNotice('doc','rev'));
  await waitFor(() => expect(hook.result.current.error).toContain('optional status failed'));
  expect(hook.result.current.value).toBeNull();
});
