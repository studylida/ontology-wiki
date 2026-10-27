// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MessageCard } from "./MessageCard";
import type { Citation, Message, Usage } from "../../types/contracts";

beforeEach(() => {
  vi.stubGlobal(
    "requestAnimationFrame",
    vi.fn(() => 1),
  );
  vi.stubGlobal("cancelAnimationFrame", vi.fn());
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
const usage: Usage = {
  provider: "openai",
  model: "configured-model",
  requestedEffort: "high",
  effectiveEffort: null,
  requestedServiceTier: "default",
  serviceTier: null,
  inputTokens: null,
  outputTokens: null,
  totalTokens: null,
  costUsd: null,
  costStatus: "unknown",
  calls: 1,
  source: "provider",
};
function show(value: Usage) {
  const message: Message = {
    id: "message-1",
    role: "assistant",
    content: "실제 도착한 부분 응답",
    responseMode: "analysis",
    runId: "run-1",
    status: "cancelled",
    createdAt: "2026-10-26T12:00:00Z",
    citations: [],
    relations: [],
    sourceViews: [],
    warnings: [],
    usage: value,
  };
  render(
    <MessageCard
      message={message}
      run={{
        id: "run-1",
        messageId: message.id,
        lastSeq: 10,
        status: "cancelled",
        metrics: {},
        generationConfig: { effort: "high", providerMode: "openai" },
      }}
      onOpen={vi.fn()}
      onRelation={vi.fn()}
      onCompare={vi.fn()}
      onOrganize={vi.fn()}
      onRetry={vi.fn()}
      onFirstVisible={vi.fn()}
    />,
  );
}
const metric = (label: string) =>
  screen.getByText(label).nextElementSibling?.textContent;
describe("provider metrics provenance", () => {
  it("does not infer returned effort, tier or zero cost from a requested configuration", () => {
    show(usage);
    expect(metric("요청 Effort")).toBe("high");
    expect(metric("공급자 반환 Effort")).toBe("공급자 미반환");
    expect(metric("요청 / 반환 서비스 등급")).toBe("default / 공급자 미반환");
    expect(metric("확인 가능한 비용")).toBe("미확인");
  });
  it("shows returned provider values separately when they differ from the request", () => {
    show({ ...usage, effectiveEffort: "medium", serviceTier: "priority" });
    expect(metric("요청 Effort")).toBe("high");
    expect(metric("공급자 반환 Effort")).toBe("medium");
    expect(metric("요청 / 반환 서비스 등급")).toBe("default / priority");
  });
  it("does not present the mixed embedding/generation aggregate as the answer model", () => {
    show({
      ...usage,
      model: "multiple",
      components: [
        {
          operation: "query_embedding",
          provider: "openai",
          model: "embedding-model",
          inputTokens: 100,
          outputTokens: null,
        },
        {
          operation: "answer_generation",
          provider: "openai",
          requestedModel: "requested-text-model",
          model: "returned-text-model",
          modelSource: "provider",
          inputTokens: 900,
          outputTokens: 200,
        },
      ],
    });
    expect(metric("요청 생성 모델")).toBe("requested-text-model");
    expect(metric("공급자 반환 모델")).toBe("returned-text-model");
    expect(screen.getByText("embedding-model")).toBeTruthy();
    expect(screen.getByText(/입력 900 \/ 출력 200 토큰/)).toBeTruthy();
    expect(screen.getByText(/입력 100 토큰/)).toBeTruthy();
    expect(screen.queryByText("multiple")).toBeNull();
  });
});

describe("answer citation grouping", () => {
  const citations: Citation[] = ["C1", "C2", "C3"].map((id, index) => ({
    id, sourceRevisionId: `r${index}`, passageId: `p${index}`, title: `자료 ${id}`,
    locator: `구간 ${id}`, excerpt: `근거 ${id}`,
    ...(id === "C3" ? { contextOrigin: "earlier_answer" } : {}),
  }));
  const message: Message = {
    id: "m-citations", role: "assistant", responseMode: "analysis", status: "completed",
    content: "실제 인용 [출처: C2]\n\n`[C1]`\n\n[C1](https://example.org)\n\n```text\n[C3]\n```",
    createdAt: "2026-10-26T12:00:00Z", citations, relations: [], sourceViews: [], warnings: [],
  };
  it.each(["analysis", "wiki"] as const)("prioritizes actual %s citations, retaining numbered uncited and prior sources", (responseMode) => {
    const onOpen = vi.fn();
    render(<MessageCard message={{ ...message, responseMode }} onOpen={onOpen} onRelation={vi.fn()} onCompare={vi.fn()} onOrganize={vi.fn()} onRetry={vi.fn()} onFirstVisible={vi.fn()} />);
    expect(screen.getByText("답변에 인용한 자료")).toBeTruthy();
    expect(screen.getByText("자료 C2").closest("details")?.open).toBe(false);
    fireEvent.click(screen.getByText("자료 C2"));
    expect(screen.getByRole("button", { name: /출처 2: 자료 C2 · 구간 C2/ })).toBeTruthy();
    const more = screen.getByText("본문에 인용되지 않은 다른 근거 · 2개 구간");
    expect(more.closest("details")?.open).toBe(false);
    fireEvent.click(more);
    const other = more.closest("details")!;
    expect(within(other).getByText("자료 C1").closest("details")?.open).toBe(false);
    fireEvent.click(within(other).getByText("자료 C1"));
    expect(within(other).getByRole("button", { name: /출처 1: 자료 C1 · 구간 C1/ })).toBeTruthy();
    expect(within(other).getByText("자료 C3").closest("details")?.open).toBe(false);
    fireEvent.click(within(other).getByText("자료 C3"));
    const prior = within(other).getByRole("button", { name: /출처 3: 자료 C3 · 구간 C3/ });
    expect(prior.textContent).toContain("이전 답변의 출처");
    fireEvent.click(prior);
    expect(onOpen).toHaveBeenCalledWith(citations[2]);
  });
  it("does not hide potential sources while the answer streams", () => {
    render(<MessageCard message={{ ...message, status: "running" }} onOpen={vi.fn()} onRelation={vi.fn()} onCompare={vi.fn()} onOrganize={vi.fn()} onRetry={vi.fn()} onFirstVisible={vi.fn()} />);
    expect(screen.queryByText("답변에 인용한 자료")).toBeNull();
    expect(screen.getByText("자료 C1").closest("details")?.open).toBe(false);
    fireEvent.click(screen.getByText("자료 C1"));
    expect(screen.getByRole("button", { name: /출처 1: 자료 C1 · 구간 C1/ })).toBeTruthy();
    expect(screen.getByText("자료 C3").closest("details")?.open).toBe(false);
    fireEvent.click(screen.getByText("자료 C3"));
    expect(screen.getByRole("button", { name: /출처 3: 자료 C3 · 구간 C3/ })).toBeTruthy();
  });
});
