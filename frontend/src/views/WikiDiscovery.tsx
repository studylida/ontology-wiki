import { useWikiDiscovery, useWikiSearch } from '../controllers/useWikiDiscovery';
import { indexLabels } from '../services/wikiDiscoveryService';
import { wikiPageHref } from '../services/wikiLinks';
import type { WikiDetail, WikiDraft } from '../types/wiki';

export function WikiDiscovery({page, onNavigate}: {page: WikiDetail; onNavigate: (id: string) => void}) {
  const state = useWikiDiscovery(page.id, page.version);
  return <section className="wiki-discovery" aria-label="위키 검색 준비와 이름 안내">
    {state.alternatives.length > 0 && <aside className="notice" aria-label="다른 의미 안내">
      <strong>다른 의미를 찾고 있나요?</strong><p>같은 이름으로 등록된 문서입니다. 뜻과 설명을 확인해 주세요.</p>
      {state.alternatives.map(item => <p key={item.page.id}><button type="button" onClick={() => onNavigate(item.page.id)}>{item.page.title}</button> {item.page.meaning}</p>)}
    </aside>}
    {state.error && <p className="notice" role="alert">{state.error} <button type="button" onClick={state.refresh}>상태 다시 확인</button></p>}
    {state.index ? <div role="status"><strong>{indexLabels[state.index.status] || state.index.status}</strong>
      <span className="muted"> · 본문은 저장되어 있습니다. 색인 대기 중에도 읽고 편집할 수 있습니다.</span>
      {state.index.indexedRevisionId && state.index.indexedRevisionId !== state.index.currentRevisionId &&
        <p className="notice">이전 판본의 색인은 최신 본문 검색에 사용하지 않습니다. 새 판본 준비를 기다려 주세요.</p>}
      {state.index.job?.error && <p>{state.index.job.error.message}</p>}
      {state.index.canRetry && <button type="button" disabled={state.busy} onClick={() => void state.retry()}>위키 색인 재시도</button>}
      {state.index.heldPassages.length > 0 && <details><summary>보류 구간 {state.index.heldPassages.length}개</summary>
        {state.index.heldPassages.map(item => <p key={item.id}>{item.locator} — {item.reason}</p>)}</details>}
    </div> : !state.error && <p className="muted">검색 준비 상태 확인 중</p>}
    <label>이 문서의 고정 링크<input readOnly value={wikiPageHref(page.id)} onFocus={e => e.target.select()} /></label>
  </section>;
}

export function WikiSearchPanel({onNavigate, draft, exclude, disabled = false}: {
  onNavigate: (id: string) => void; draft?: WikiDraft; exclude?: string; disabled?: boolean;
}) {
  const search = useWikiSearch(draft, exclude);
  return <section className="wiki-discovery" aria-label={draft ? '비슷한 위키 안내' : '위키 내용 검색'}>
    {!draft && <label>개념·내용 검색<input value={search.query} maxLength={4000} onChange={e => search.setQuery(e.target.value)}
      onKeyDown={e => {if (e.key === 'Enter' && search.query.trim()) {e.preventDefault(); void search.run();}}} /></label>}
    <button type="button" disabled={disabled || search.busy || !(draft ? draft.title.trim() : search.query.trim())} onClick={() => void search.run()}>
      {draft ? '비슷한 위키 문서 확인' : '키워드·의미 검색'}</button>
    <p className="muted">{draft ? '중복 여부를 단정하지 않습니다. 기존 문서를 확인하거나 새 문서 작성을 계속할 수 있습니다.' :
      '검색을 실행할 때만 임베딩을 사용합니다. 문서 열람에는 AI 호출이 필요하지 않습니다.'}</p>
    {search.busy && <p role="status">위키를 검색하고 있습니다.</p>}
    {search.error && <p role="alert" className="error">{search.error}</p>}
    {search.result && <><p className="muted">{search.result.semanticStatus === 'used' ? '키워드 + 의미 검색' : '키워드 검색'} ·
      {search.result.reranking.status === 'used' ? ' 재순위화 적용' : ' 기본 검색 순위'}</p>
      {search.result.warnings.map(w => <p key={w} className="notice">{w}</p>)}
      {!search.result.items.length && <p>검색된 문서가 없습니다. 같은 개념이 없다는 보증은 아닙니다.</p>}
      {search.result.items.map(hit => <article className="wiki-search-hit" key={hit.page.id}>
        <strong>{hit.page.title}</strong><small> · v{hit.page.revisionNumber} · {hit.locator}</small>
        {hit.page.meaning && <p>{hit.page.meaning}</p>}<p>{hit.excerpt}</p>
        {hit.nameMatch && <p className="muted">이름이 일치하는 항목입니다. 같은 개념인지는 내용을 확인하세요.</p>}
        {draft ? <a href={wikiPageHref(hit.page.id)} target="_blank" rel="noopener noreferrer">기존 문서 확인·보강 (새 탭)</a> :
          <button type="button" disabled={disabled} onClick={() => onNavigate(hit.page.id)}>문서 열기</button>}
      </article>)}
    </>}
  </section>;
}
