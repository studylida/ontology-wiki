import { useCallback, useRef, useState } from "react";
import { documentRepository } from "../repositories/api";
import { ApiError, errorMessage } from "../repositories/http";

type BatchState = "ready" | "created" | "failed" | "unknown";
export interface BatchDocument {
  file: File;
  title: string;
  url: string;
  publisher: string;
  author: string;
  sourceType: string;
  state: BatchState;
  message?: string;
}

export function useBatchDocumentController(onChanged: () => void) {
  const [items, setItems] = useState<BatchDocument[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [limitedList, setLimitedList] = useState(false);
  const submitting = useRef(false);

  const select = useCallback((files: File[]) => {
    if (files.length > 200) {
      setItems([]);
      setError("한 번에 최대 200개 파일을 선택해 주세요.");
      return;
    }
    setError(null);
    setItems(
      files.map((file) => ({
        file,
        title: file.name.replace(/\.[^.]+$/, ""),
        url: "",
        publisher: "",
        author: "",
        sourceType: "",
        state: "ready",
      })),
    );
  }, []);
  const setTitle = useCallback((index: number, title: string) => {
    setItems((previous) =>
      previous.map((item, i) => (i === index ? { ...item, title } : item)),
    );
    setError(null);
  }, []);
  const setMetadata = useCallback(
    (
      index: number,
      patch: Partial<
        Pick<BatchDocument, "url" | "publisher" | "author" | "sourceType">
      >,
    ) => {
      setItems((previous) =>
        previous.map((item, i) => (i === index ? { ...item, ...patch } : item)),
      );
      setError(null);
    },
    [],
  );
  const submit = useCallback(async () => {
    if (submitting.current) return;
    const eligible = items.filter(
      (item) => item.state === "ready" || item.state === "failed",
    );
    if (!eligible.length) return;
    if (
      eligible.some(
        (item) => !item.title.trim() || item.title.trim().length > 500,
      )
    ) {
      setError("각 자료의 제목을 1~500자로 입력해 주세요.");
      return;
    }
    if (
      eligible.some((item) => {
        const value = item.url.trim();
        if (!value) return false;
        try {
          const url = new URL(value);
          return (
            value.length > 4000 || !["http:", "https:"].includes(url.protocol)
          );
        } catch {
          return true;
        }
      })
    ) {
      setError(
        "원문 URL은 비워 두거나 올바른 http 또는 https 주소로 입력해 주세요.",
      );
      return;
    }
    if (
      eligible.some(
        (item) =>
          item.publisher.trim().length > 500 ||
          item.author.trim().length > 500 ||
          item.sourceType.trim().length > 80,
      )
    ) {
      setError("발행처·저자는 500자, 출처 유형은 80자 이하여야 합니다.");
      return;
    }
    const titles = eligible.map((item) =>
      item.title.trim().toLocaleLowerCase(),
    );
    if (new Set(titles).size !== titles.length) {
      setError("선택한 자료에 같은 제목이 있습니다. 각 제목을 확인해 주세요.");
      return;
    }
    submitting.current = true;
    setBusy(true);
    setError(null);
    try {
      const existing = await documentRepository.list();
      setLimitedList(existing.items.length >= 250);
      if (existing.items.length >= 250) {
        setError(
          "기존 문헌이 250건 이상이라 제목 중복을 전체 확인할 수 없습니다. 개별 등록으로 검토해 주세요.",
        );
        return;
      }
      const existingTitles = new Set(
        existing.items.map((item) => item.title.trim().toLocaleLowerCase()),
      );
      if (titles.some((title) => existingTitles.has(title))) {
        setError(
          "기존 자료와 제목이 같습니다. 검토 목록에서 같은 문헌인지 확인하고 필요한 경우 제목을 수정해 주세요.",
        );
        return;
      }
      let changed = false;
      for (const item of eligible) {
        const update = (state: BatchState, message?: string) =>
          setItems((previous) =>
            previous.map((entry) =>
              entry === item ? { ...entry, state, message } : entry,
            ),
          );
        if (
          !/\.(md|markdown|txt)$/i.test(item.file.name) ||
          item.file.size > 2_000_000
        ) {
          update(
            "failed",
            "2 MB 이하의 Markdown 또는 텍스트 파일을 선택해 주세요.",
          );
          continue;
        }
        let content: string;
        try {
          content = await item.file.text();
          if (!content.trim()) throw new Error("파일이 비어 있습니다.");
        } catch (readError) {
          update("failed", errorMessage(readError));
          continue;
        }
        try {
          await documentRepository.create({
            title: item.title.trim(),
            content,
            format: /\.txt$/i.test(item.file.name) ? "text" : "markdown",
            visibility: "shared_candidate",
            url: item.url.trim() || undefined,
            publisher: item.publisher.trim() || undefined,
            author: item.author.trim() || undefined,
            sourceType: item.sourceType.trim() || "unknown",
            attributionBasis: "unknown",
          });
          changed = true;
          update("created");
        } catch (requestError) {
          // A lost response may follow a successful commit, so it is not safe to retry automatically.
          if (
            !(requestError instanceof ApiError) ||
            requestError.status === 0 ||
            requestError.status >= 500
          ) {
            update(
              "unknown",
              "서버 처리 여부를 확인할 수 없습니다. 검토 목록에서 확인한 뒤 처리해 주세요.",
            );
            break;
          }
          update("failed", errorMessage(requestError));
        }
      }
      if (changed) onChanged();
    } catch (listError) {
      setError(
        `기존 문헌 목록을 확인하지 못했습니다: ${errorMessage(listError)}`,
      );
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }, [items, onChanged]);
  return {
    items,
    select,
    setTitle,
    setMetadata,
    busy,
    error,
    limitedList,
    submit,
  };
}
