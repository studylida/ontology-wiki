import { useCallback, useRef, useState } from "react";
import { researchService } from "../services/researchService";
import { errorMessage } from "../repositories/http";
import type { ResearchCard, TransferResult } from "../types/contracts";

export function useResearchController(
  onTransfer: (result: TransferResult & { conversationId: string }) => void,
) {
  const [query, setQuery] = useState("");
  const [conditions, setConditions] = useState("");
  const [items, setItems] = useState<ResearchCard[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [fetchingIds, setFetchingIds] = useState<string[]>([]);
  const [transferring, setTransferring] = useState(false);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [originId, setOriginId] = useState<string | undefined>();
  const [searchedQuery, setSearchedQuery] = useState("");
  const sequence = useRef(0);
  const fetching = useRef(new Set<string>());
  const begin = useCallback(
    (conversationId?: string, question?: string) => {
      if (originId !== conversationId) {
        sequence.current++;
        setItems([]);
        setSelectedIds([]);
        setSearchedQuery("");
        setQuery(question || "");
        setConditions("");
        setWarnings([]);
        setError(null);
        setBusy(false);
      } else if (question && !items.length && !query) setQuery(question);
      setOriginId(conversationId);
    },
    [items.length, originId, query],
  );
  const search = useCallback(async () => {
    const attempt = ++sequence.current;
    setBusy(true);
    setError(null);
    try {
      const result = await researchService.search(query, originId);
      if (attempt !== sequence.current) return;
      setItems(result.items);
      setSelectedIds([]);
      setWarnings(result.warnings || []);
      setSearchedQuery(query.trim());
    } catch (error) {
      if (attempt === sequence.current) setError(errorMessage(error));
    } finally {
      if (attempt === sequence.current) setBusy(false);
    }
  }, [originId, query]);
  const fetchContent = useCallback(
    async (card: ResearchCard) => {
      if (fetching.current.has(card.id)) return;
      fetching.current.add(card.id);
      setFetchingIds([...fetching.current]);
      setError(null);
      const attempt = sequence.current;
      try {
        const result = await researchService.fetch(
          card,
          searchedQuery || query,
          originId,
        );
        if (attempt !== sequence.current) return;
        setItems((items) =>
          items.map((value) => (value.id === card.id ? result : value)),
        );
        setSelectedIds((ids) =>
          ids.map((id) => (id === card.id ? result.id : id)),
        );
      } catch (error) {
        if (attempt === sequence.current) setError(errorMessage(error));
      } finally {
        fetching.current.delete(card.id);
        setFetchingIds([...fetching.current]);
      }
    },
    [originId, query, searchedQuery],
  );
  const toggleSelection = useCallback(
    (id: string) =>
      setSelectedIds((ids) =>
        ids.includes(id) ? ids.filter((value) => value !== id) : [...ids, id],
      ),
    [],
  );
  const transfer = useCallback(async () => {
    setTransferring(true);
    setError(null);
    try {
      const result = await researchService.transfer(
        items.filter((item) => selectedIds.includes(item.id)),
        searchedQuery || query,
        conditions,
        originId,
      );
      setOriginId(result.conversationId);
      setWarnings(result.warnings || []);
      onTransfer(result);
    } catch (error) {
      setError(errorMessage(error));
    } finally {
      setTransferring(false);
    }
  }, [
    conditions,
    items,
    onTransfer,
    originId,
    query,
    searchedQuery,
    selectedIds,
  ]);
  return {
    query,
    conditions,
    items,
    selectedIds,
    busy,
    fetchingIds,
    transferring,
    warnings,
    error,
    originId,
    searchedQuery,
    setQuery,
    setConditions,
    begin,
    search,
    fetchContent,
    toggleSelection,
    transfer,
  };
}
