import { useEffect, useRef } from 'react';
import type { SourceSelection } from '../types/contracts';
import { useSourceController } from '../controllers/useSourceController';
import { DocumentMarkdown, SafeMarkdown } from './components/SafeMarkdown';
import { wikiPageHref } from '../services/wikiLinks';
export function SourcePanel({selection, onClose}: {selection: SourceSelection; onClose: () => void}) {
  const controller = useSourceController(selection), close = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    close.current?.focus();
    return () => { if (previous?.isConnected) previous.focus(); };
  }, []);
  const c = selection.citation;
  const isWiki = selection.sourceKind === 'wiki';
  const wiki = controller.source && 'pageId' in controller.source ? controller.source : null;
  const passage = c ? controller.source?.passages.find(p => p.id === c.passageId) : null;
  return <aside className="source-panel" aria-label="원문 패널" onKeyDown={e => {if (e.key === 'Escape') onClose();}}>
    <header className="section-header"><h2>{c ? `출처 [${c.number}]` : '문헌 원문'}</h2><button ref={close} onClick={onClose}>원문 닫기</button></header>
    <p className="muted">{isWiki ? '공용 위키 · 직원이 편집한 지식' : '원본 문헌'}</p>
    <h3>{selection.title}</h3><p className="muted">판본 ID: {selection.revisionId}</p>
    {controller.loading && <p role="status">원문 구간을 확인하는 중입니다.</p>}
    {controller.error && <p role="alert" className="error">{controller.error}</p>}
    {controller.source && <>
      {!controller.source.active && <p className="notice">현재 검색에 쓰이는 활성 판본이 아닙니다. 인용한 판본을 그대로 표시합니다.</p>}
      <button disabled={controller.downloading} onClick={controller.download}>{controller.downloading ? '원본 확인 중' : isWiki ? '이 판본 Markdown 받기' : '원본 파일 받기'}</button>
      {wiki && <section aria-label="위키 판본 정보"><p>v{wiki.revisionNumber} · {wiki.editor.username} · {new Date(wiki.createdAt).toLocaleString('ko-KR')}</p>
        <a href={wikiPageHref(wiki.pageId)} target="_blank" rel="noopener noreferrer">현재 위키 문서 열기</a>
        {wiki.sourceNote && <details><summary>편집자가 기록한 근거·업무 맥락</summary><p className="muted">직원이 기록한 메모이며 문헌의 검증된 인용이 아닙니다.</p><SafeMarkdown content={wiki.sourceNote} /></details>}
        <details><summary>인용한 판본의 전체 Markdown</summary><SafeMarkdown content={wiki.content} /></details>
      </section>}
      {passage && <section className="evidence" data-testid="evidence-passage"><h3>[{c!.number}] {passage.locator}</h3><DocumentMarkdown content={passage.text} /></section>}
      {c ? <details><summary>이 판본의 전체 추출 구간</summary>{controller.source.passages.map(p => <section key={p.id}><h4>{p.locator}</h4>{p.excluded && <p className="notice">검색 보류: {p.exclusionReason}</p>}<DocumentMarkdown content={p.text} /></section>)}</details>
        : controller.source.passages.map(p => <section key={p.id}><h4>{p.locator}</h4>{p.excluded && <p className="notice">검색 보류: {p.exclusionReason}</p>}<DocumentMarkdown content={p.text} /></section>)}
      {controller.source.passages.length === 0 && <p>아직 추출된 구간이 없습니다. 처리 상태를 확인해 주세요. 원본 파일은 별도로 보존되어 있습니다.</p>}
    </>}
  </aside>;
}
