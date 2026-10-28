import { useEffect, useRef, useState } from 'react';
import type { Source, SourceSelection } from '../types/contracts';
import { api } from '../repositories/api';
import { downloadSource, errorMessage } from '../repositories/http';
import { pause } from '../services/conversationService';

export function useSourceController(selection: SourceSelection) {
  const [source, setSource] = useState<Source | null>(null), [loading, setLoading] = useState(true);
  const [error, setError] = useState(''), [downloading, setDownloading] = useState(false);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    const controller = new AbortController(); setSource(null); setLoading(true); setError('');
    void (async () => {
      while (!controller.signal.aborted) {
        try {
          const value = await api.source(selection.documentId, selection.revisionId, controller.signal);
          if (controller.signal.aborted) return;
          if (selection.citation && !value.passages.some(p => p.id === selection.citation?.passageId && !p.excluded)) throw new Error('인용한 구간을 현재 원문에서 확인할 수 없습니다.');
          setSource(value); setError('');
        } catch (e) { if (controller.signal.aborted) return; setSource(null); setError(errorMessage(e)); }
        finally { if (!controller.signal.aborted) setLoading(false); }
        try { await pause(5000, controller.signal); } catch { return; }
      }
    })();
    return () => controller.abort();
  }, [selection.documentId, selection.revisionId, selection.citation?.passageId]);
  async function download() {
    setDownloading(true);
    try { await downloadSource(selection.documentId, selection.revisionId); }
    catch (e) { if (mounted.current) { setSource(null); setError(errorMessage(e)); } }
    finally { if (mounted.current) setDownloading(false); }
  }
  return {source, loading, error, downloading, download};
}
