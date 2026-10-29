import { useEffect, useRef, useState } from 'react';
import { downloadEvidence } from '../services/sourceService';
import { errorMessage } from '../repositories/http';
import type { WikiDetail } from '../types/wiki';
export function useWikiDownload(page: WikiDetail) {
  const [busy, setBusy] = useState(false), [error, setError] = useState('');
  const mounted = useRef(true);
  useEffect(() => {mounted.current = true; return () => {mounted.current = false;};}, []);
  const download = async () => {
    if (busy) return;
    setBusy(true); setError('');
    try {await downloadEvidence({sourceKind: 'wiki', pageId: page.id, revisionId: page.currentRevisionId, title: page.title});}
    catch (e) {if (mounted.current) setError(errorMessage(e));}
    finally {if (mounted.current) setBusy(false);}
  };
  return {busy, error, download};
}
