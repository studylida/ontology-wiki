import { describe, expect, it, vi } from 'vitest';
import { SseParser, parseRunEvent } from '../repositories/stream';
import { applyRunEvent } from './chatState';
import { followRun } from './conversationService';
import { citationIndex, orderedCitations, safeUrl } from './citationService';
import type { Citation, RunDetail, RunEvent } from '../types/contracts';
const c: Citation = {id: 'p1', passageId: 'p1', sourceRevisionId: 'r1', documentId: 'd1', title: '문헌', locator: '2절', excerpt: '조건', number: 7};
const run = (): RunDetail => ({runId: 'r', conversationId: 'c', userMessageId: 'u', messageId: 'm', requestId: 'q',
  status: 'generating', durableSeq: 2, eventsUrl: '', error: null, usage: null, retrieval: null, retrievalRunId: null,
  answer: {id: 'm', role: 'assistant', content: '저장된 ', createdAt: '', status: 'generating', runId: 'r', citations: [], warnings: [], sourceUnavailable: false, historicalSources: false}});
describe('current SSE contract', () => {
  it('keeps split frames, comments, CRLF and multiline data', () => {
    const parser = new SseParser();
    expect(parser.push(': ping\r\n\r\nid: 3\r\ndata: {"runId":"r",\r\n')).toEqual([]);
    const result = parser.push('data: "seq":3,"type":"delta","data":{"text":"한글"}}\r\n\r\n');
    expect(parseRunEvent(result[0]).data).toEqual({text: '한글'});
  });
  it.each([
    {type: 'text.delta', seq: 1, data: {text: 'old'}},
    {type: 'delta', seq: 0, data: {text: 'wrong'}},
    {type: 'complete', seq: 1, data: {status: 'failed'}},
    {type: 'citation', seq: 1, data: {...c, number: 0}},
  ])('rejects invalid and retired events', value => expect(() => parseRunEvent(JSON.stringify({runId: 'r', ...value}))).toThrow());
  it('accepts a transport error without a durable sequence', () => {
    expect(parseRunEvent(JSON.stringify({runId: 'r', type: 'stream_error', data: {error: {code: 'down', message: '끊김'}}})).seq).toBeUndefined();
  });
  it('ignores duplicates but does not ignore sequence gaps or foreign runs', () => {
    const r = run();
    expect(applyRunEvent(r, {runId: 'r', seq: 2, type: 'delta', data: {text: 'duplicate'}})).toBe(r);
    expect(() => applyRunEvent(r, {runId: 'r', seq: 4, type: 'delta', data: {text: 'gap'}})).toThrow();
    expect(() => applyRunEvent(r, {runId: 'other', seq: 3, type: 'delta', data: {text: 'private'}})).toThrow();
  });
  it('preserves partial text and actual failed status', () => {
    const failed = applyRunEvent(run(), {runId: 'r', seq: 3, type: 'error', data: {status: 'failed', error: {code: 'db', message: '저장 실패'}}});
    expect(failed.status).toBe('failed'); expect(failed.answer.content).toBe('저장된 '); expect(failed.error?.code).toBe('db');
  });
});
describe('snapshot and stream recovery', () => {
  it('continues after snapshot cursor without duplicated text or any POST capability', async () => {
    const initial = run(), done = {...run(), status: 'completed' as const};
    done.answer = {...done.answer, content: '저장된 본문', status: 'completed'}; done.durableSeq = 4;
    const get = vi.fn().mockResolvedValueOnce(initial).mockResolvedValueOnce(done);
    const stream = vi.fn(async (_id: string, after: number, _signal: AbortSignal, callback: (e: RunEvent) => void) => {
      expect(after).toBe(2); callback({runId: 'r', seq: 3, type: 'delta', data: {text: '본문'}});
      callback({runId: 'r', seq: 4, type: 'complete', data: {status: 'completed'}});
    });
    const views: RunDetail[] = [];
    await followRun('r', new AbortController().signal, v => views.push(v), vi.fn(), {get, stream});
    expect(views.at(-1)?.answer.content).toBe('저장된 본문'); expect(get).toHaveBeenCalledTimes(2); expect(stream).toHaveBeenCalledTimes(1);
  });
  it('EOF relies on stored failure, not a fabricated complete event', async () => {
    const failed = {...run(), status: 'failed' as const}; failed.answer = {...failed.answer, status: 'failed'};
    const get = vi.fn().mockResolvedValueOnce(run()).mockResolvedValueOnce(failed), views: RunDetail[] = [];
    await followRun('r', new AbortController().signal, v => views.push(v), vi.fn(), {get, stream: vi.fn(async () => {})});
    expect(views.some(v => v.status === 'completed')).toBe(false); expect(views.at(-1)?.status).toBe('failed');
  });
  it('does not replay protected content', async () => {
    const hidden = run(); hidden.answer = {...hidden.answer, content: '', citations: [], sourceUnavailable: true};
    const stream = vi.fn(async () => {}), onView = vi.fn();
    await followRun('r', new AbortController().signal, onView, vi.fn(), {get: async () => hidden, stream});
    expect(stream).not.toHaveBeenCalled(); expect(onView).toHaveBeenCalledWith(hidden);
  });
});
describe('citation identity and safe URLs', () => {
  it('preserves server numbering and rejects fake identities', () => {
    const other = {...c, id: 'p2', passageId: 'p2', number: 2};
    expect(orderedCitations([c, other]).map(v => v.number)).toEqual([2, 7]);
    expect(citationIndex([c, {...c, id: 'fake'}]).size).toBe(1);
  });
  it.each(['javascript:alert(1)', 'data:text/html,hello', '/private', 'citation:unknown'])('blocks unsafe URL %s', value => expect(safeUrl(value)).toBeUndefined());
});
