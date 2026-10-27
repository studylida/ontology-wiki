// @vitest-environment jsdom
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { SourcePanel } from "./SourcePanel";
import type { useSourceController } from "../controllers/useSourceController";

beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function () { this.open = true; };
  HTMLDialogElement.prototype.close = function () { this.open = false; };
});
afterEach(cleanup);

describe("source provenance", () => {
  it("distinguishes the stored editorial summary from the linked original", () => {
    const controller = {
      selection: { revisionId: "r1" }, loading: false, error: null,
      revision: {
        id: "r1", documentId: "d1", title: "시험 요약", content: "편집한 본문",
        metadata: { sourceType: "editorial_summary", url: "https://example.org/paper" },
        reviewStatus: "approved", indexStatus: "ready", readScope: "full", passages: [],
      },
      open: vi.fn(), openRevision: vi.fn(), close: vi.fn(),
    } satisfies ReturnType<typeof useSourceController>;
    render(<SourcePanel controller={controller} onQuestion={vi.fn()} />);
    expect(screen.getByRole("dialog", { name: "편집 요약과 근거" })).toBeTruthy();
    expect(screen.getByText(/저장된 자료는 편집 요약입니다/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "연결된 원문 링크 열기" }).getAttribute("href")).toBe("https://example.org/paper");
    expect(screen.getByText("편집한 본문")).toBeTruthy();
  });
});
