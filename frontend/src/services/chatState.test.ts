import { describe, expect, it } from "vitest";
import { chatReducer, initialChatState, type ChatState } from "./chatState";
import {
  buildAnswerRequest,
  defaultDraft,
  groupsFromViews,
  restoreDraft,
  splitWiki,
} from "./conversationService";
import type { RunEvent, SourceView } from "../types/contracts";

function active() {
  const draft = {
    ...defaultDraft(),
    text: "열압착 본딩 조건은?",
    documentContextIds: ["private-revision"],
    attachmentIds: ["a1"],
  };
  const request = buildAnswerRequest(draft, "c1", undefined, {}, "request-1");
  let state: ChatState = { ...initialChatState(), id: "c1", draft };
  state = chatReducer(state, { type: "begin", request, preserveDraft: false });
  return chatReducer(state, {
    type: "accepted",
    request,
    value: {
      runId: "r1",
      conversationId: "c1",
      messageId: "m1",
      status: "queued",
      eventsUrl: "/answer-runs/r1/events",
    },
  });
}
const event = (
  type: RunEvent["type"],
  seq: number,
  data: Record<string, unknown>,
  runId = "r1",
): RunEvent => ({ type, seq, data, runId, at: "2026-10-26T00:00:00Z" });

describe("persisted answer event ordering", () => {
  it("deduplicates replayed deltas and refuses another conversation run", () => {
    let state = active();
    state = chatReducer(state, {
      type: "event",
      event: event("text.delta", 2, { text: "실제 " }),
    });
    state = chatReducer(state, {
      type: "event",
      event: event("text.delta", 2, { text: "중복" }),
    });
    state = chatReducer(state, {
      type: "event",
      event: event("text.delta", 3, { text: "이전 대화" }, "other-run"),
    });
    expect(state.messages.at(-1)?.content).toBe("실제 ");
    expect(state.run?.lastSeq).toBe(2);
  });
  it("retains partial text and ignores late deltas after cancellation", () => {
    let state = active();
    state = chatReducer(state, {
      type: "event",
      event: event("text.delta", 1, { text: "수신된 문장" }),
    });
    state = chatReducer(state, {
      type: "event",
      event: event("run.cancelled", 2, { status: "cancelled", usage: null }),
    });
    const stopped = state;
    state = chatReducer(state, {
      type: "event",
      event: event("text.delta", 3, { text: "추가 내용" }),
    });
    expect(state).toBe(stopped);
    expect(state.messages.at(-1)?.content).toBe("수신된 문장");
    expect(state.messages.at(-1)?.status).toBe("cancelled");
  });
  it("retains nullable usage, shows a failed terminal as failed, and never invents success", () => {
    let state = active();
    state = chatReducer(state, {
      type: "event",
      event: event("run.failed", 1, {
        error: { message: "공급자 연결 실패" },
        usage: {
          costUsd: null,
          inputTokens: null,
          outputTokens: null,
          totalTokens: null,
          costStatus: "unknown",
        },
      }),
    });
    expect(state.run?.status).toBe("failed");
    expect(state.messages.at(-1)?.usage?.costUsd).toBeNull();
    expect(state.error).toBe("공급자 연결 실패");
  });
  it("marks fixture as soon as run.started arrives, before any body text", () => {
    const state = chatReducer(active(), {
      type: "event",
      event: event("run.started", 1, {
        generationConfig: {
          model: "fixture",
          providerMode: "fixture",
          effort: null,
        },
      }),
    });
    expect(state.run?.generationConfig?.providerMode).toBe("fixture");
    expect(state.messages.at(-1)?.content).toBe("");
  });
});
describe("draft and submitted settings are independent", () => {
  it("changing modes preserves draft, selected documents and attachments", () => {
    const initial = {
      ...initialChatState(),
      draft: {
        ...defaultDraft(),
        text: "보존할 초안",
        documentContextIds: ["d1"],
        attachmentIds: ["a1"],
        extended: true,
      },
    };
    const result = chatReducer(initial, {
      type: "draft",
      values: { responseMode: "analysis" },
    });
    expect(result.draft).toMatchObject({
      text: "보존할 초안",
      responseMode: "analysis",
      extended: true,
      documentContextIds: ["d1"],
      attachmentIds: ["a1"],
    });
    expect(result.messages).toEqual([]);
    expect(result.run).toBeNull();
  });
  it("a follow-up keeps the original composer draft while using a distinct request ID", () => {
    const initial = {
      ...initialChatState(),
      draft: { ...defaultDraft(), text: "아직 작성 중인 초안" },
    };
    const request = buildAnswerRequest(
      initial.draft,
      undefined,
      "관계 후속 질문",
      {},
      "followup-1",
    );
    const result = chatReducer(initial, {
      type: "begin",
      request,
      preserveDraft: true,
    });
    expect(result.draft.text).toBe("아직 작성 중인 초안");
    expect(result.messages[0].content).toBe("관계 후속 질문");
    expect(request.clientRequestId).toBe("followup-1");
  });
  it("browser next-settings override submitted defaults; a new conversation starts wiki/off", () => {
    expect(
      restoreDraft(
        { text: "초안", responseMode: "analysis", extended: true },
        { responseMode: "wiki", extended: false },
      ),
    ).toMatchObject({ text: "초안", responseMode: "analysis", extended: true });
    expect(defaultDraft()).toMatchObject({
      responseMode: "wiki",
      extended: false,
    });
  });
});
describe("rendering and explicit source predicates", () => {
  it("renders a partial provider sentence immediately without waiting for structured JSON", () => {
    expect(splitWiki("## 핵심 설명\n실제로 도착한")).toEqual([
      "실제로 도착한",
      "",
      "",
      "",
      "",
    ]);
    expect(
      splitWiki(
        "## 핵심 설명\n설명\n## 목적·원리\n원리\n## 사례·조건\n조건",
      )[2],
    ).toBe("조건");
  });
  it("does not infer attribution and retains publisher+type as AND predicates within each group", () => {
    const base = {
      conceptId: "c",
      sourceRevisionId: "s",
      publisher: "표시명",
      author: "외부 저자",
      attributionBasis: "author_byline",
      aspect: "조건",
      summary: "요약",
      status: "extracted",
      evidence: [],
    };
    const views: SourceView[] = [
      { ...base, id: "v1", publisherId: "p1", sourceType: "column" },
      { ...base, id: "v2", publisherId: "p2", sourceType: "paper" },
    ];
    expect(groupsFromViews(views)).toEqual([
      { groupId: "p1:column", publisherId: "p1", sourceType: "column" },
      { groupId: "p2:paper", publisherId: "p2", sourceType: "paper" },
    ]);
  });
});
