import type { ChatSeed } from '../types/wikiProposal';
import { useLayoutEffect, useRef } from 'react';
import type { Citation } from '../types/contracts';
import type { useConversationController } from '../controllers/useConversationController';
import { statusLabel } from '../services/chatState';
import { orderedCitations } from '../services/citationService';
import { SafeMarkdown } from './components/SafeMarkdown';
type Chat = ReturnType<typeof useConversationController>;
export function ConversationView({chat, onCitation, onWikiRequest}: {chat: Chat; onCitation: (c: Citation) => void; onWikiRequest?: (seed:ChatSeed)=>void}) {
  const scroller = useRef<HTMLDivElement>(null), stick = useRef(true);
  useLayoutEffect(() => { stick.current = true; }, [chat.selected]);
  useLayoutEffect(() => { const node = scroller.current; if (node && stick.current) node.scrollTop = node.scrollHeight; }, [chat.conversation?.messages]);
  const messages = chat.conversation?.messages || [];
  const lastAssistant = [...messages].reverse().find(m => m.role === 'assistant');
  return <section className="chat" aria-label="대화">
    <header className="section-header"><div><p className="eyebrow">PRIVATE CONVERSATION</p><h1>{chat.conversation?.title || '문헌에서 근거를 찾으세요'}</h1></div>
      <button disabled={chat.busy || chat.loading} onClick={chat.refresh}>대화 상태 새로고침</button></header>
    {chat.error && <p role="alert" className="error">{chat.error}</p>}
    {chat.pending && <div className="notice" role="status"><strong>전송 결과 확인이 필요합니다.</strong><p>새 요청을 만들지 않습니다. 같은 요청 ID로 접수를 확인합니다.</p>
      <button disabled={chat.busy} onClick={chat.resend}>같은 요청 다시 전송</button></div>}
    {['connecting', 'reconnecting', 'disconnected'].includes(chat.connection) && <div className="notice" role="status">
      {chat.connection === 'disconnected' ? '연결이 끊겼습니다. 표시된 내용은 마지막으로 확인한 상태입니다.' : '저장된 답변과 연결 상태를 확인하고 있습니다.'}
      {chat.connection === 'disconnected' && <button onClick={chat.refresh}>저장된 실행 다시 연결</button>}</div>}
    <div className="messages" ref={scroller} onScroll={() => {const n = scroller.current; if (n) stick.current = n.scrollHeight - n.scrollTop - n.clientHeight < 100;}} aria-busy={chat.loading}>
      {chat.loading && <p role="status">대화를 불러오는 중입니다.</p>}
      {!chat.selected && <div className="empty"><h2>새 대화로 시작하세요</h2><p>공용 문헌이나 위키를 준비한 뒤 질문하고 문장 옆 각주로 근거를 확인할 수 있습니다.</p><button className="primary" onClick={chat.create} disabled={chat.busy}>새 대화 시작</button></div>}
      {chat.selected && !chat.loading && messages.length === 0 && <p className="empty">확인하고 싶은 업무 질문을 입력해 주세요.</p>}
      {messages.map(message => <article key={message.id} className={`message ${message.role}`} data-testid={`message-${message.role}`}>
        <div className="message-heading"><strong>{message.role === 'user' ? '나' : '어시스턴트'}</strong>
          {message.role === 'assistant' && <span role="status">{statusLabel(message.status)}</span>}</div>
        {message.sourceUnavailable ? <p role="alert">근거 자료를 현재 사용할 수 없어 답변과 출처를 숨겼습니다.</p> : <>
          {message.historicalSources && <p className="notice">과거 판본을 사용한 답변입니다. 현재 기준은 새 질문으로 확인해 주세요.</p>}
          <SafeMarkdown content={message.content} citations={message.role === 'assistant' ? message.citations : []} onCitation={onCitation} />
          {message.role === 'assistant' && orderedCitations(message.citations).length > 0 && <nav className="citations" aria-label="답변 출처 목록">
            {orderedCitations(message.citations).map(c => <button key={c.passageId} onClick={() => onCitation(c)}>[{c.number}] {c.title} · {c.locator}</button>)}
          </nav>}
        </>}
        {!message.sourceUnavailable && message.content && message.status === 'completed' && chat.selected && onWikiRequest &&
          <button onClick={()=>onWikiRequest({conversationId:chat.selected!,messageId:message.id,content:message.content})}>선택해서 위키 제안</button>}
        {message.warnings.map(warning => <p className="muted" key={warning}>{warning}</p>)}
        {message.runId === chat.run?.runId && chat.run.error && <p role="alert" className="error">{chat.run.error.message}</p>}
        {message.id === lastAssistant?.id && ['failed', 'cancelled', 'interrupted'].includes(message.status) && message.runId &&
          <button disabled={chat.busy || chat.active || Boolean(chat.pending)} onClick={() => chat.retry(message.runId!)}>답변 다시 생성</button>}
      </article>)}
    </div>
    <form className="composer" onSubmit={e => {e.preventDefault(); chat.submit();}}>
      <label htmlFor="question">업무 질문</label><textarea id="question" rows={3} maxLength={30000} value={chat.draft}
        onChange={e => chat.setDraft(e.target.value)} placeholder="문헌의 적용 조건이나 선택 이유를 질문해 보세요."
        disabled={!chat.selected || chat.loading || chat.busy || Boolean(chat.pending)} />
      <div className="composer-actions"><small>문헌과 위키는 공용입니다. 이 대화는 본인만 볼 수 있습니다.</small>
        {chat.active && <button type="button" disabled={chat.busy || !chat.run} onClick={chat.cancel}>답변 중단</button>}
        <button className="primary" disabled={!chat.selected || chat.busy || chat.loading || chat.active || !chat.draft.trim() || Boolean(chat.pending)}>질문 보내기</button></div>
    </form>
  </section>;
}
