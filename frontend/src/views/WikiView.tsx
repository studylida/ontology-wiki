import { WikiProposals } from './WikiProposals';
import { WikiMarkdownDownload } from './WikiMarkdownDownload';
import { useState } from 'react';
import { useWikiController } from '../controllers/useWikiController';
import { validWikiDraft } from '../services/wikiService';
import { WikiDiscovery, WikiSearchPanel } from './WikiDiscovery';
import { SafeMarkdown } from './components/SafeMarkdown';
import './wiki.css';
const date = (value: string) => new Date(value).toLocaleString('ko-KR');
export function WikiView({userId}: {userId: string}) {
  const wiki = useWikiController(userId), page = wiki.page;
  const [search, setSearch] = useState(''), [preview, setPreview] = useState(false);
  const unavailable = wiki.busy || !!wiki.pending;
  return <section className="wiki" aria-label="공용 위키">
    <header className="section-header"><div><p className="eyebrow">SHARED WIKI</p><h1>공용 위키</h1><p>개념과 업무 경험을 함께 기록하고 보강합니다.</p></div>
      <button className="primary" disabled={unavailable || wiki.editing} onClick={wiki.startNew}>새 위키 문서</button></header>
    <p className="muted">모든 직원이 읽고 일반 문서를 편집할 수 있습니다. 검색 준비가 끝나면 채팅의 근거로 활용합니다. AI 제안은 직접 확인한 뒤 반영합니다.</p>
    {wiki.error && <p role="alert" className="error">{wiki.error}</p>}{wiki.notice && <p role="status" className="notice">{wiki.notice}</p>}
    {wiki.storageWarning && <p className="notice" role="alert">{wiki.storageWarning}</p>}
    {wiki.pending && !wiki.busy && <div className="notice" role="alert"><p>{wiki.pending.receipt ?
      '저장은 확인했지만 문서 조회에 실패했습니다. 저장 요청을 반복하지 않고 문서만 다시 불러옵니다.' :
      '저장 결과를 확인하지 못했습니다. 입력은 보존했습니다. 같은 요청으로 다시 확인하면 중복 저장하지 않습니다.'}</p>
      <button onClick={wiki.resend}>{wiki.pending.receipt ? '저장된 문서 다시 불러오기' : '같은 저장 요청 다시 확인'}</button></div>}
    <WikiSearchPanel onNavigate={id => void wiki.select(id)} disabled={unavailable || wiki.editing} />
    {!wiki.editing && !wiki.pending && <WikiProposals key={page?.id || "new"} userId={userId} page={page} onApplied={id => {wiki.refresh(); void wiki.select(id);}}/>}
    <div className="wiki-workspace"><aside className="wiki-list" aria-label="위키 문서 목록">
      <form onSubmit={e => {e.preventDefault(); wiki.search(search);}}><label>위키 제목 검색<input value={search} maxLength={300} onChange={e => setSearch(e.target.value)} /></label>
        <div className="actions"><button>검색</button><button type="button" onClick={wiki.refresh}>목록 새로고침</button></div></form>
      {wiki.listError && <p role="alert" className="error">{wiki.listError}</p>}
      {wiki.loadingList ? <p role="status">문서 목록을 불러오는 중입니다.</p> : <p className="muted">{wiki.listing.total}개 문서</p>}
      {!wiki.loadingList && !wiki.listing.total && <p>등록된 문서가 없거나 제목 검색 결과가 없습니다.</p>}
      {wiki.listing.items.map(item => <button className={`wiki-item ${page?.id === item.id ? 'selected' : ''}`} key={item.id}
        disabled={unavailable || wiki.editing} aria-pressed={page?.id === item.id} onClick={() => void wiki.select(item.id)}>
        <strong>{item.title}</strong>{item.meaning && <small>{item.meaning}</small>}<small>v{item.revisionNumber} · {item.editor.username} {item.locked ? '· 보호됨' : ''}</small><small>{date(item.updatedAt)}</small></button>)}
      <div className="actions"><button disabled={wiki.offset === 0 || wiki.loadingList} onClick={() => wiki.setOffset(Math.max(0, wiki.offset - wiki.listing.limit))}>이전 문서 목록</button>
        <button disabled={wiki.offset + wiki.listing.limit >= wiki.listing.total || wiki.loadingList} onClick={() => wiki.setOffset(wiki.offset + wiki.listing.limit)}>다음 문서 목록</button></div>
    </aside><div className="wiki-detail">
      {wiki.loadingPage && <p role="status">문서를 불러오는 중입니다.</p>}
      {wiki.editing ? <form className="wiki-editor" aria-label="위키 편집" onSubmit={e => {e.preventDefault(); wiki.save();}}>
        <h2>{page || wiki.pending?.command.kind === 'edit' ? '문서 편집' : '새 문서 작성'}</h2>
        <p className="muted">저장하면 전 직원에게 바로 공개됩니다. 출처나 업무 경험은 필요한 만큼 기록하세요.</p>
        <label>위키 제목<input required maxLength={300} value={wiki.draft.title} disabled={unavailable} onChange={e => wiki.change('title', e.target.value)} /></label>
        <label>다른 이름·약어 (선택 · 한 줄에 하나)<textarea rows={2} value={wiki.draft.aliasesText || ''} disabled={unavailable} onChange={e => wiki.change('aliasesText', e.target.value)} /></label>
        <label>이 개념의 뜻·구분 (선택)<input maxLength={500} value={wiki.draft.meaning || ''} disabled={unavailable} onChange={e => wiki.change('meaning', e.target.value)} /></label>
        <p className="muted">본문에 [개념 이름](/wiki/문서ID) 형식으로 연결할 수 있습니다. 대상 문서의 고정 링크를 복사해 사용하세요.</p>
        <WikiSearchPanel draft={wiki.draft} exclude={page?.id} onNavigate={id => void wiki.select(id)} disabled={unavailable} />
        <div className="wiki-field"><label htmlFor="wiki-markdown">위키 본문 (Markdown)</label><textarea id="wiki-markdown" required maxLength={100000} rows={14} value={wiki.draft.markdown} disabled={unavailable} onChange={e => wiki.change('markdown', e.target.value)} /></div>
        <div className="wiki-field"><label htmlFor="wiki-source-note">근거·업무 맥락 (선택)</label><textarea id="wiki-source-note" rows={3} maxLength={10000} placeholder="문헌명·판본·관련 위치 또는 프로젝트에서 직접 확인한 조건을 적어 주세요." value={wiki.draft.sourceNote} disabled={unavailable} onChange={e => wiki.change('sourceNote', e.target.value)} /></div>
        <label>변경 요약 (선택)<input maxLength={500} value={wiki.draft.changeSummary} disabled={unavailable} onChange={e => wiki.change('changeSummary', e.target.value)} /></label>
        <div className="actions"><button className="primary" disabled={unavailable || wiki.conflicted || !validWikiDraft(wiki.draft)}>위키 저장</button>
          <button type="button" disabled={unavailable} onClick={wiki.cancelEdit}>편집 취소</button>
          <button type="button" onClick={() => setPreview(value => !value)}>{preview ? '미리보기 닫기' : 'Markdown 미리보기'}</button></div>
        {preview && <div className="wiki-preview"><SafeMarkdown onWikiNavigate={id => void wiki.select(id)} content={wiki.draft.markdown} /></div>}

      </form> : page ? <>
        <WikiDiscovery key={page.id} page={page} onNavigate={id => void wiki.select(id)} />
        <header><h2>{page.title}</h2>{page.meaning && <p>{page.meaning}</p>}{!!page.aliases?.length && <p className="muted">다른 이름: {page.aliases.join(" · ")}</p>}<p className="muted">v{page.revisionNumber} · {page.locked ? '보호된 문서' : '공동 편집 가능'}</p>
          {page.revision.aiAssisted && <p className="notice">AI 제안을 직원이 검토·수정하여 반영한 판본입니다. 자동으로 사실을 인증한 내용은 아닙니다.</p>}
          <p className="muted">작성 {page.creator.username} · {date(page.createdAt)}<br/>최근 본문 수정 {page.editor.username} · {date(page.revision.createdAt)}</p></header>
        <div className="actions">{page.canEdit && <button disabled={unavailable || wiki.conflicted} onClick={wiki.startEdit}>문서 편집</button>}
          <WikiMarkdownDownload page={page} />
          <button disabled={unavailable} onClick={() => void wiki.showHistory()}>변경 이력</button>
          <button disabled={unavailable} onClick={() => void wiki.select(page.id)}>문서 새로고침</button>
          {page.canProtect && <button disabled={unavailable || wiki.conflicted} onClick={() => wiki.setConfirmProtect(true)}>{page.locked ? '문서 보호 해제' : '문서 보호'}</button>}</div>
        {!page.canEdit && <p className="notice">관리자가 보호한 문서입니다. 열람과 이전 판본 확인은 가능합니다.</p>}
        {wiki.confirmProtect && <div role="alertdialog" aria-label="문서 보호 변경 확인" className="notice"><p>{page.locked ? '모든 직원이 다시 편집할 수 있도록 보호를 해제합니다.' : '일반 직원의 편집과 복구를 제한합니다. 모든 직원은 계속 읽을 수 있습니다.'}</p>
          <button disabled={unavailable || wiki.conflicted} onClick={wiki.protect}>보호 변경 실행</button> <button disabled={unavailable} onClick={() => wiki.setConfirmProtect(false)}>보호 변경 취소</button></div>}
        <article aria-label="위키 본문"><SafeMarkdown onWikiNavigate={id => void wiki.select(id)} content={page.revision.markdown} /></article>
        {page.revision.sourceNote && <section className="wiki-sources" aria-label="근거와 업무 맥락"><h3>근거·업무 맥락</h3><p className="muted">편집자가 기록한 출처 또는 경험입니다. 공식 승인이나 사실 인증을 뜻하지 않습니다.</p><SafeMarkdown onWikiNavigate={id => void wiki.select(id)} content={page.revision.sourceNote} /></section>}
        {wiki.history && <section aria-label="위키 변경 이력" className="wiki-history"><h3>변경 이력</h3>
          {wiki.history.items.map(revision => <button key={revision.id} disabled={unavailable} onClick={() => void wiki.showRevision(revision.id)}>
            <strong>v{revision.number} · {revision.editor.username}</strong> · {date(revision.createdAt)}<br/>{revision.changeSummary || '변경 요약 없음'}{revision.restoredFromId ? ' · 이전 판본 복구' : ''}</button>)}
          <div className="actions"><button disabled={unavailable || wiki.history.offset === 0} onClick={() => void wiki.showHistory(Math.max(0, wiki.history!.offset - wiki.history!.limit))}>이전 이력 목록</button>
            <button disabled={unavailable || wiki.history.offset + wiki.history.limit >= wiki.history.total} onClick={() => void wiki.showHistory(wiki.history!.offset + wiki.history!.limit)}>다음 이력 목록</button></div>
        </section>}
        {wiki.historical && <section aria-label="이전 판본" className="wiki-historical"><h3>이전 판본 v{wiki.historical.number}: {wiki.historical.title}</h3><SafeMarkdown onWikiNavigate={id => void wiki.select(id)} content={wiki.historical.markdown} />
          {wiki.historical.sourceNote && <><h4>이 판본의 근거·업무 맥락</h4><SafeMarkdown onWikiNavigate={id => void wiki.select(id)} content={wiki.historical.sourceNote} /></>}
          <h4>선택한 판본 → 현재 판본 변경 비교</h4><pre className="wiki-diff">{wiki.comparison?.diff || '내용 차이가 없습니다.'}</pre>
          {page.canEdit && wiki.historical.id !== page.currentRevisionId && <button disabled={unavailable || wiki.conflicted} onClick={() => wiki.setConfirmRestore(true)}>이 판본으로 복구</button>}
          {wiki.confirmRestore && <div role="alertdialog" aria-label="이전 판본 복구 확인" className="notice"><p>제목·본문·근거 메모를 선택한 판본으로 복구해 새 판본으로 저장합니다. 현재와 과거 이력은 삭제하지 않습니다.</p>
            <button disabled={unavailable || wiki.conflicted} onClick={wiki.restore}>복구 실행</button> <button disabled={unavailable} onClick={() => wiki.setConfirmRestore(false)}>복구 취소</button></div>}
        </section>}
      </> : !wiki.loadingPage && <p className="empty">문서를 선택하거나 새로운 개념을 기록해 보세요.</p>}
    {wiki.conflicted && <div className="notice"><h3>{wiki.editing ? '입력을 보존했습니다' : '최신 문서 상태를 확인해 주세요'}</h3><p>다른 직원의 수정이나 문서 보호 상태가 바뀌었습니다. 최신 내용과 비교한 뒤 작업을 다시 선택해 주세요.</p>
          <button type="button" disabled={wiki.busy} onClick={() => void wiki.inspectLatest()}>최신 판본과 비교</button>
          {wiki.latest && <><h4>서버의 최신 판본 v{wiki.latest.revisionNumber}: {wiki.latest.title}</h4><SafeMarkdown onWikiNavigate={id => void wiki.select(id)} content={wiki.latest.revision.markdown} />
            {wiki.latest.revision.sourceNote && <><h4>최신 근거·업무 맥락</h4><SafeMarkdown onWikiNavigate={id => void wiki.select(id)} content={wiki.latest.revision.sourceNote} /></>}
            {wiki.editing && <p>내 입력은 자동으로 병합되지 않습니다. 위 입력란과 최신 내용을 비교해 필요한 부분을 직접 반영하세요.</p>}
            {(wiki.latest.canEdit || !wiki.editing) ? <button type="button" onClick={wiki.acceptLatestBase}>{wiki.editing ? '최신 판본 확인 후 편집 계속' : '최신 문서 상태로 돌아가기'}</button> : <p>보호된 문서입니다. 관리자만 본문을 변경할 수 있습니다.</p>}</>}
        </div>}
    </div></div>
  </section>;
}
