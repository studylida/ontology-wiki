import { useCallback, useEffect, useState } from "react";
import { documentRepository } from "../repositories/api";
import { errorMessage, isAbort } from "../repositories/http";
import type { CreateDocument, DocumentSummary } from "../types/contracts";

export function useDocumentPicker(open: boolean) {
  const [items, setItems] = useState<DocumentSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    documentRepository
      .list(undefined, controller.signal)
      .then((result) => setItems(result.items))
      .catch((error) => {
        if (!isAbort(error)) setError(errorMessage(error));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [open]);
  return {
    items: items.filter((item) =>
      item.title.toLocaleLowerCase().includes(query.toLocaleLowerCase()),
    ),
    allItems: items,
    query,
    setQuery,
    error,
    loading,
  };
}
const initialDocument = (): CreateDocument => ({
  title: "",
  content: "",
  format: "markdown",
  visibility: "private",
  attributionBasis: "unknown",
  sourceType: "unknown",
});
export function useDocumentUploadController(
  onCreated: (document: DocumentSummary) => void,
) {
  const [values, setValues] = useState<CreateDocument>(initialDocument);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const patch = useCallback(
    (values: Partial<CreateDocument>) =>
      setValues((current) => ({ ...current, ...values })),
    [],
  );
  const readFile = useCallback(async (file?: File) => {
    if (!file) return;
    if (!/\.(md|markdown|txt)$/i.test(file.name)) {
      setError("텍스트 또는 Markdown 파일을 선택해 주세요.");
      return;
    }
    if (file.size > 2_000_000) {
      setError("텍스트 파일은 2 MB 이하로 선택해 주세요.");
      return;
    }
    try {
      const content = await file.text();
      setValues((current) => ({
        ...current,
        title: current.title || file.name.replace(/\.[^.]+$/, ""),
        content,
        format: /\.txt$/i.test(file.name) ? "text" : "markdown",
      }));
      setError(null);
    } catch {
      setError("파일 내용을 읽지 못했습니다.");
    }
  }, []);
  const submit = useCallback(async () => {
    if (!values.title.trim() || !values.content.trim()) {
      setError("제목과 문헌 본문을 입력해 주세요.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await documentRepository.create({
        ...values,
        title: values.title.trim(),
      });
      onCreated(result);
      setValues(initialDocument());
    } catch (error) {
      setError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [onCreated, values]);
  return { values, patch, busy, error, readFile, submit };
}
