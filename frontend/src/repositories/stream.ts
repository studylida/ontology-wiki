import type { RunEvent } from "../types/contracts";
import { apiUrl, requestHeaders, responseError } from "./http";

/** Stateful SSE parser: handles split UTF-8 (in the reader), CRLF, multiline data and comments. */
export class SseParser {
  private buffer = "";
  push(chunk: string): string[] {
    this.buffer += chunk;
    const frames: string[] = [];
    let match: RegExpExecArray | null;
    while ((match = /\r?\n\r?\n/.exec(this.buffer))) {
      const block = this.buffer.slice(0, match.index);
      this.buffer = this.buffer.slice(match.index + match[0].length);
      const data = block
        .split(/\r?\n/)
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).replace(/^ /, ""))
        .join("\n");
      if (data) frames.push(data);
    }
    return frames;
  }
}
const TYPES = new Set([
  "run.started",
  "retrieval.status",
  "text.delta",
  "citation.add",
  "relation.add",
  "source_view.add",
  "run.completed",
  "run.failed",
  "run.cancelled",
]);
export function parseRunEvent(raw: string): RunEvent {
  const event = JSON.parse(raw) as RunEvent;
  if (
    !event ||
    !TYPES.has(event.type) ||
    typeof event.runId !== "string" ||
    !Number.isSafeInteger(event.seq) ||
    event.seq < 1 ||
    !event.data ||
    typeof event.data !== "object"
  ) {
    throw new Error(
      "응답 이벤트 형식을 확인하지 못했습니다. 저장된 실행을 다시 연결해 주세요.",
    );
  }
  return event;
}
export async function readRunStream(
  runId: string,
  after: number,
  signal: AbortSignal,
  onEvent: (event: RunEvent) => void,
): Promise<void> {
  const headers = requestHeaders();
  headers.set("Accept", "text/event-stream");
  const response = await fetch(
    apiUrl(`/answer-runs/${encodeURIComponent(runId)}/events?after=${after}`),
    { headers, signal, cache: "no-store", credentials: "same-origin" },
  );
  if (!response.ok) throw await responseError(response);
  if (
    !response.body ||
    !response.headers.get("content-type")?.includes("text/event-stream")
  )
    throw new Error("서버에서 응답 스트림을 받지 못했습니다.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const parser = new SseParser();
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      for (const raw of parser.push(decoder.decode(value, { stream: true })))
        onEvent(parseRunEvent(raw));
    }
    for (const raw of parser.push(decoder.decode()))
      onEvent(parseRunEvent(raw));
  } finally {
    reader.releaseLock();
  }
}
