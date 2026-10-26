// @vitest-environment jsdom
import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import { wikiRepository } from "../repositories/api";
import { ApiError } from "../repositories/http";
import { useWikiController } from "./useWikiController";
import type { WikiPage } from "../types/contracts";

vi.mock("../repositories/api", () => ({
  wikiRepository: {
    list: vi.fn().mockResolvedValue({ items: [] }),
    jobs: vi.fn().mockResolvedValue({ items: [] }),
    get: vi.fn(),
    update: vi.fn(),
  },
}));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
const page: WikiPage = {
  id: "wiki-1",
  title: "원래 제목",
  summary: "요약",
  content: "원래 내용",
  version: 1,
  updatedAt: "2026-10-26T12:00:00Z",
  versions: [],
  originMessages: [],
  citations: [],
};

describe("personal wiki conflict recovery", () => {
  it("keeps list loading separate when the selected page arrives before its debounced list", async () => {
    let resolveList!: (value: { items: WikiPage[] }) => void;
    vi.mocked(wikiRepository.get).mockResolvedValueOnce(page);
    vi.mocked(wikiRepository.list).mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveList = resolve;
        }),
    );
    const { result } = renderHook(() => useWikiController(true, page.id));
    await waitFor(() => expect(result.current.page?.id).toBe(page.id));
    expect(result.current.listLoading).toBe(true);
    expect(result.current.items).toEqual([]);
    await waitFor(() => expect(resolveList).toBeDefined());
    await act(async () => {
      resolveList({ items: [page] });
    });
    expect(result.current.listLoading).toBe(false);
    expect(result.current.items[0].id).toBe(page.id);
  });
  it("keeps the edit through a 409 and requires an explicit latest-version choice before saving", async () => {
    const latest = { ...page, version: 2, content: "다른 기기의 수정" };
    vi.mocked(wikiRepository.get)
      .mockResolvedValueOnce(page)
      .mockResolvedValueOnce(latest);
    vi.mocked(wikiRepository.update)
      .mockRejectedValueOnce(
        new ApiError(
          409,
          "WIKI_VERSION_CONFLICT",
          "다른 변경이 저장되었습니다.",
        ),
      )
      .mockResolvedValueOnce({
        ...latest,
        version: 3,
        content: "작성 중인 설명",
      });
    const { result } = renderHook(() => useWikiController(true, page.id));
    await waitFor(() => expect(result.current.page?.id).toBe(page.id));
    act(() => result.current.startEdit());
    act(() => result.current.setContent("작성 중인 설명"));
    await act(async () => {
      await result.current.save();
    });
    expect(result.current.content).toBe("작성 중인 설명");
    expect(result.current.conflictPage?.content).toBe("다른 기기의 수정");
    expect(result.current.page?.version).toBe(1);
    await act(async () => {
      await result.current.save();
    });
    expect(wikiRepository.update).toHaveBeenCalledTimes(1);
    act(() => result.current.adoptConflictBase());
    expect(result.current.content).toBe("작성 중인 설명");
    await act(async () => {
      await result.current.save();
    });
    expect(wikiRepository.update).toHaveBeenLastCalledWith(
      page.id,
      page.title,
      "작성 중인 설명",
      2,
    );
    expect(result.current.page?.version).toBe(3);
  });
});
