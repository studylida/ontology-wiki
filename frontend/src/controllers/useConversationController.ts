import { useCallback, useEffect, useRef, useState } from 'react';
import type { Conversation, ConversationDetail, RunDetail, Submission } from '../types/contracts';
import { api } from '../repositories/api';
import { ApiError, errorMessage } from '../repositories/http';
import { newRequestId, pendingSubmission, rememberedConversation, rememberConversation, savePending } from '../repositories/workspaceStorage';
import { followRun, type Connection } from '../services/conversationService';
import { isActive } from '../services/chatState';

export function useConversationController(userId: string) {
  const [items, setItems] = useState<Conversation[]>([]);
  const [selected, setSelected] = useState<string | null>(() => { try { return rememberedConversation(userId); } catch { return null; } });
  const [pending, setPending] = useState<Submission | null>(() => pendingSubmission(userId));
  const [conversation, setConversation] = useState<ConversationDetail | null>(null), [run, setRun] = useState<RunDetail | null>(null);
  const [draft, setDraft] = useState(''), [loading, setLoading] = useState(false), [busy, setBusy] = useState(false);
  const [error, setError] = useState(''), [connection, setConnection] = useState<Connection>('idle');
  const [revision, setRevision] = useState(0);
  const locked = useRef(false), mounted = useRef(true), epoch = useRef(0);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const refresh = useCallback(() => setRevision(n => n + 1), []);
  const refreshList = useCallback(async (signal?: AbortSignal) => {
    const result = await api.conversations(signal);
    if (mounted.current && !signal?.aborted) setItems(result.items);
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    void refreshList(controller.signal).catch(e => { if (!controller.signal.aborted) setError(errorMessage(e)); });
    return () => controller.abort();
  }, [refreshList, revision]);
  useEffect(() => {
    const controller = new AbortController(), generation = ++epoch.current;
    const current = () => !controller.signal.aborted && generation === epoch.current;
    setConversation(null); setRun(null); setConnection('idle'); setError('');
    if (!selected) { setLoading(false); return () => controller.abort(); }
    setLoading(true);
    void (async () => {
      try {
        rememberConversation(userId, selected);
        const detail = await api.conversation(selected, controller.signal);
        if (!current()) return;
        setConversation(detail); setLoading(false);
        const lastAnswer = [...detail.messages].reverse().find(m => m.runId);
        if (lastAnswer?.runId) {
          await followRun(lastAnswer.runId, controller.signal, value => {
            if (!current()) return;
            setRun(value);
            setConversation(previous => previous ? {...previous, messages: previous.messages.map(m => m.id === value.answer.id ? value.answer : m)} : previous);
            const unresolved = pendingSubmission(userId);
            if (unresolved?.requestId === value.requestId) { savePending(userId, null); setPending(null); setDraft(''); }
          }, value => { if (current()) setConnection(value); });
        }
      } catch (e) { if (current()) { setError(errorMessage(e)); setConnection('disconnected'); } }
      finally { if (current()) setLoading(false); }
    })();
    return () => controller.abort();
  }, [selected, revision, userId]);
  function select(id: string) { if (!locked.current) { setDraft(''); setSelected(id); if (id === selected) refresh(); } }
  async function create() {
    if (locked.current) return;
    locked.current = true; setBusy(true); setError('');
    try { const value = await api.createConversation(); if (mounted.current) { setItems(old => [value, ...old]); setSelected(value.id); setDraft(''); } }
    catch (e) { if (mounted.current) setError(errorMessage(e)); }
    finally { locked.current = false; if (mounted.current) setBusy(false); }
  }
  async function transmit(value: Submission) {
    if (locked.current) return;
    locked.current = true; setBusy(true); setError('');
    try {
      // Persist before the request. Unknown delivery can be repeated with the SAME ID after refresh.
      savePending(userId, value); setPending(value);
      await api.submit(value);
      if (!mounted.current) return;
      savePending(userId, null); setPending(null); setDraft(''); setSelected(value.conversationId); refresh();
      if (value.kind === 'turn' && conversation?.title === '새 대화' && conversation.messages.length === 0) {
        await api.renameConversation(value.conversationId, value.question.slice(0, 100)).catch(() => undefined);
        if (mounted.current) await refreshList().catch(() => undefined);
      }
    } catch (e) {
      if (!mounted.current) return;
      if (e instanceof ApiError && e.status >= 400 && e.status < 500) { savePending(userId, null); setPending(null); }
      setError(errorMessage(e));
    } finally { locked.current = false; if (mounted.current) setBusy(false); }
  }
  function submit() {
    if (!selected || !draft.trim() || pending || loading || busy || conversation?.messages.some(m => isActive(m.status))) return;
    void transmit({kind: 'turn', conversationId: selected, question: draft.trim(), requestId: newRequestId()});
  }
  function retry(runId: string) {
    if (!selected || pending || busy) return;
    void transmit({kind: 'retry', conversationId: selected, runId, requestId: newRequestId()});
  }
  async function cancel() {
    if (!run || locked.current) return;
    locked.current = true; setBusy(true); setError('');
    try { await api.cancel(run.runId); if (mounted.current) refresh(); }
    catch (e) { if (mounted.current) setError(errorMessage(e)); }
    finally { locked.current = false; if (mounted.current) setBusy(false); }
  }
  return {items, selected, conversation, run, draft, setDraft, loading, busy, error, connection, pending,
    create, select, submit, cancel, retry, refresh, resend: () => pending && void transmit(pending),
    active: Boolean(conversation?.messages.some(m => isActive(m.status)))};
}
