// @vitest-environment jsdom
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { documentRepository } from "../repositories/api";
import { useReviewController } from "./useReviewController";
import type { DocumentRevision } from "../types/contracts";

vi.mock("../repositories/api", () => ({
  documentRepository: {
    list: vi.fn().mockResolvedValue({ items: [] }),
    jobs: vi.fn().mockResolvedValue({ items: [] }),
    revision: vi.fn(),
    metadata: vi.fn(),
  },
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

it("saves editable attribution without sending immutable URL or visibility", async () => {
  const revision: DocumentRevision = {
    id: "rev-1", documentId: "doc-1", title: "논문 요약", content: "본문",
    metadata: { url: "https://example.org/article", visibility: "shared_candidate", author: "연구자", sourceType: "unknown" },
    reviewStatus: "pending", indexStatus: "pending", passages: [], readScope: "full",
  };
  vi.mocked(documentRepository.revision).mockResolvedValue(revision);
  vi.mocked(documentRepository.metadata).mockResolvedValue({ metadataVersion: 2, changed: true });
  const { result } = renderHook(() => useReviewController(true));
  act(() => result.current.select(revision.id));
  await waitFor(() => expect(result.current.revision?.id).toBe(revision.id));
  act(() => result.current.setMetadata({ ...result.current.metadata, sourceType: "editorial_summary" }));
  await act(async () => { await result.current.saveMetadata(); });
  const [, patch] = vi.mocked(documentRepository.metadata).mock.calls[0];
  expect(patch).toMatchObject({ author: "연구자", sourceType: "editorial_summary" });
  expect(patch).not.toHaveProperty("url");
  expect(patch).not.toHaveProperty("visibility");
  expect(result.current.metadata.url).toBe("https://example.org/article");
});
