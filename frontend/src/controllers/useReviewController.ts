import { useCallback, useEffect, useRef, useState } from "react";
import { documentRepository } from "../repositories/api";
import { errorMessage, isAbort } from "../repositories/http";
import type {
  DocumentMetadata,
  DocumentRevision,
  DocumentSummary,
  Job,
  ReviewStatus,
} from "../types/contracts";

export function useReviewController(active: boolean) {
  const [filter, setFilter] = useState<ReviewStatus>("pending");
  const [items, setItems] = useState<DocumentSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [revision, setRevision] = useState<DocumentRevision | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [metadata, setMetadata] = useState<DocumentMetadata>({});
  const [content, setContent] = useState("");
  const [editingContent, setEditingContent] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const sequence = useRef(0);
  const revisionRef = useRef(revision);
  revisionRef.current = revision;
  const refresh = useCallback(async () => {
    const currentId = revisionRef.current?.id;
    const results = await Promise.allSettled([
      documentRepository.list(filter),
      documentRepository.jobs(),
      currentId
        ? documentRepository.revision(currentId)
        : Promise.resolve(null),
    ]);
    if (results[0].status === "fulfilled") setItems(results[0].value.items);
    else setError(errorMessage(results[0].reason));
    if (results[1].status === "fulfilled") setJobs(results[1].value.items);
    else setError(errorMessage(results[1].reason));
    if (results[2].status === "fulfilled" && results[2].value) {
      const latest = results[2].value;
      // Poll status without discarding an in-progress metadata/content edit.
      setRevision((current) =>
        current?.id === latest.id
          ? {
              ...current,
              reviewStatus: latest.reviewStatus,
              indexStatus: latest.indexStatus,
            }
          : current,
      );
    } else if (results[2].status === "rejected") {
      setError(errorMessage(results[2].reason));
      if ([403, 404].includes(results[2].reason?.status))
        setRevision((current) => (current?.id === currentId ? null : current));
    }
  }, [filter]);
  useEffect(() => {
    if (active) void refresh();
  }, [active, refresh]);
  useEffect(() => {
    if (!active) return;
    const timer = window.setInterval(() => {
      void refresh();
    }, 15000);
    return () => clearInterval(timer);
  }, [active, refresh]);
  useEffect(() => {
    if (!selectedId) return;
    const attempt = ++sequence.current;
    const controller = new AbortController();
    setLoading(true);
    setRevision(null);
    setError(null);
    setReason("");
    setEditingContent(false);
    documentRepository
      .revision(selectedId, controller.signal)
      .then((value) => {
        if (sequence.current === attempt) {
          setRevision(value);
          setMetadata(value.metadata);
          setContent(value.content);
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
  }, [selectedId]);
  const decide = useCallback(
    async (decision: "approve" | "reject" | "hold" | "withdraw") => {
      if (!revision) return;
      if (!reason.trim()) {
        setError("검토 사유를 입력해 주세요.");
        return;
      }
      setBusy(true);
      setError(null);
      try {
        await documentRepository.review(revision.id, decision, reason.trim());
        const latest = await documentRepository.revision(revision.id);
        setRevision(latest);
        setReason("");
        setNotice(
          decision === "approve"
            ? "문헌을 승인했습니다. 검색 반영은 별도 상태로 확인해 주세요."
            : "문헌 검토 결과를 저장했습니다.",
        );
        await refresh();
      } catch (error) {
        setError(errorMessage(error));
      } finally {
        setBusy(false);
      }
    },
    [reason, refresh, revision],
  );
  const saveMetadata = useCallback(async () => {
    if (!revision) return;
    setBusy(true);
    setError(null);
    try {
      const { publisher, publisherId, author, attributedTo, attributionBasis, sourceType, publishedAt } = metadata;
      await documentRepository.metadata(revision.id, {
        publisher, publisherId, author, attributedTo, attributionBasis, sourceType, publishedAt,
      });
      const latest = await documentRepository.revision(revision.id);
      setRevision(latest);
      setMetadata(latest.metadata);
      setNotice(
        "서지·귀속 정보를 저장했습니다. 이전 귀속에서 만든 관점은 갱신 전까지 표시하지 않습니다.",
      );
      void refresh();
    } catch (error) {
      setError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [metadata, refresh, revision]);
  const saveRevision = useCallback(async () => {
    if (!revision || !content.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const result = await documentRepository.newRevision(
        revision.documentId,
        content,
      );
      setSelectedId(result.currentRevisionId);
      setEditingContent(false);
      setNotice(
        "수정 본문을 새 판본으로 저장했습니다. 이전 판본은 유지되며 새 판본은 다시 검토합니다.",
      );
      await refresh();
    } catch (error) {
      setError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [content, refresh, revision]);
  const index = useCallback(async () => {
    if (!revision) return;
    setBusy(true);
    setError(null);
    try {
      await documentRepository.index([revision.id]);
      setNotice(
        "이 문헌의 즉시 검색 반영 작업을 요청했습니다. 완료 상태를 확인해 주세요.",
      );
      await refresh();
    } catch (error) {
      setError(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }, [refresh, revision]);
  const jobAction = useCallback(
    async (id: string, action: "cancel" | "retry") => {
      setBusy(true);
      setError(null);
      try {
        if (action === "cancel") await documentRepository.cancelJob(id);
        else await documentRepository.retryJob(id);
        await refresh();
      } catch (error) {
        setError(errorMessage(error));
      } finally {
        setBusy(false);
      }
    },
    [refresh],
  );
  return {
    filter,
    setFilter,
    items,
    selectedId,
    select: setSelectedId,
    revision,
    loading,
    busy,
    error,
    notice,
    reason,
    setReason,
    metadata,
    setMetadata,
    content,
    setContent,
    editingContent,
    setEditingContent,
    jobs,
    decide,
    saveMetadata,
    saveRevision,
    index,
    jobAction,
    refresh,
  };
}
