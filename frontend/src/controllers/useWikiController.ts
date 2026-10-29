import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, errorMessage } from '../repositories/http';
import { guardWikiUnload, wikiRepository } from '../repositories/wikiRepository';
import { pendingWikiMutation, savePendingWikiMutation } from '../repositories/workspaceStorage';
import { applyWikiCommand, draftFromPending, draftFromRevision, emptyWikiDraft, protectWikiCommand,
  restoreWikiCommand, saveWikiCommand, validWikiDraft, wikiMutationNotice } from '../services/wikiService';
import { currentWikiPage, onWikiNavigation, rememberWikiPage } from '../repositories/wikiNavigation';
import type { WikiCommand, WikiComparison, WikiDetail, WikiDraft, WikiList, WikiPage, WikiPending, WikiRevision, WikiRevisionSummary } from '../types/wiki';

/** Workspace is keyed by authenticated user; no private recovery state crosses logout. */
export function useWikiController(userId: string, active = true) {
  const [recovered] = useState(() => pendingWikiMutation(userId));
  const [pending, setPending] = useState<WikiPending | null>(recovered);
  const [query, setQuery] = useState(''), [offset, setOffset] = useState(0), [refreshKey, setRefreshKey] = useState(0);
  const [listing, setListing] = useState<WikiList<WikiPage>>({items: [], total: 0, limit: 30, offset: 0});
  const [loadingList, setLoadingList] = useState(true), [listError, setListError] = useState('');
  const [page, setPage] = useState<WikiDetail | null>(null), [loadingPage, setLoadingPage] = useState(false);
  const [targetId, setTargetId] = useState<string | null>(recovered?.command.kind !== 'create' ? recovered?.command.pageId || null : null);
  const [editing, setEditing] = useState(recovered?.command.kind === 'create' || recovered?.command.kind === 'edit');
  const [draft, setDraft] = useState<WikiDraft>(() => draftFromPending(recovered));
  const [baseVersion, setBaseVersion] = useState<number | null>(recovered?.command.kind === 'edit' ? recovered.command.body.baseVersion : null);
  const [conflicted, setConflicted] = useState(false), [latest, setLatest] = useState<WikiDetail | null>(null);
  const [error, setError] = useState(''), [notice, setNotice] = useState(''), [storageWarning, setStorageWarning] = useState('');
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState<WikiList<WikiRevisionSummary> | null>(null);
  const [historical, setHistorical] = useState<WikiRevision | null>(null), [comparison, setComparison] = useState<WikiComparison | null>(null);
  const [confirmRestore, setConfirmRestore] = useState(false), [confirmProtect, setConfirmProtect] = useState(false);
  const mounted = useRef(true), inFlight = useRef(false), request = useRef(0);
  const draftRef = useRef(draft); draftRef.current = draft;
  const current = (sequence: number) => mounted.current && sequence === request.current;
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
  const navigation = useRef<(id: string) => void>(() => {});
  navigation.current = id => { void select(id); };
  useEffect(() => {
    const id = currentWikiPage();
    if (id && !recovered) navigation.current(id);
    return onWikiNavigation(id => {if (id) navigation.current(id);});
  }, []);
  // The view stays mounted across tabs. Background read/save completion must not
  // replace a chat/documents URL; returning to the wiki restores its permalink.
  useEffect(() => {if (active && page) rememberWikiPage(page.id, true);}, [active, page?.id]);
  const refresh = useCallback(() => setRefreshKey(n => n + 1), []);
  function remember(value: WikiPending | null) {
    setPending(value);
    setStorageWarning(savePendingWikiMutation(userId, value) ? '' : '브라우저 저장소를 사용할 수 없습니다. 결과를 확인하기 전에는 이 화면을 닫지 마세요.');
  }
  function clearPanels() {setHistory(null); setHistorical(null); setComparison(null); setLatest(null); setConflicted(false); setConfirmRestore(false); setConfirmProtect(false);}
  async function select(id: string) {
    if (editing || pending || inFlight.current) {
      if (page) rememberWikiPage(page.id, true);
      setError('작성 중인 내용을 저장하거나 편집을 취소한 뒤 다른 문서를 열어 주세요.'); return;
    }
    const sequence = ++request.current; setBusy(false); setLoadingPage(true); setTargetId(id); setPage(null); clearPanels(); setError(''); setNotice('');
    if (active) rememberWikiPage(id);
    try {const result = await wikiRepository.detail(id); if (current(sequence)) setPage(result);}
    catch (e) {if (current(sequence)) setError(errorMessage(e));}
    finally {if (current(sequence)) setLoadingPage(false);}
  }
  function startNew() {
    if (editing || pending || busy || inFlight.current) return;
    request.current += 1; setTargetId(null); setPage(null); setLoadingPage(false); clearPanels(); setError(''); setNotice('');
    setDraft(emptyWikiDraft()); setBaseVersion(null); setEditing(true);
  }
  function startEdit() {
    if (!page?.canEdit || busy || pending || conflicted || inFlight.current) return;
    setTargetId(page.id); setDraft(draftFromRevision(page.revision)); setBaseVersion(page.version); setEditing(true); clearPanels(); setError(''); setNotice('');
  }
  function cancelEdit() {if (busy || pending) return; setEditing(false); setDraft(emptyWikiDraft()); clearPanels(); setError('');}
  function change(field: keyof WikiDraft, value: string) {if (!busy && !pending) setDraft(valueBefore => ({...valueBefore, [field]: value}));}
  async function execute(command: WikiCommand, receipt = pending?.receipt || null) {
    if (inFlight.current) return;
    const sequence = ++request.current;
    inFlight.current = true; setBusy(true); remember({command, receipt}); setError(''); setNotice('');
    if (command.kind !== 'create') setTargetId(command.pageId);
    let acknowledged = receipt;
    try {
      const result = await applyWikiCommand(command, receipt, value => {
        acknowledged = value;
        if (current(sequence)) remember({command, receipt: value});
      });
      if (!current(sequence)) return;
      setPage(result.page); setTargetId(result.page.id); remember(null); clearPanels(); refresh();
      setEditing(false); setDraft(emptyWikiDraft()); setBaseVersion(null);
      setNotice(wikiMutationNotice(command, result.receipt, result.page));
    } catch (e) {
      if (!current(sequence)) return;
      setError(errorMessage(e));
      // Only a rejected write may clear the command. Readback failure never loses its receipt.
      if (!acknowledged && e instanceof ApiError && e.status >= 400 && e.status < 500) {
        remember(null);
        if (e.code === 'wiki_version_conflict' || e.code === 'wiki_locked') {setConflicted(true); setLatest(null);}
      }
    } finally {inFlight.current = false; if (current(sequence)) setBusy(false);}
  }
  function save() {
    if (pending || busy || conflicted || !editing || !validWikiDraft(draftRef.current)) return;
    if (targetId && !page) {setConflicted(true); setError('저장된 편집 기준을 다시 확인해 주세요.'); return;}
    void execute(saveWikiCommand(draftRef.current, page, baseVersion));
  }
  async function inspectLatest() {
    if (!targetId || busy || pending) return;
    const sequence = ++request.current; setBusy(true);
    try {const result = await wikiRepository.detail(targetId); if (current(sequence)) {setLatest(result); setError('');}}
    catch (e) {if (current(sequence)) setError(errorMessage(e));}
    finally {if (current(sequence)) setBusy(false);}
  }
  function acceptLatestBase() {
    if (!latest || (editing && !latest.canEdit)) return;
    setPage(latest); setBaseVersion(latest.version); clearPanels(); refresh();
    setNotice(editing ? '비교한 최신 판본을 편집 기준으로 선택했습니다. 남겨둔 입력을 검토한 뒤 저장해 주세요.' :
      '최신 문서 상태를 확인했습니다. 필요한 작업을 다시 선택해 주세요.');
  }
  async function showHistory(nextOffset = 0) {
    if (!page || editing || busy || pending) return;
    const sequence = ++request.current; setBusy(true); setError('');
    try {const result = await wikiRepository.history(page.id, nextOffset); if (current(sequence)) setHistory(result);}
    catch (e) {if (current(sequence)) setError(errorMessage(e));}
    finally {if (current(sequence)) setBusy(false);}
  }
  async function showRevision(id: string) {
    if (!page || busy || pending) return;
    const sequence = ++request.current; setBusy(true); setError(''); setConfirmRestore(false);
    try {
      const [revision, diff] = await Promise.all([wikiRepository.revision(page.id, id), wikiRepository.compare(page.id, id, page.currentRevisionId)]);
      if (current(sequence)) {setHistorical(revision); setComparison(diff);}
    } catch (e) {if (current(sequence)) setError(errorMessage(e));}
    finally {if (current(sequence)) setBusy(false);}
  }
  return {query, search: (value: string) => {setQuery(value); setOffset(0);}, listing, loadingList, listError, offset, setOffset, refresh,
    page, select, loadingPage, editing, draft, change, startNew, startEdit, cancelEdit, save, busy, error, notice, storageWarning,
    pending, resend: () => {if (pending) void execute(pending.command, pending.receipt);}, conflicted, latest, inspectLatest, acceptLatestBase,
    history, showHistory, historical, comparison, showRevision, confirmRestore, setConfirmRestore, confirmProtect, setConfirmProtect,
    restore: () => {if (page && historical && !busy && !pending && !conflicted) void execute(restoreWikiCommand(page, historical.id));},
    protect: () => {if (page && !busy && !pending && !conflicted) void execute(protectWikiCommand(page));}};
}
