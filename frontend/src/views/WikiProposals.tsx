import { useId, useState } from 'react';
import { useWikiProposals } from '../controllers/useWikiProposals';
import { proposalLabel, proposalSource } from '../services/wikiProposalService';
import type { ChatSeed } from '../types/wikiProposal';
import type { WikiDetail } from '../types/wiki';
import type { SourceSelection } from '../types/contracts';
import { SafeMarkdown } from './components/SafeMarkdown';
import { SourcePanel } from './SourcePanel';
import { WikiSearchPanel } from './WikiDiscovery';
export function WikiProposals({userId, page, seed, onApplied}: {userId: string; page: WikiDetail | null; seed?: ChatSeed; onApplied?: (id:string)=>void}) {
  const c = useWikiProposals(userId, page, seed, onApplied), p = c.selected;
  const fieldId = useId();
  const [source, setSource] = useState<SourceSelection | null>(null), [preview, setPreview] = useState(false);
  return <section className="wiki-proposals" aria-label="AI 위키 편집 보조">
    <h2>{page ? '이 문서의 AI 수정 제안' : 'AI로 새 개념 초안 만들기'}</h2>
    <p className="muted">제안은 본인과 대상 문서 관리자만 확인합니다. 직접 검토하고 반영하기 전에는 공용 위키·검색·Markdown에 공개되지 않습니다.</p>
    <details open={!!seed}><summary>AI에게 {page ? '부분 수정·링크' : '새 초안'} 요청</summary>
      {seed && <><div className="proposal-field"><label htmlFor={`${fieldId}-message`}>대화 메시지 원문 — 반영할 부분만 선택하세요</label><textarea id={`${fieldId}-message`} readOnly rows={5} value={seed.content}
        onSelect={e => {const t=e.currentTarget; if(t.selectionEnd>t.selectionStart)c.setContext(t.value.slice(t.selectionStart,t.selectionEnd));}} /></div>
        <p>선택한 문장만 전달합니다. 대화 전체와 다른 메시지는 포함되지 않습니다.</p></>}
      <form onSubmit={e=>{e.preventDefault();c.submit();}}>
        {page && <label>제안 종류<select disabled={c.busy || !!c.pending} value={c.mode} onChange={e=>c.setMode(e.target.value as 'edit'|'links')}><option value="edit">필요한 부분 수정</option><option value="links">핵심 개념 링크만 제안</option></select></label>}
        <div className="proposal-field"><label htmlFor={`${fieldId}-instruction`}>AI 편집 요청</label><textarea id={`${fieldId}-instruction`} maxLength={3000} rows={2} value={c.instruction} disabled={c.busy || !!c.pending} onChange={e=>c.setInstruction(e.target.value)} /></div>
        <div className="proposal-field"><label htmlFor={`${fieldId}-context`}>{seed ? '위키 반영 요청에 포함할 선택 문장' : '추가할 업무 경험·내용 (선택)'}</label><textarea id={`${fieldId}-context`} maxLength={6000} rows={3} value={c.context} disabled={c.busy || !!c.pending} onChange={e=>c.setContext(e.target.value)} /></div>
        {seed && <label><input type="checkbox" checked={c.confirmed} onChange={e=>c.setConfirmed(e.target.checked)}/> 선택 문장과 요청만 제안 검토용으로 전달하는 것을 확인했습니다.</label>}
        <button disabled={c.busy || !!c.pending || !c.instruction.trim() || (!!seed && (!c.confirmed || !c.context.trim() || !seed.content.includes(c.context)))}>AI 제안 요청</button>
      </form>
    </details>
    {c.error && <p role="alert" className="error">{c.error}</p>}{c.notice && <p role="status">{c.notice}</p>}
    {c.pending && <div className="notice"><p>{c.pending.receipt ? '접수·저장은 확인했습니다. 제안 조회만 다시 확인합니다.' : '접수 결과를 확인하지 못했습니다. 동일한 요청으로 확인해 주세요.'}</p><button disabled={c.busy} onClick={c.resend}>같은 제안 요청 다시 확인</button></div>}
    <div className="actions"><button disabled={c.busy || !!c.pending} onClick={c.refresh}>제안 목록 새로고침</button>
      {c.items.map(i=><button key={i.id} disabled={c.busy || !!c.pending} onClick={()=>void c.open(i.id)}>{proposalLabel(i.status)} · {new Date(i.createdAt).toLocaleString('ko-KR')}</button>)}</div>
    {p && <article aria-label="위키 제안 검토"><h3>{proposalLabel(p.status)}</h3>
      {['pending','running'].includes(p.status) && <p role="status">기존 작업자가 처리합니다. 이 화면의 조회·새로고침은 새 모델 호출을 만들지 않습니다.</p>}
      {p.error && <p role="alert">{p.error.message} 위의 요청을 다시 확인해 새 제안을 요청할 수 있습니다.</p>}
      <details><summary>이 제안에 전달한 요청과 선택 내용</summary><p>{p.instruction}</p><pre className="wiki-diff">{p.employeeText}</pre></details>
      <p>{p.result.reason}</p>{p.result.model?.startsWith('fixture') && <p className="notice">검증용 fixture 제안입니다. 실제 AI 품질 평가가 아닙니다.</p>}
      {(p.result.warnings || []).map((w,i)=><p className="muted" key={i}>{w}</p>)}
      {p.stale && <p role="alert" className="notice">대상 문서나 보호 상태가 변경됐습니다. 입력은 유지합니다. 최신 문서를 확인하고 새 제안을 요청해 주세요.</p>}
      {p.base.markdown && <details><summary>AI가 읽은 기존 본문</summary><SafeMarkdown content={p.base.markdown}/></details>}
      {p.result.diff && <details open><summary>AI가 제안한 변경 부분</summary><pre className="wiki-diff">{p.result.diff}</pre></details>}
      {(p.result.links || []).map(l=><p key={l.pageId}>링크 제안: {l.anchor} — {l.reason}</p>)}
      {(p.result.evidence || []).map(e=><div key={e.passageId}><p>{e.title} · {e.locator}</p><blockquote>{e.text}</blockquote><button onClick={()=>setSource(proposalSource(e))}>해당 판본 근거 확인</button></div>)}
      {!!p.result.similar?.length && <div className="notice">비슷한 기존 문서가 있습니다. 새 문서 저장을 막지 않습니다.
        {p.result.similar.map(s=><p key={s.pageId}><a target="_blank" rel="noopener noreferrer" href={'/wiki/'+s.pageId}>{s.title}</a> — {s.meaning}</p>)}</div>}
      {p.status === 'ready' && c.draft && <form onSubmit={e=>{e.preventDefault();c.apply();}} aria-label="제안 반영 편집">
        <label>반영할 위키 제목<input maxLength={300} value={c.draft.title} disabled={c.busy || !!c.pending} onChange={e=>c.change('title',e.target.value)}/></label>
        <div className="proposal-field"><label htmlFor={`${fieldId}-markdown`}>반영할 Markdown</label><textarea id={`${fieldId}-markdown`} rows={10} maxLength={100000} value={c.draft.markdown} disabled={c.busy || !!c.pending} onChange={e=>c.change('markdown',e.target.value)}/></div>
        <div className="proposal-field"><label htmlFor={`${fieldId}-source`}>반영할 근거·업무 맥락</label><textarea id={`${fieldId}-source`} rows={2} maxLength={10000} value={c.draft.sourceNote} disabled={c.busy || !!c.pending} onChange={e=>c.change('sourceNote',e.target.value)}/></div>
        {!page && <WikiSearchPanel draft={c.draft} disabled={c.busy} onNavigate={()=>{}}/>}
        <p className="notice">아래 반영 버튼을 누르면 위의 제목·본문·근거 메모가 공용 위키에 공개됩니다. 요청문과 개인 대화 원문은 자동 공개하지 않습니다.</p>
        <button type="button" onClick={()=>setPreview(v=>!v)}>반영 내용 미리보기</button>
        {preview && <SafeMarkdown content={c.draft.markdown}/>}
        <button className="primary" disabled={!p.canApply || c.busy || !!c.pending || !c.draft.title.trim() || !c.draft.markdown.trim()}>검토한 내용 위키에 반영</button>
        {!p.canApply && !p.stale && <p>현재 권한으로 반영할 수 없습니다. 보호된 문서는 관리자만 반영합니다.</p>}
      </form>}
      {!['applied','dismissed'].includes(p.status) && <button disabled={c.busy || !!c.pending} onClick={()=>void c.dismiss()}>이 제안 무시</button>}
      {p.appliedResult && <p><a href={'/wiki/'+p.appliedResult.pageId}>반영한 위키 열기</a></p>}
    </article>}
    {source && <SourcePanel selection={source} onClose={()=>setSource(null)}/>}
  </section>;
}
