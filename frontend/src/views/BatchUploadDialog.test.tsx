// @vitest-environment jsdom
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  renderHook,
  screen,
  waitFor,
} from "@testing-library/react";
import { documentRepository } from "../repositories/api";
import { ApiError } from "../repositories/http";
import { useBatchDocumentController } from "../controllers/useBatchDocumentController";
import type { useReviewController } from "../controllers/useReviewController";
import { BatchUploadDialog, canBatchDocumentUpload } from "./BatchUploadDialog";
import { ReviewView } from "./ReviewView";

beforeAll(() => {
  HTMLDialogElement.prototype.showModal = function () {
    this.open = true;
  };
  HTMLDialogElement.prototype.close = function () {
    this.open = false;
  };
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function file(name: string, body: string) {
  const result = new File([body], name, { type: "text/markdown" });
  Object.defineProperty(result, "text", { value: async () => body });
  return result;
}

describe("batch document registration", () => {
  it("requires both review and write permissions", () => {
    expect(
      canBatchDocumentUpload(["documents:review", "documents:write"]),
    ).toBe(true);
    expect(canBatchDocumentUpload(["documents:review"])).toBe(false);
    expect(canBatchDocumentUpload(["documents:write"])).toBe(false);
    expect(canBatchDocumentUpload(undefined)).toBe(false);
  });
  it("hides the batch entry for an account with review but no write access", () => {
    const review = {
      items: [],
      jobs: [],
      filter: "pending",
      revision: null,
      loading: false,
    } as unknown as ReturnType<typeof useReviewController>;
    const action = vi.fn();
    const { rerender } = render(
      <ReviewView
        controller={review}
        onQuestion={vi.fn()}
        onUpload={vi.fn()}
        canIndex={false}
        onBatchUpload={
          canBatchDocumentUpload(["documents:review"]) ? action : undefined
        }
      />,
    );
    expect(screen.queryByRole("button", { name: "여러 문헌 등록" })).toBeNull();
    rerender(
      <ReviewView
        controller={review}
        onQuestion={vi.fn()}
        onUpload={vi.fn()}
        canIndex={false}
        onBatchUpload={
          canBatchDocumentUpload(["documents:review", "documents:write"])
            ? action
            : undefined
        }
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "여러 문헌 등록" }));
    expect(action).toHaveBeenCalledTimes(1);
  });
  it("keeps front matter and retries only rejected files after partial success", async () => {
    vi.spyOn(documentRepository, "list").mockResolvedValue({ items: [] });
    const create = vi
      .spyOn(documentRepository, "create")
      .mockResolvedValueOnce({} as never)
      .mockRejectedValueOnce(new ApiError(422, "invalid", "확인 필요"))
      .mockResolvedValueOnce({} as never);
    const changed = vi.fn();
    render(<BatchUploadDialog onClose={vi.fn()} onChanged={changed} />);
    const original = "---\ndocument_form: editorial_summary\n---\n# 내용";
    fireEvent.change(screen.getByLabelText(/Markdown 또는 텍스트 파일 선택/), {
      target: {
        files: [file("first.md", original), file("second.txt", "본문")],
      },
    });
    fireEvent.change(screen.getByLabelText("first.md 제목"), {
      target: { value: "첫 제목" },
    });
    fireEvent.click(screen.getByText("first.md 출처 정보"));
    fireEvent.change(screen.getByLabelText("first.md 원문 URL"), {
      target: { value: "https://example.org/paper" },
    });
    fireEvent.change(screen.getByLabelText("first.md 발행처"), {
      target: { value: "발행처 A" },
    });
    fireEvent.change(screen.getByLabelText("first.md 저자"), {
      target: { value: "저자 A" },
    });
    fireEvent.change(screen.getByLabelText("first.md 출처 유형"), {
      target: { value: "editorial_summary" },
    });
    fireEvent.click(screen.getByRole("button", { name: "검토 대기로 등록" }));
    await screen.findByText(/등록하지 못함 · 확인 필요/);
    expect(create).toHaveBeenCalledTimes(2);
    expect(create.mock.calls[0][0]).toMatchObject({
      title: "첫 제목",
      content: original,
      visibility: "shared_candidate",
      url: "https://example.org/paper",
      publisher: "발행처 A",
      author: "저자 A",
      sourceType: "editorial_summary",
    });
    expect(create.mock.calls[1][0]).toMatchObject({
      title: "second",
      format: "text",
    });
    fireEvent.click(screen.getByRole("button", { name: "검토 대기로 등록" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(3));
    expect(create.mock.calls[2][0].title).toBe("second");
    expect(changed).toHaveBeenCalledTimes(2);
  });

  it("does not resend a request whose outcome is unknown", async () => {
    vi.spyOn(documentRepository, "list").mockResolvedValue({ items: [] });
    const create = vi
      .spyOn(documentRepository, "create")
      .mockRejectedValueOnce(new ApiError(0, "network", "연결 실패"))
      .mockResolvedValueOnce({} as never);
    render(<BatchUploadDialog onClose={vi.fn()} onChanged={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/Markdown 또는 텍스트 파일 선택/), {
      target: {
        files: [file("uncertain.md", "본문"), file("next.md", "본문")],
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "검토 대기로 등록" }));
    await screen.findByText(/서버 처리 여부를 확인할 수 없습니다/);
    expect(create).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "검토 대기로 등록" }));
    await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
    expect(create.mock.calls[1][0].title).toBe("next");
  });

  it("stops before creating a title already present in the review list", async () => {
    vi.spyOn(documentRepository, "list").mockResolvedValue({
      items: [{ title: "same" } as never],
    });
    const create = vi.spyOn(documentRepository, "create");
    render(<BatchUploadDialog onClose={vi.fn()} onChanged={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/Markdown 또는 텍스트 파일 선택/), {
      target: { files: [file("same.md", "본문")] },
    });
    fireEvent.click(screen.getByRole("button", { name: "검토 대기로 등록" }));
    await screen.findByText(/기존 자료와 제목이 같습니다/);
    expect(create).not.toHaveBeenCalled();
  });

  it("does not claim to have checked every title when the list is capped", async () => {
    vi.spyOn(documentRepository, "list").mockResolvedValue({
      items: Array.from(
        { length: 250 },
        (_, i) => ({ title: `existing ${i}` }) as never,
      ),
    });
    const create = vi.spyOn(documentRepository, "create");
    render(<BatchUploadDialog onClose={vi.fn()} onChanged={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/Markdown 또는 텍스트 파일 선택/), {
      target: { files: [file("new.md", "본문")] },
    });
    fireEvent.click(screen.getByRole("button", { name: "검토 대기로 등록" }));
    await screen.findByText(
      /250건 이상이라 제목 중복을 전체 확인할 수 없습니다/,
    );
    expect(create).not.toHaveBeenCalled();
  });

  it("blocks duplicate titles within the selected files", async () => {
    const list = vi.spyOn(documentRepository, "list");
    const create = vi.spyOn(documentRepository, "create");
    render(<BatchUploadDialog onClose={vi.fn()} onChanged={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/Markdown 또는 텍스트 파일 선택/), {
      target: {
        files: [file("same.md", "첫 본문"), file("same.txt", "둘째 본문")],
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "검토 대기로 등록" }));
    expect(screen.getByText(/선택한 자료에 같은 제목이 있습니다/)).toBeTruthy();
    expect(list).not.toHaveBeenCalled();
    expect(create).not.toHaveBeenCalled();
  });

  it("rejects non-http URLs before creating any document", () => {
    const list = vi.spyOn(documentRepository, "list");
    const create = vi.spyOn(documentRepository, "create");
    render(<BatchUploadDialog onClose={vi.fn()} onChanged={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/Markdown 또는 텍스트 파일 선택/), {
      target: { files: [file("unsafe.md", "본문")] },
    });
    fireEvent.click(screen.getByText("unsafe.md 출처 정보"));
    fireEvent.change(screen.getByLabelText("unsafe.md 원문 URL"), {
      target: { value: "javascript:alert(1)" },
    });
    fireEvent.click(screen.getByRole("button", { name: "검토 대기로 등록" }));
    expect(screen.getByText(/올바른 http 또는 https 주소/)).toBeTruthy();
    expect(list).not.toHaveBeenCalled();
    expect(create).not.toHaveBeenCalled();
  });

  it("does not start another batch while a prior submission is pending", async () => {
    let resolveList!: (value: { items: [] }) => void;
    const list = vi.spyOn(documentRepository, "list").mockReturnValue(
      new Promise((resolve) => {
        resolveList = resolve;
      }),
    );
    const create = vi
      .spyOn(documentRepository, "create")
      .mockResolvedValue({} as never);
    const { result } = renderHook(() => useBatchDocumentController(vi.fn()));
    act(() => result.current.select([file("only.md", "본문")]));
    act(() => {
      void result.current.submit();
      void result.current.submit();
    });
    expect(list).toHaveBeenCalledTimes(1);
    resolveList({ items: [] });
    await waitFor(() => expect(create).toHaveBeenCalledTimes(1));
  });
});
