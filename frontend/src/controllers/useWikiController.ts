import { useCallback, useEffect, useRef, useState } from "react";
import { wikiRepository } from "../repositories/api";
import { ApiError, errorMessage, isAbort } from "../repositories/http";
import type {
  Job,
  WikiDeleted,
  WikiPage,
  WikiPageSummary,
} from "../types/contracts";

export function useWikiController(active: boolean, selectedId?: string) {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<WikiPageSummary[]>([]);
  const [page, setPage] = useState<WikiPage | null>(null);
  const [loading, setLoading] = useState(false);
  const [listLoading, setListLoading] = useState(active);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [lastDeleted, setLastDeleted] = useState<WikiDeleted | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [conflictPage, setConflictPage] = useState<WikiPage | null>(null);
  const sequence = useRef(0);
  const refresh = useCallback(async () => {
    setListLoading(true);
    try {
      const result = await wikiRepository.list(query);
      setItems(result.items);
    } catch (error) {
      setError(errorMessage(error));
    } finally {
      setListLoading(false);
    }
  }, [query]);
  useEffect(() => {
    if (!active) return;
    setListLoading(true);
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      wikiRepository
        .list(query, controller.signal)
        .then((result) => setItems(result.items))
        .catch((error) => {
          if (!isAbort(error)) setError(errorMessage(error));
        })
        .finally(() => {
          if (!controller.signal.aborted) setListLoading(false);
        });
    }, 200);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [active, query]);
  useEffect(() => {
    if (!active) return;
    const controller = new AbortController();
    const loadJobs = () =>
      wikiRepository
        .jobs(controller.signal)
        .then((result) => setJobs(result.items))
        .catch((error) => {
          if (!isAbort(error)) setError(errorMessage(error));
        });
    void loadJobs();
    const timer = window.setInterval(() => {
      void loadJobs();
    }, 15000);
    return () => {
      controller.abort();
      clearInterval(timer);
    };
  }, [active]);
  useEffect(() => {
    if (
      !active ||
      !selectedId ||
      page?.id === selectedId ||
      lastDeleted?.id === selectedId
    )
      return;
    const attempt = ++sequence.current;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setEditing(false);
    setConflictPage(null);
    setPage(null);
    wikiRepository
      .get(selectedId, controller.signal)
      .then((result) => {
        if (sequence.current === attempt) {
          setPage(result);
          setTitle(result.title);
          setContent(result.content);
        }
      })
      .catch((error) => {
        if (!isAbort(error) && sequence.current === attempt)
          setError(errorMessage(error));
      })
      .finally(() => {
        if (sequence.current === attempt) setLoading(false);
      });
    return () => controller.abort();
  }, [active, selectedId, page?.id, lastDeleted?.id]);
  const save = useCallback(async () => {
    if (!page || page.restricted || conflictPage) return;
    setBusy(true);
    setError(null);
    try {
      const result = await wikiRepository.update(
        page.id,
        title.trim(),
        content,
        page.version,
      );
      setPage(result);
      setTitle(result.title);
      setContent(result.content);
      setEditing(false);
      setNotice("개인 위키 변경을 저장했습니다.");
      void refresh();
    } catch (error) {
      setError(errorMessage(error));
      if (error instanceof ApiError && error.status === 409) {
        try {
          const latest = await wikiRepository.get(page.id);
          if (latest.restricted) {
            setPage(latest);
            setTitle("");
            setContent("");
            setEditing(false);
          } else setConflictPage(latest);
        } catch (refreshError) {
          setError(errorMessage(refreshError));
        }
      }
    } finally {
      setBusy(false);
    }
  }, [conflictPage, content, page, refresh, title]);
  const undo = useCallback(async () => {
    if (!page) return;
    setBusy(true);
    setError(null);
    try {
      const result = await wikiRepository.undo(page.id, page.version);
      if ("deleted" in result) {
        setPage(null);
        setLastDeleted(result);
        setNotice(
          "첫 정리를 되돌렸습니다. 이 원메시지로 자동 재생성하지 않습니다.",
        );
      } else {
        setPage(result);
        setTitle(result.title);
        setContent(result.content);
        setNotice(
          "이전 판본으로 되돌렸습니다. 자동 정리로 다시 덮어쓰지 않습니다.",
        );
      }
      setEditing(false);
      void refresh();
    } catch (error) {
      setError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [page, refresh]);
  const remove = useCallback(async (): Promise<boolean> => {
    if (!page) return false;
    setBusy(true);
    setError(null);
    try {
      const result = await wikiRepository.remove(page.id);
      setLastDeleted(result);
      setPage(null);
      setEditing(false);
      setNotice(
        "개인 위키를 삭제했습니다. 이 원메시지로 자동 재생성하지 않습니다.",
      );
      await refresh();
      return true;
    } catch (error) {
      setError(errorMessage(error));
      return false;
    } finally {
      setBusy(false);
    }
  }, [page, refresh]);
  const restoreDeleted = useCallback(async (): Promise<string | null> => {
    if (!lastDeleted) return null;
    setBusy(true);
    setError(null);
    try {
      const result = await wikiRepository.undo(
        lastDeleted.id,
        lastDeleted.version,
      );
      if ("deleted" in result) {
        setLastDeleted(result);
        return null;
      }
      setPage(result);
      setTitle(result.title);
      setContent(result.content);
      setLastDeleted(null);
      setNotice("삭제한 개인 위키를 복원했습니다.");
      await refresh();
      return result.id;
    } catch (error) {
      setError(errorMessage(error));
      return null;
    } finally {
      setBusy(false);
    }
  }, [lastDeleted, refresh]);
  const startEdit = useCallback(() => {
    if (page && !page.restricted) {
      setTitle(page.title);
      setContent(page.content);
      setConflictPage(null);
      setEditing(true);
    }
  }, [page]);
  const adoptConflictBase = useCallback(() => {
    if (!conflictPage) return;
    setPage(conflictPage);
    setConflictPage(null);
    setError(null);
    setNotice(
      "최신 판본을 저장 기준으로 선택했습니다. 작성 중인 내용은 그대로 유지됩니다. 최신 변경을 반영한 뒤 저장해 주세요.",
    );
  }, [conflictPage]);
  return {
    query,
    setQuery,
    items,
    page,
    jobs,
    loading,
    listLoading,
    busy,
    error,
    notice,
    editing,
    title,
    content,
    conflictPage,
    adoptConflictBase,
    lastDeleted,
    restoreDeleted,
    setTitle,
    setContent,
    startEdit,
    cancelEdit: () => {
      if (conflictPage) setPage(conflictPage);
      setConflictPage(null);
      setEditing(false);
    },
    save,
    undo,
    remove,
    refresh,
  };
}
