// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { api } from './api';
import { authStorage, AUTH_CHANGED, pendingSubmission, savePending, clearWorkspace } from './workspaceStorage';
import { http } from './http';
beforeEach(() => sessionStorage.clear());
afterEach(() => vi.unstubAllGlobals());
it('uploads FormData with authorization but without a forced JSON boundary', async () => {
  authStorage.setToken('test-token');
  const fetcher = vi.fn(async () => new Response(JSON.stringify({documentId: 'd'}), {status: 202})); vi.stubGlobal('fetch', fetcher);
  await api.upload(new File(['source'], 'source.md'), '공용');
  const [url, options] = fetcher.mock.calls[0] as unknown as [string, RequestInit];
  expect(url).toBe('/api/v1/documents'); expect(options.body).toBeInstanceOf(FormData);
  expect((options.headers as Headers).get('Authorization')).toBe('Bearer test-token');
  expect((options.headers as Headers).has('Content-Type')).toBe(false);
});
it('sends only turns and preserves the request identity', async () => {
  const fetcher = vi.fn(async () => new Response('{}', {status: 202})); vi.stubGlobal('fetch', fetcher);
  await api.submit({kind: 'turn', conversationId: 'c', question: '질문', requestId: 'stable'});
  const [url, options] = fetcher.mock.calls[0] as unknown as [string, RequestInit];
  expect(url).toBe('/api/v1/conversations/c/turns'); expect(JSON.parse(options.body as string)).toEqual({question: '질문', requestId: 'stable'});
  expect(fetcher).toHaveBeenCalledTimes(1);
});
it('signals revoked authentication and never renders an error body as HTML', async () => {
  authStorage.setToken('revoked'); const expired = vi.fn(); window.addEventListener(AUTH_CHANGED, expired);
  vi.stubGlobal('fetch', async () => new Response('<html>bad</html>', {status: 401}));
  await expect(http('/auth/me')).rejects.toMatchObject({status: 401, code: 'HTTP_401'});
  expect(expired).toHaveBeenCalledTimes(1); window.removeEventListener(AUTH_CHANGED, expired);
});
it('keeps ambiguous submissions per user and never restores old workspace content', () => {
  sessionStorage.setItem('knowledge-hub.workspace', JSON.stringify({content: 'old answer'}));
  const submission = {kind: 'turn' as const, conversationId: 'c', question: 'q', requestId: 'id'};
  savePending('alice', submission); expect(pendingSubmission('bob')).toBeNull(); expect(pendingSubmission('alice')).toEqual(submission);
  clearWorkspace('alice'); expect(pendingSubmission('alice')).toBeNull();
});
