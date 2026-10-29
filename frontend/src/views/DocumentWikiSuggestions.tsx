import { useState } from 'react';
import { useDocumentWikiNotice } from '../controllers/useDocumentWikiNotice';
import { documentWikiLabel } from '../services/documentWikiService';
import { WikiProposals } from './WikiProposals';
export function DocumentWikiSuggestions({userId, documentId, revisionId}: {userId: string; documentId: string; revisionId: string}) {
  const {value, error} = useDocumentWikiNotice(documentId, revisionId), [open, setOpen] = useState(false);
  if (error) return <p className="muted">{error}</p>;
  if (!value) return null;
  const count = value.items.filter(p => ['pending','running','ready'].includes(p.status)).length;
  return <aside className="document-wiki-notice" aria-label="문헌의 위키 보강 안내">
    <p role="status">{documentWikiLabel(value.status)} · 확인할 제안 {count}건</p>
    <p className="muted">위키 보강은 선택 사항입니다. 확인하지 않아도 문헌 검색과 채팅을 사용할 수 있습니다.</p>
    {!value.enabled && <p className="muted">자동 검토는 비용·자료 사용 범위를 확인한 서버 설정에서 켭니다.</p>}
    {value.error && <p className="notice">{value.error.message} 자동 유료 재시도는 하지 않습니다.</p>}
    {value.result.reason && <p>{value.result.reason}</p>}
    {(value.result.warnings || []).map((w,i) => <p key={i} className="muted">{w}</p>)}
    {!!value.items.length && <><button onClick={() => setOpen(v => !v)}>{open ? '위키 제안 접기' : '위키 보강 제안 확인'}</button>
      {open && <WikiProposals key={documentId+revisionId} userId={userId} page={null} documentId={documentId}/>}</>}
  </aside>;
}
