// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MessageCard } from "./MessageCard";
import type { Message, Usage } from "../../types/contracts";

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
