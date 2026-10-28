import { useEffect, useRef, useState } from 'react';
import type { SharedDocument, Source } from '../types/contracts';
import { api } from '../repositories/api';
import { errorMessage } from '../repositories/http';
import { pause } from '../services/conversationService';

export function useDocumentController(onMutation: () => void) {
  const [items, setItems] = useState<SharedDocument[]>([]), [selected, setSelected] = useState<string | null>(null);
  const [source, setSource] = useState<Source | null>(null), [error, setError] = useState(''), [sourceError, setSourceError] = useState('');
  const [busy, setBusy] = useState(false), [loading, setLoading] = useState(true), [notice, setNotice] = useState('');
  const [revision, setRevision] = useState(0), [confirmId, setConfirmId] = useState<string | null>(null);
  const locked = useRef(false), mounted = useRef(true);
  const current = items.find(d => d.id === selected) || null;
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      while (!controller.signal.aborted) {
        try {
          const response = await api.documents(controller.signal);
          if (controller.signal.aborted) return;
          setItems(response.items); setError(''); setLoading(false);
        } catch (e) { if (controller.signal.aborted) return; setError('상태 갱신 실패: ' + errorMessage(e)); setLoading(false); }
        try { await pause(2000, controller.signal); } catch { return; }
      }
    })();
    return () => controller.abort();
  }, [revision]);
  useEffect(() => {
    const controller = new AbortController(); setSource(null); setSourceError('');
    if (current && !current.withdrawn && current.currentRevisionId) {
      void api.source(current.id, current.currentRevisionId, controller.signal).then(value => {
        if (!controller.signal.aborted) setSource(value);
      }).catch(e => { if (!controller.signal.aborted) setSourceError(errorMessage(e)); });
    }
    return () => controller.abort();
  }, [selected, current?.currentRevisionId, current?.status, current?.latestRevision?.heldPassageCount, revision]);
  async function upload(file: File, title: string) {
    if (locked.current) return false;
    locked.current = true; setBusy(true); setError(''); setNotice('');
    try {
      const receipt = await api.upload(file, title);
      if (!mounted.current) return false;
      setSelected(receipt.documentId); setRevision(n => n + 1);
      setNotice(receipt.duplicate ? '같은 문헌의 기존 등록 결과입니다. 아래 서버 상태를 확인해 주세요.' : '파일을 저장하고 처리를 접수했습니다. 검색 가능 여부는 아래 상태에서 확인해 주세요.');
      onMutation(); return true;
    } catch (e) { if (mounted.current) setError(errorMessage(e)); return false; }
    finally { locked.current = false; if (mounted.current) setBusy(false); }
  }
  async function operate(id: string, action: 'reprocess' | 'deactivate') {
    if (locked.current) return;
    locked.current = true; setBusy(true); setError(''); setNotice('');
    try {
      await api[action](id);
      if (!mounted.current) return;
      setConfirmId(null); setSource(null); setRevision(n => n + 1); onMutation();
      setNotice(action === 'deactivate' ? '서버에서 문헌을 비활성화했습니다.' : '재처리 요청을 확인했습니다. 실제 작업 상태를 아래에서 확인해 주세요.');
    } catch (e) { if (mounted.current) setError(errorMessage(e)); }
    finally { locked.current = false; if (mounted.current) setBusy(false); }
  }
  return {items, selected, setSelected, current, source, error, sourceError, busy, loading, notice, upload,
    confirmId, setConfirmId, operate, refresh: () => setRevision(n => n + 1)};
}
