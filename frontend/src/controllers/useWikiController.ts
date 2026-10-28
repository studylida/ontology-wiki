import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, errorMessage, isAbort } from '../repositories/http';
import { guardWikiUnload, wikiRepository } from '../repositories/wikiRepository';
import { applyWikiCommand, draftFromRevision, emptyWikiDraft, protectWikiCommand, restoreWikiCommand, saveWikiCommand } from '../services/wikiService';
import type { WikiCommand, WikiComparison, WikiDetail, WikiDraft, WikiList, WikiPage, WikiRevision, WikiRevisionSummary } from '../types/wiki';

export function useWikiController() {
  const [query, setQuery] = useState(''), [offset, setOffset] = useState(0), [refreshKey, setRefreshKey] = useState(0);
  const [listing, setListing] = useState<WikiList<WikiPage>>({items: [], total: 0, limit: 30, offset: 0});
  const [loadingList, setLoadingList] = useState(true), [listError, setListError] = useState('');
  const [page, setPage] = useState<WikiDetail | null>(null), [loadingPage, setLoadingPage] = useState(false);
  const [editing, setEditing] = useState(false), [draft, setDraft] = useState<WikiDraft>(emptyWikiDraft);
  const [baseVersion, setBaseVersion] = useState<number | null>(null), [conflicted, setConflicted] = useState(false);
  const [latest, setLatest] = useState<WikiDetail | null>(null), [error, setError] = useState(''), [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false), [pending, setPending] = useState<WikiCommand | null>(null);
  const [history, setHistory] = useState<WikiList<WikiRevisionSummary> | null>(null);
  const [historical, setHistorical] = useState<WikiRevision | null>(null), [comparison, setComparison] = useState<WikiComparison | null>(null);
  const [confirmRestore, setConfirmRestore] = useState(false), [confirmProtect, setConfirmProtect] = useState(false);
  const mounted = useRef(true), inFlight = useRef(false), request = useRef(0);
  const draftRef = useRef(draft); draftRef.current = draft;
  useEffect(() => {mounted.current = true; return () => {mounted.current = false; request.current += 1;};}, []);
  useEffect(() => guardWikiUnload(editing || !!pending), [editing, pending]);
  useEffect(() => {
    const controller = new AbortController(); setLoadingList(true);
    void wikiRepository.list(query, offset, controller.signal).then(result => {
      if (!controller.signal.aborted) {setListing(result); setListError('');}
    }).catch(e => {if (!controller.signal.aborted) setListError(errorMessage(e));})
      .finally(() => {if (!controller.signal.aborted) setLoadingList(false);});
    return () => controller.abort();
  }, [query, offset, refreshKey]);
  const refresh = useCallback(() => setRefreshKey(n => n + 1), []);
  function clearPanels() {setHistory(null); setHistorical(null); setComparison(null); setLatest(null); setConflicted(false); setConfirmRestore(false); setConfirmProtect(false);}
  async function select(id: string) {
    if (editing || pending || inFlight.current) {setError('작성 중인 내용을 저장하거나 편집을 취소한 뒤 다른 문서를 열어 주세요.'); return;}
    const sequence = ++request.current; setLoadingPage(true); setPage(null); clearPanels(); setError(''); setNotice('');
    try {const result = await wikiRepository.detail(id); if (mounted.current && sequence === request.current) setPage(result);}
    catch (e) {if (mounted.current && sequence === request.current) setError(errorMessage(e));}
    finally {if (mounted.current && sequence === request.current) setLoadingPage(false);}
  }
  function startNew() {
    if (editing || pending || busy) return;
    request.current += 1; setPage(null); setLoadingPage(false); clearPanels(); setError(''); setNotice('');
    setDraft(emptyWikiDraft()); setBaseVersion(null); setEditing(true);
  }
  function startEdit() {
    if (!page?.canEdit || busy || pending) return;
    setDraft(draftFromRevision(page.revision)); setBaseVersion(page.version); setEditing(true); clearPanels(); setError(''); setNotice('');
  }
  function cancelEdit() {if (busy || pending) return; setEditing(false); setDraft(emptyWikiDraft()); clearPanels(); setError('');}
  function change(field: keyof WikiDraft, value: string) {setDraft(current => ({...current, [field]: value}));}
  async function execute(command: WikiCommand) {
    if (inFlight.current) return;
    inFlight.current = true; setBusy(true); setPending(command); setError(''); setNotice('');
    try {
      const result = await applyWikiCommand(command);
      if (!mounted.current) return;
      setPage(result.page); setPending(null); clearPanels(); refresh();
      setEditing(false); setDraft(emptyWikiDraft()); setBaseVersion(null);
      setNotice(command.kind === 'protect' ? (result.page.locked ? '관리자가 문서를 보호했습니다.' : '문서 보호를 해제했습니다.') :
        `판본 ${result.page.revisionNumber}이 저장되었습니다.${result.receipt.replayed ? ' 기존 요청의 저장 결과를 확인했습니다.' : ''}`);
    } catch (e) {
      if (!mounted.current) return;
      setError(errorMessage(e));
      if (e instanceof ApiError && e.status >= 400 && e.status < 500) {
        setPending(null);
        if (e.code === 'wiki_version_conflict' || e.code === 'wiki_locked') {setConflicted(true); setLatest(null);}
      }
      // Unknown transport/5xx outcome retains the exact command for an idempotent resend.
    } finally {inFlight.current = false; if (mounted.current) setBusy(false);}
  }
  function save() {if (!pending) void execute(saveWikiCommand(draftRef.current, page, baseVersion));}
  async function inspectLatest() {
    if (!page || busy) return;
    setBusy(true);
    try {const result = await wikiRepository.detail(page.id); if (mounted.current) {setLatest(result); setError('');}}
    catch (e) {if (mounted.current) setError(errorMessage(e));}
    finally {if (mounted.current) setBusy(false);}
  }
  function acceptLatestBase() {
    if (!latest?.canEdit) return;
    setPage(latest); setBaseVersion(latest.version); setConflicted(false); setLatest(null);
    setNotice('비교한 최신 판본을 편집 기준으로 선택했습니다. 남겨둔 입력을 검토한 뒤 저장해 주세요.');
  }
  async function showHistory(nextOffset = 0) {
    if (!page || editing || busy || pending) return;
    const sequence = ++request.current; setBusy(true); setError('');
    try {const result = await wikiRepository.history(page.id, nextOffset); if (mounted.current && sequence === request.current) setHistory(result);}
    catch (e) {if (mounted.current && !isAbort(e)) setError(errorMessage(e));}
    finally {if (mounted.current) setBusy(false);}
  }
  async function showRevision(id: string) {
    if (!page || busy) return;
    const sequence = ++request.current; setBusy(true); setError(''); setConfirmRestore(false);
    try {
      const [revision, diff] = await Promise.all([wikiRepository.revision(page.id, id), wikiRepository.compare(page.id, id, page.currentRevisionId)]);
      if (mounted.current && sequence === request.current) {setHistorical(revision); setComparison(diff);}
    } catch (e) {if (mounted.current) setError(errorMessage(e));}
    finally {if (mounted.current) setBusy(false);}
  }
  return {query, search: (value: string) => {setQuery(value); setOffset(0);}, listing, loadingList, listError, offset, setOffset, refresh,
    page, select, loadingPage, editing, draft, change, startNew, startEdit, cancelEdit, save, busy, error, notice,
    pending, resend: () => {if (pending) void execute(pending);}, conflicted, latest, inspectLatest, acceptLatestBase,
    history, showHistory, historical, comparison, showRevision, confirmRestore, setConfirmRestore, confirmProtect, setConfirmProtect,
    restore: () => {if (page && historical) void execute(restoreWikiCommand(page, historical.id));},
    protect: () => {if (page) void execute(protectWikiCommand(page));}};
}
