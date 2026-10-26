import { useCallback, useEffect, useRef, useState } from "react";
import { documentRepository, ontologyRepository } from "../repositories/api";
import { errorMessage, isAbort } from "../repositories/http";
import type {
  Citation,
  Concept,
  DocumentRevision,
  SourceView,
} from "../types/contracts";

export function useSourceController() {
  const [selection, setSelection] = useState<{
    revisionId: string;
    citation?: Citation;
  } | null>(null);
  const [revision, setRevision] = useState<DocumentRevision | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sequence = useRef(0);
  useEffect(() => {
    const attempt = ++sequence.current;
    if (!selection) {
      setRevision(null);
      return;
    }
    setLoading(true);
    setError(null);
    setRevision(null);
    const controller = new AbortController();
    documentRepository
      .revision(selection.revisionId, controller.signal)
      .then((value) => {
        if (sequence.current === attempt) setRevision(value);
      })
      .catch((error) => {
        if (!isAbort(error) && sequence.current === attempt)
          setError(errorMessage(error));
      })
      .finally(() => {
        if (sequence.current === attempt) setLoading(false);
      });
    return () => controller.abort();
  }, [selection]);
  const open = useCallback(
    (citation: Citation) =>
      setSelection({ revisionId: citation.sourceRevisionId, citation }),
    [],
  );
  const openRevision = useCallback(
    (revisionId: string) => setSelection({ revisionId }),
    [],
  );
  const close = useCallback(() => setSelection(null), []);
  return { selection, revision, loading, error, open, openRevision, close };
}
export function useConceptPicker(open: boolean) {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<Concept[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true);
      setError(null);
      ontologyRepository
        .concepts(query, controller.signal)
        .then((result) => setItems(result.items))
        .catch((error) => {
          if (!isAbort(error)) setError(errorMessage(error));
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 200);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, open]);
  return { query, setQuery, items, loading, error };
}
export function useSourceViewsController(
  initial: SourceView[],
  conceptId?: string,
) {
  const [publisherId, setPublisherId] = useState("");
  const [sourceType, setSourceType] = useState("");
  const [aspect, setAspect] = useState("");
  const [loaded, setLoaded] = useState<SourceView[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const sequence = useRef(0);
  const load = useCallback(async () => {
    if (!conceptId) return;
    const attempt = ++sequence.current;
    setLoading(true);
    setError(null);
    try {
      const result = await ontologyRepository.sourceViews(conceptId, {
        publisherId,
        sourceType,
        aspect,
      });
      if (sequence.current === attempt) setLoaded(result.items);
    } catch (error) {
      if (sequence.current === attempt) setError(errorMessage(error));
    } finally {
      if (sequence.current === attempt) setLoading(false);
    }
  }, [aspect, conceptId, publisherId, sourceType]);
  const changeFilter = useCallback(
    (name: "publisherId" | "sourceType" | "aspect", value: string) => {
      sequence.current++;
      setLoaded(null);
      setLoading(false);
      setSelectedIds([]);
      if (name === "publisherId") setPublisherId(value);
      else if (name === "sourceType") setSourceType(value);
      else setAspect(value);
    },
    [],
  );
  const all = loaded ?? initial;
  const items = all.filter(
    (view) =>
      (!publisherId || view.publisherId === publisherId) &&
      (!sourceType || view.sourceType === sourceType) &&
      (!aspect || view.aspect === aspect),
  );
  const toggleSelection = (id: string) =>
    setSelectedIds((ids) =>
      ids.includes(id) ? ids.filter((value) => value !== id) : [...ids, id],
    );
  return {
    publisherId,
    sourceType,
    aspect,
    items,
    selected: items.filter((item) => selectedIds.includes(item.id)),
    selectedIds,
    loading,
    error,
    loaded: loaded !== null,
    changeFilter,
    toggleSelection,
    load,
  };
}
