import type { RunDetail, RunEvent } from '../types/contracts';
import { api } from '../repositories/api';
import { ApiError } from '../repositories/http';
import { readRunStream } from '../repositories/stream';
import { applyRunEvent, isActive } from './chatState';
export type Connection = 'connecting' | 'live' | 'reconnecting' | 'disconnected' | 'idle';
export function pause(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) { reject(new DOMException('Aborted', 'AbortError')); return; }
    const abort = () => { clearTimeout(timer); reject(new DOMException('Aborted', 'AbortError')); };
    const timer = setTimeout(() => { signal.removeEventListener('abort', abort); resolve(); }, ms);
    signal.addEventListener('abort', abort, {once: true});
  });
}
interface RunPort {
  get: (id: string, signal?: AbortSignal) => Promise<RunDetail>;
  stream: (id: string, after: number, signal: AbortSignal, onEvent: (event: RunEvent) => void) => Promise<void>;
}
/** Recovery uses GET only. A snapshot replaces both body and cursor atomically. */
export async function followRun(runId: string, signal: AbortSignal, onView: (run: RunDetail) => void,
  onConnection: (value: Connection) => void, port: RunPort = {get: api.run, stream: readRunStream}) {
  let failure: unknown;
  for (let attempt = 0; attempt < 4 && !signal.aborted; attempt++) {
    onConnection(attempt ? 'reconnecting' : 'connecting');
    try {
      let view = await port.get(runId, signal);
      if (signal.aborted) return;
      onView(view);
      if (!isActive(view.status) || view.answer.sourceUnavailable) { onConnection('idle'); return; }
      onConnection('live');
      await port.stream(runId, view.durableSeq, signal, event => {
        if (signal.aborted) return;
        view = applyRunEvent(view, event); onView(view);
      });
      if (signal.aborted) return;
      // EOF is not success. Reload persisted status; never start another generation.
      view = await port.get(runId, signal);
      if (signal.aborted) return;
      onView(view);
      if (!isActive(view.status) || view.answer.sourceUnavailable) { onConnection('idle'); return; }
      failure = new Error('완료 전에 연결이 끝났습니다. 저장된 실행을 다시 연결해 주세요.');
    } catch (error) {
      if (signal.aborted) return;
      failure = error;
      if (error instanceof ApiError && [401, 403, 404].includes(error.status)) break;
    }
    if (attempt < 3) await pause([500, 1500, 3000][attempt], signal);
  }
  if (!signal.aborted) { onConnection('disconnected'); throw failure || new Error('연결 상태를 확인해 주세요.'); }
}
