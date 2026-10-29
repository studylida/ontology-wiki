import { useEffect, useRef, useState } from 'react';
import type { EvidenceSource, SourceSelection } from '../types/contracts';
import { errorMessage } from '../repositories/http';
import { readSource, downloadEvidence, sourceKey } from '../services/sourceService';
import { pause } from '../services/conversationService';

export function useSourceController(selection: SourceSelection) {
  const [source, setSource] = useState<EvidenceSource | null>(null), [loading, setLoading] = useState(true);
  const [error, setError] = useState(''), [downloading, setDownloading] = useState(false);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    const controller = new AbortController(); setSource(null); setLoading(true); setError('');
    void (async () => {
      while (!controller.signal.aborted) {
        try {
          const value = await readSource(selection, controller.signal);
          if (controller.signal.aborted) return;
          setSource(value); setError('');
        } catch (e) { if (controller.signal.aborted) return; setSource(null); setError(errorMessage(e)); }
        finally { if (!controller.signal.aborted) setLoading(false); }
        try { await pause(5000, controller.signal); } catch { return; }
      }
    })();
    return () => controller.abort();
  }, [sourceKey(selection)]);
  async function download() {
    setDownloading(true);
    try { await downloadEvidence(selection); }
    catch (e) { if (mounted.current) { setSource(null); setError(errorMessage(e)); } }
    finally { if (mounted.current) setDownloading(false); }
  }
  return {source, loading, error, downloading, download};
}
