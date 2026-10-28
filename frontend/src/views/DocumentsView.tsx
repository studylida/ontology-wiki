import { useRef, useState } from 'react';
import { useDocumentController } from '../controllers/useDocumentController';
import { documentStatus } from '../services/documentService';
import type { SourceSelection } from '../types/contracts';
export function DocumentsView({onMutation, onSource}: {onMutation: () => void; onSource: (source: SourceSelection) => void}) {
  const docs = useDocumentController(onMutation), input = useRef<HTMLInputElement>(null);
  const [title, setTitle] = useState(''), [file, setFile] = useState<File | null>(null);
  const current = docs.current, latest = current?.latestRevision;
  return <section className="documents" aria-label="공용 문헌">
    <header className="section-header"><div><p className="eyebrow">SHARED KNOWLEDGE</p><h1>공용 문헌</h1></div><button onClick={docs.refresh}>문헌 상태 새로고침</button></header>
    <form className="upload" onSubmit={e => {e.preventDefault(); if (file) void docs.upload(file, title).then(ok => {if (ok) {setFile(null); setTitle(''); if (input.current) input.current.value = '';}});}}>
      <h2>문헌 업로드</h2><p id="sharing-note"><strong>회사 전체 직원이 검색하고 활용하는 공용 자료입니다.</strong> 전사 공유가 허용된 자료만 업로드해 주세요. 별도 관리자 승인은 필요하지 않습니다.</p>
      <div className="upload-fields"><label>문헌 제목 (선택)<input maxLength={500} value={title} onChange={e => setTitle(e.target.value)} disabled={docs.busy} /></label>
        <label>문헌 파일<input ref={input} type="file" accept=".md,.markdown,.txt,.pdf,.xml,.nxml,.jats" aria-describedby="sharing-note" required disabled={docs.busy} onChange={e => setFile(e.target.files?.[0] || null)} /></label></div>
      <div className="row"><small>Markdown·UTF-8 텍스트·PDF·JATS XML / 최대 20MB. 파일 저장과 검색 준비는 별도 단계입니다.</small>
        <button className="primary" disabled={docs.busy || !file}>{docs.busy ? '요청 처리 중' : '공용 문헌 업로드'}</button></div>
    </form>
    {docs.error && <p role="alert" className="error">{docs.error}</p>}{docs.notice && <p role="status" className="notice">{docs.notice}</p>}
    {docs.loading && <p role="status">문헌 상태를 불러오는 중입니다.</p>}
    <div className="document-workspace"><div className="document-list"><h2>문헌 목록 <small>최근 100개</small></h2>
      {!docs.loading && docs.items.length === 0 && <p>아직 등록된 공용 문헌이 없습니다.</p>}
      {docs.items.map(d => <button className={`document-item ${docs.selected === d.id ? 'selected' : ''}`} key={d.id} aria-pressed={docs.selected === d.id} onClick={() => docs.setSelected(d.id)}>
        <strong>{d.title}</strong><span>{documentStatus(d.status)}</span><small>{d.searchable ? `공용 검색 가능 · 판본 ${d.activeRevision?.revision}` : '공용 검색 불가'}</small></button>)}
    </div><div className="document-detail" aria-label="문헌 운영 상세">
      {!current ? <p className="empty">문헌을 선택하면 판본과 처리 상태를 확인할 수 있습니다.</p> : <>
        <h2>{current.title}</h2><p role="status">최신 판본: {latest?.revision ?? '없음'} · {documentStatus(current.status)}</p>
        <p>검색에 사용하는 판본: {current.searchable ? current.activeRevision?.revision : '없음'}</p>
        {current.searchable && current.activeRevisionId !== current.currentRevisionId && <p className="notice">새 판본과 별개로 기존 유효 판본을 검색에 사용하고 있습니다.</p>}
        {latest && <><p>파일: {latest.filename}</p><p>전체 구간 {latest.passageCount} · 유효 {latest.usablePassageCount} · 보류 {latest.heldPassageCount}</p>
          {latest.job && <p>처리 작업: {documentStatus(latest.job.status)}{latest.job.stage ? ` · ${latest.job.stage}` : ''}</p>}
          {latest.job?.error && <p role="alert" className="error">{latest.job.error.message} <small>({latest.job.error.code})</small></p>}
          {latest.limitations.map(note => <p className="notice" key={note}>{note}</p>)}
        </>}
        <div className="actions">
          {!current.withdrawn && current.currentRevisionId && <button onClick={() => onSource({documentId: current.id, revisionId: current.currentRevisionId!, title: latest?.title || current.title})}>최신 판본 원문 확인</button>}
          {!current.withdrawn && current.activeRevisionId && current.activeRevisionId !== current.currentRevisionId && <button onClick={() => onSource({documentId: current.id, revisionId: current.activeRevisionId!, title: current.activeRevision?.title || current.title})}>사용 중 판본 원문 확인</button>}
          {current.canManage && !current.withdrawn && <><button disabled={docs.busy} onClick={() => void docs.operate(current.id, 'reprocess')}>재처리 요청</button>
            <button className="danger" disabled={docs.busy} onClick={() => docs.setConfirmId(current.id)}>문헌 비활성화</button></>}
        </div>
        {!current.canManage && <p className="muted">이 문헌의 변경 작업은 서버에서 허용된 등록자 또는 운영자만 수행할 수 있습니다.</p>}
        {current.canManage && !current.withdrawn && <p className="muted">실패한 작업을 재처리합니다. 이미 완료되었거나 진행 중인 작업은 서버가 중복 실행하지 않습니다.</p>}
        {docs.confirmId === current.id && <div role="alertdialog" aria-label="문헌 비활성화 확인" className="notice">
          <p>공용 검색과 원문 열람에서 제외합니다. 이 문헌을 사용한 과거 답변도 제한됩니다.</p>
          <button disabled={docs.busy} onClick={() => docs.setConfirmId(null)}>돌아가기</button> <button className="danger" disabled={docs.busy} onClick={() => void docs.operate(current.id, 'deactivate')}>비활성화 실행</button></div>}
        {!current.withdrawn && <><h3>최신 판본 보류 구간</h3>{docs.sourceError && <p role="alert" className="error">{docs.sourceError}</p>}
          {docs.source ? docs.source.passages.filter(p => p.excluded).length ? docs.source.passages.filter(p => p.excluded).map(p => <details key={p.id}><summary>{p.locator} · {p.exclusionReason || '품질 확인 필요'}</summary><pre>{p.text}</pre></details>) : <p>보류된 구간이 없습니다.</p> : !docs.sourceError && <p>구간 상태 확인 중</p>}</>}
      </>}
    </div></div>
  </section>;
}
