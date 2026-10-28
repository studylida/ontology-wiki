import type { RunDetail, RunEvent, RunStatus } from '../types/contracts';
export const isActive = (status?: string) => ['accepted', 'retrieving', 'generating'].includes(status || '');
const LABELS: Record<string, string> = {accepted: '접수됨', retrieving: '근거 검색 중', generating: '답변 작성 중',
  completed: '완료', failed: '실패', cancelled: '취소됨', interrupted: '중단됨'};
export const statusLabel = (status?: string) => LABELS[status || ''] || status || '상태 확인 중';
export function applyRunEvent(run: RunDetail, event: RunEvent): RunDetail {
  if (event.runId !== run.runId) throw new Error('다른 실행의 이벤트입니다.');
  if (event.type === 'stream_error') throw new Error(event.data.error.message);
  if (event.seq <= run.durableSeq) return run;
  if (event.seq !== run.durableSeq + 1) throw new Error('이벤트 순서가 끊겼습니다. 저장된 답변을 다시 조회합니다.');
  const next = {...run, durableSeq: event.seq, answer: {...run.answer}};
  if (event.type === 'delta') next.answer.content += event.data.text;
  else if (event.type === 'citation') next.answer.citations = [...run.answer.citations.filter(c => c.passageId !== event.data.passageId), event.data];
  else {
    next.status = event.data.status as RunStatus;
    next.answer.status = next.status;
    if (event.data.warnings) next.answer.warnings = event.data.warnings;
    if ('error' in event.data) next.error = event.data.error || null;
  }
  return next;
}
