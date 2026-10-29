import { useCallback, useEffect, useState } from 'react';
import { BookOpen, LogOut, MessageSquare } from 'lucide-react';
import type { Citation, SourceSelection, User } from './types/contracts';
import { useAuthController } from './controllers/useAuthController';
import { useConversationController } from './controllers/useConversationController';
import { LoginView } from './views/LoginView';
import { ConversationView } from './views/ConversationView';
import { DocumentsView } from './views/DocumentsView';
import { SourcePanel } from './views/SourcePanel';
import { currentWikiPage, onWikiNavigation } from './repositories/wikiNavigation';
import { WikiView } from './views/WikiView';
function Workspace({user, logout}: {user: User; logout: () => void}) {
  const chat = useConversationController(user.id);
  const [tab, setTab] = useState<'chat' | 'documents' | 'wiki'>(() => currentWikiPage() ? 'wiki' : 'chat');
  const [wikiOpened, setWikiOpened] = useState(() => !!currentWikiPage());
  useEffect(() => onWikiNavigation(id => {if (id) {setTab('wiki'); setWikiOpened(true);}}), []);
  const [source, setSource] = useState<SourceSelection | null>(null);
  useEffect(() => setSource(null), [chat.selected]);
  const documentsChanged = useCallback(() => {setSource(null); chat.refresh();}, [chat.refresh]);
  const showCitation = useCallback((citation: Citation) => setSource({documentId: citation.documentId,
    revisionId: citation.sourceRevisionId, title: citation.title, citation}), []);
  return <div className={`workspace ${source ? 'with-source' : ''}`}>
    <aside className="sidebar"><div className="brand"><BookOpen aria-hidden="true" /><strong>사내 지식<br/>어시스턴트</strong></div>
      <button className="primary" disabled={chat.busy} onClick={() => {setTab('chat'); setSource(null); void chat.create();}}>새 대화</button>
      <nav aria-label="작업 공간"><button aria-current={tab === 'chat' ? 'page' : undefined} onClick={() => {setTab('chat'); setSource(null); chat.refresh();}}><MessageSquare aria-hidden="true" /> 대화</button>
        <button aria-current={tab === 'documents' ? 'page' : undefined} onClick={() => {setTab('documents'); setSource(null);}}><BookOpen aria-hidden="true" /> 공용 문헌</button>
        <button aria-current={tab === 'wiki' ? 'page' : undefined} onClick={() => {setTab('wiki'); setWikiOpened(true); setSource(null);}}><BookOpen aria-hidden="true" /> 공용 위키</button></nav>
      <h2>내 대화</h2><nav className="conversation-list" aria-label="내 대화 목록">{chat.items.map(item => <button key={item.id} aria-current={chat.selected === item.id ? 'true' : undefined}
        disabled={chat.busy} onClick={() => {setTab('chat'); setSource(null); chat.select(item.id);}}><span>{item.title}</span><small>{new Date(item.updatedAt).toLocaleString('ko-KR')}</small></button>)}</nav>
      <footer><span>{user.username}</span><button onClick={logout}><LogOut aria-hidden="true" /> 로그아웃</button></footer>
    </aside>
    <main className="main-content">{tab === 'chat' && <ConversationView chat={chat} onCitation={showCitation} />}{tab === 'documents' && <DocumentsView onMutation={documentsChanged} onSource={setSource} />}
      {wikiOpened && <div className="wiki-host" hidden={tab !== 'wiki'}><WikiView userId={user.id} /></div>}</main>
    {source && <SourcePanel key={`${source.documentId}:${source.revisionId}:${source.citation?.passageId || ''}`} selection={source} onClose={() => setSource(null)} />}
  </div>;
}
export default function App() {
  const auth = useAuthController();
  if (auth.checking) return <main className="empty" role="status">로그인 상태 확인 중</main>;
  return auth.user ? <Workspace key={auth.user.id} user={auth.user} logout={auth.logout} /> : <LoginView busy={auth.busy} error={auth.error} login={auth.login} />;
}
