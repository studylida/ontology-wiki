import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, errorMessage } from '../repositories/http';
import { proposalRepository } from '../repositories/wikiProposalRepository';
import { guardWikiUnload } from '../repositories/wikiRepository';
import { pendingProposal, savePendingProposal, newRequestId } from '../repositories/workspaceStorage';
import { applyProposalCommand, executeProposal, proposalDraft } from '../services/wikiProposalService';
import type { ChatSeed, Proposal, ProposalCommand, ProposalMode, ProposalPending, ProposalSummary } from '../types/wikiProposal';
import type { WikiDetail, WikiWrite } from '../types/wiki';
export function useWikiProposals(userId: string, page: WikiDetail | null, seed?: ChatSeed, onApplied?: (id: string) => void) {
  const [items, setItems] = useState<ProposalSummary[]>([]), [selected, setSelected] = useState<Proposal | null>(null);
  const [mode, setMode] = useState<ProposalMode>(page ? 'edit' : 'create');
  const [instruction, setInstruction] = useState(''), [context, setContext] = useState('');
  const [confirmed, setConfirmed] = useState(false), [draft, setDraft] = useState<WikiWrite | null>(null);
  const [error, setError] = useState(''), [busy, setBusy] = useState(false), [notice, setNotice] = useState('');
  const [pending, setPending] = useState<ProposalPending | null>(() => pendingProposal(userId));
  const [refresh, setRefresh] = useState(0);
  const alive = useRef(true), flight = useRef(false), sequence = useRef(0), draftId = useRef('');
  useEffect(() => {alive.current = true; return () => {alive.current = false; sequence.current++;};}, []);
  useEffect(() => guardWikiUnload(!!pending || !!draft), [pending, draft]);
  useEffect(() => {
    const abort = new AbortController();
    proposalRepository.list(page?.id, abort.signal).then(v => {if (!abort.signal.aborted) setItems(v.items);})
      .catch(e => {if (!abort.signal.aborted) setError(errorMessage(e));});
    return () => abort.abort();
  }, [page?.id, refresh]);
  const show = useCallback((value: Proposal) => {
    setSelected(value);
    setItems(items => items.map(item => item.id === value.id ? {...item, status: value.status, updatedAt: value.updatedAt} : item));
    if (value.status === 'ready' && draftId.current !== value.id) {setDraft(proposalDraft(value)); draftId.current = value.id;}
  }, []);
  useEffect(() => {
    if (!selected || busy || pending || !['pending', 'running'].includes(selected.status)) return;
    const abort = new AbortController();
    const n = sequence.current;
    let reading = false;
    const timer = setInterval(() => {
      if (reading) return;
      reading = true;
      proposalRepository.get(selected.id, abort.signal).then(v => {if (!abort.signal.aborted && n === sequence.current) show(v);})
        .catch(e => {if (!abort.signal.aborted && n === sequence.current) setError(errorMessage(e));})
        .finally(() => {reading = false;});
    }, 1600);
    return () => {clearInterval(timer); abort.abort();};
  }, [selected?.id, selected?.status, busy, pending, show]);
  function remember(value: ProposalPending | null) {
    setPending(value);
    if (!savePendingProposal(userId, value)) setNotice('브라우저 복구 저장소를 사용할 수 없습니다. 요청 결과를 확인하기 전 창을 닫지 마세요.');
  }
  async function open(id: string) {
    if (flight.current || pending) return;
    const n = ++sequence.current; setBusy(true); setError('');
    try {const value = await proposalRepository.get(id); if (alive.current && n === sequence.current) {if (draftId.current !== value.id) setDraft(null); show(value);}}
    catch(e) {if (alive.current && n === sequence.current) setError(errorMessage(e));}
    finally {if (alive.current && n === sequence.current) setBusy(false);}
  }
  async function execute(value: ProposalPending) {
    if (flight.current) return;
    flight.current = true; const n = ++sequence.current; setBusy(true); setError(''); remember(value);
    let acknowledged = value.receipt;
    try {
      const result = await executeProposal(value, receipt => {acknowledged = receipt; if (alive.current && n === sequence.current) remember({...value, receipt});});
      if (!alive.current || n !== sequence.current) return;
      remember(null); show(result); setRefresh(k => k+1);
      if (result.status === 'applied') {setDraft(null); setNotice('직원이 확인한 내용이 공용 위키에 저장됐습니다.'); onApplied?.(result.appliedResult!.pageId);}
    } catch(e) {
      if (!alive.current || n !== sequence.current) return;
      setError(errorMessage(e));
      if (!acknowledged && e instanceof ApiError && e.status >= 400 && e.status < 500) {
        remember(null);
        if (value.command.kind === 'apply') {
          try {const updated = await proposalRepository.get(value.command.id);
            if (alive.current && n === sequence.current) show(updated);
          } catch { /* Keep the reviewed draft on failure. */ }
        }
      }
    } finally {flight.current = false; if (alive.current && n === sequence.current) setBusy(false);}
  }
  function submit() {
    if (busy || pending || !instruction.trim() || (seed && (!confirmed || !context.trim() || !seed.content.includes(context)))) return;
    const command: ProposalCommand = {kind: 'submit', body: {requestId: newRequestId(), mode: page ? mode : 'create',
      ...(page ? {pageId: page.id} : {}), instruction, ...(seed ? {selection: {conversationId: seed.conversationId,
        messageId: seed.messageId, text: context}} : {contextText: context})}};
    void execute({command, receipt: null});
  }
  async function dismiss() {
    if (!selected || flight.current || busy || pending) return;
    flight.current = true; const n = ++sequence.current; setBusy(true);
    try {await proposalRepository.dismiss(selected.id); const updated = await proposalRepository.get(selected.id);
      if (alive.current && n === sequence.current) {show(updated); setDraft(null); setRefresh(k=>k+1);}}
    catch(e) {if (alive.current && n === sequence.current) setError(errorMessage(e));}
    finally {flight.current = false; if (alive.current && n === sequence.current) setBusy(false);}
  }
  return {items, selected, mode, setMode, instruction, setInstruction, context, setContext, confirmed, setConfirmed,
    draft, change: (key: keyof WikiWrite, value: string) => {if (!busy && !pending) setDraft(d => d ? {...d,[key]:value}:d);},
    busy, pending, error, notice, open, submit, dismiss, refresh: () => setRefresh(k=>k+1),
    retryRead: () => selected && void open(selected.id),
    resend: () => pending && void execute(pending),
    apply: () => {if (selected?.canApply && draft?.title.trim() && draft.markdown.trim() && !busy && !pending)
      void execute({command: applyProposalCommand(selected, draft), receipt: null});}};
}
