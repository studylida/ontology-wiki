import { useEffect, useState } from 'react';
import { errorMessage } from '../repositories/http';
import { loadDocumentWikiNotice } from '../services/documentWikiService';
import type { DocumentWikiNotice } from '../types/documentWiki';
export function useDocumentWikiNotice(documentId: string, revisionId: string) {
  const [value, setValue] = useState<DocumentWikiNotice | null>(null), [error, setError] = useState('');
  useEffect(() => {
    const abort = new AbortController(); let reading = false;
    setValue(null); setError('');
    const read = async () => {
      if (reading || abort.signal.aborted) return;
      reading = true;
      try {const result = await loadDocumentWikiNotice(documentId, abort.signal);
        if (!abort.signal.aborted) {setValue(result); setError('');}}
      catch(e) {if (!abort.signal.aborted) setError(errorMessage(e));}
      finally {reading = false;}
    };
    void read(); const timer = setInterval(() => void read(), 3500);
    return () => {abort.abort(); clearInterval(timer);};
  }, [documentId, revisionId]);
  return {value, error};
}
