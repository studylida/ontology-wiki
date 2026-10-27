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
    expect(screen.getByText(/자료 형태: 편집 요약/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "자료에 연결된 링크 열기" }).getAttribute("href")).toBe("https://example.org/paper");
    expect(screen.getByText(/연결된 링크는 인용 구간의 개별 근거와 다를 수 있습니다/)).toBeTruthy();
    expect(screen.getByText("편집한 본문")).toBeTruthy();
  });

  it("labels edited source material separately from the publisher's original", () => {
    const controller = {
      selection: { revisionId: "r2" }, loading: false, error: null,
      revision: {
        id: "r2", documentId: "d2", title: "편집본", content: "수정한 본문",
        metadata: { sourceType: "manufacturer_glossary", documentForm: "edited_derivative" as const, url: "https://example.org/original" },
        reviewStatus: "approved", indexStatus: "ready", readScope: "full", passages: [],
      },
      open: vi.fn(), openRevision: vi.fn(), close: vi.fn(),
    } satisfies ReturnType<typeof useSourceController>;
    render(<SourcePanel controller={controller} onQuestion={vi.fn()} />);
    expect(screen.getByRole("dialog", { name: "편집본과 근거" })).toBeTruthy();
    expect(screen.getByText(/자료 형태: 편집본/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "자료에 연결된 링크 열기" })).toBeTruthy();
  });

  it("labels legacy extracted text without calling it an original document", () => {
    const controller = {
      selection: { revisionId: "r3" }, loading: false, error: null,
      revision: {
        id: "r3", documentId: "d3", title: "추출본", content: "텍스트",
        metadata: { sourceType: "research_article_text_extraction" },
        reviewStatus: "approved", indexStatus: "ready", readScope: "full", passages: [],
      },
      open: vi.fn(), openRevision: vi.fn(), close: vi.fn(),
    } satisfies ReturnType<typeof useSourceController>;
    render(<SourcePanel controller={controller} onQuestion={vi.fn()} />);
    expect(screen.getByRole("dialog", { name: "원문 텍스트 추출본과 근거" })).toBeTruthy();
  });
});
