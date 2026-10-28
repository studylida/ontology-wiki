import { isCitation, type RunEvent } from '../types/contracts';
import { apiUrl, requestHeaders, responseError } from './http';

/** Retained incremental parser: UTF-8 is decoded by the reader; comments and CRLF are supported. */
export class SseParser {
  private buffer = '';
  push(chunk: string): string[] {
    this.buffer += chunk;
    if (this.buffer.length > 2000000) throw new Error('응답 이벤트가 허용 크기를 초과했습니다.');
    const frames: string[] = [];
    let match: RegExpExecArray | null;
    while ((match = /\r?\n\r?\n/.exec(this.buffer))) {
      const block = this.buffer.slice(0, match.index);
      this.buffer = this.buffer.slice(match.index + match[0].length);
      const data = block.split(/\r?\n/).filter(line => line.startsWith('data:'))
        .map(line => line.slice(5).replace(/^ /, '')).join('\n');
      if (data) frames.push(data);
    }
    return frames;
  }
}
const TYPES = new Set(['state', 'citation', 'delta', 'complete', 'error', 'cancelled', 'interrupted', 'stream_error']);
export function parseRunEvent(raw: string): RunEvent {
  const e = JSON.parse(raw) as RunEvent;
  const invalid = () => { throw new Error('응답 이벤트 형식을 확인하지 못했습니다. 저장된 실행을 다시 조회해 주세요.'); };
  if (!e || typeof e.runId !== 'string' || !TYPES.has(e.type) || !e.data || typeof e.data !== 'object') return invalid();
  if (e.type === 'stream_error') {
    if (e.seq !== undefined || typeof e.data.error?.message !== 'string') return invalid();
  } else {
    if (!Number.isSafeInteger(e.seq) || e.seq < 1) return invalid();
    if (e.type === 'delta' && typeof e.data.text !== 'string') return invalid();
    if (e.type === 'citation' && !isCitation(e.data)) return invalid();
    const states: Record<string, string[]> = {state: ['accepted', 'retrieving', 'generating'], complete: ['completed'],
      error: ['failed'], cancelled: ['cancelled'], interrupted: ['interrupted']};
    if (e.type !== 'delta' && e.type !== 'citation' && !states[e.type].includes(e.data.status)) return invalid();
  }
  return e;
}
export async function readRunStream(runId: string, after: number, signal: AbortSignal, onEvent: (event: RunEvent) => void): Promise<void> {
  const headers = requestHeaders(); headers.set('Accept', 'text/event-stream');
  const response = await fetch(apiUrl(`/answer-runs/${encodeURIComponent(runId)}/events?after=${after}`),
    {headers, signal, cache: 'no-store', credentials: 'same-origin'});
  if (!response.ok) throw await responseError(response);
  if (!response.body || !response.headers.get('content-type')?.includes('text/event-stream')) throw new Error('응답 스트림을 받지 못했습니다.');
  const reader = response.body.getReader(), decoder = new TextDecoder(), parser = new SseParser();
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      for (const raw of parser.push(decoder.decode(value, {stream: true}))) onEvent(parseRunEvent(raw));
    }
    for (const raw of parser.push(decoder.decode())) onEvent(parseRunEvent(raw));
  } finally { await reader.cancel().catch(() => undefined); reader.releaseLock(); }
}
