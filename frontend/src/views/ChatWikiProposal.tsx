import type { ChatSeed } from '../types/wikiProposal';
import { useWikiProposalTarget } from '../controllers/useWikiProposalTarget';
import { WikiProposals } from './WikiProposals';
export function ChatWikiProposal({userId,seed,onClose}: {userId:string;seed:ChatSeed;onClose:()=>void}) {
  const target=useWikiProposalTarget();
  return <section className="wiki-chat-proposal" role="dialog" aria-label="선택 대화로 위키 제안"><button onClick={onClose}>제안 창 닫기</button>
    <h2>선택한 메시지로 위키 작성 요청</h2><p>새 개념 초안 또는 기존 문서의 보강을 선택하세요.</p>
    <form onSubmit={e=>{e.preventDefault();void target.search();}}><label>대상 위키 제목 검색<input value={target.query} onChange={e=>target.setQuery(e.target.value)}/></label><button disabled={target.busy}>대상 검색</button></form>
    {target.error && <p role="alert">{target.error}</p>}
    <button disabled={target.busy} onClick={target.newPage}>새 개념으로 제안</button>
    {target.items.map(p=><button key={p.id} disabled={target.busy} onClick={()=>void target.select(p.id)}>{p.title} · {p.meaning || p.id}</button>)}
    <p>대상: {target.page?.title || '새 개념'}</p>
    <WikiProposals key={target.page?.id || 'new'} userId={userId} page={target.page} seed={seed}/>
  </section>;
}
