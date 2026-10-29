import type { WikiDetail } from '../types/wiki';
import { useWikiDownload } from '../controllers/useWikiDownload';
export function WikiMarkdownDownload({page}: {page: WikiDetail}) {
  const c = useWikiDownload(page);
  return <span><button disabled={c.busy} onClick={() => void c.download()}>{c.busy ? 'Markdown 확인 중' : 'Markdown 받기'}</button>
    {c.error && <span role="alert" className="error">{c.error}</span>}</span>;
}
