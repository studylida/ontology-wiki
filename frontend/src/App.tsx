import { useCallback, useEffect, useState } from "react";
import {
  BookOpen,
  ChevronLeft,
  Compass,
  Cpu,
  FileCheck2,
  LogOut,
  Menu,
  MessageSquare,
  Plus,
  Search,
  Settings2,
  X,
} from "lucide-react";
import type {
  DocumentSummary,
  Route,
  TransferResult,
  User,
} from "./types/contracts";
import { useAuthController } from "./controllers/useAuthController";
import { useRoute } from "./controllers/useRoute";
import { useConversationController } from "./controllers/useConversationController";
import { useResearchController } from "./controllers/useResearchController";
import { useSourceController } from "./controllers/useSourceController";
import { useWikiController } from "./controllers/useWikiController";
import { useReviewController } from "./controllers/useReviewController";
import { useEnvironmentController } from "./controllers/useSettingsController";
import { LoginView } from "./views/LoginView";
import { ConversationView } from "./views/ConversationView";
import { ResearchView } from "./views/ResearchView";
import { PersonalWikiView } from "./views/PersonalWikiView";
import { ReviewView } from "./views/ReviewView";
import { BatchUploadDialog, canBatchDocumentUpload } from "./views/BatchUploadDialog";
import { SourcePanel } from "./views/SourcePanel";
import {
  ResourcePicker,
  SettingsDialog,
  UploadDialog,
} from "./views/WorkspaceDialogs";
import {
  EmptyState,
  ErrorNotice,
  InfoNotice,
  Loading,
} from "./views/components/Primitives";

function Workspace({ user, onLogout }: { user: User; onLogout: () => void }) {
  const { route, navigate } = useRoute();
  const [activeConversationId, setActiveConversationId] = useState<
    string | undefined
  >(() =>
    ["conversation", "research"].includes(route.screen) ? route.id : undefined,
  );
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dialog, setDialog] = useState<
    "resources" | "upload" | "batch-upload" | "settings" | null
  >(null);
  const [conversationFilter, setConversationFilter] = useState("");
  const [globalNotice, setGlobalNotice] = useState<string | null>(null);
  const canReview =
    user.permissions?.includes("documents:review") ||
    ["admin", "reviewer"].includes(user.role);
  const canBatchUpload = canBatchDocumentUpload(user.permissions);
  const canIndex =
    user.permissions?.includes("jobs:manage") || user.role === "admin";
  const onCreated = useCallback(
    (id: string) => {
      setActiveConversationId(id);
      navigate({ screen: "conversation", id }, true);
    },
    [navigate],
  );
  const selectedId =
    route.screen === "conversation" ? route.id : activeConversationId;
  const chat = useConversationController(user.id, selectedId, onCreated);
  const source = useSourceController();
  const environment = useEnvironmentController();
  const go = useCallback(
    (next: Route) => {
      if (next.screen === "conversation") setActiveConversationId(next.id);
      navigate(next);
      setSidebarOpen(false);
    },
    [navigate],
  );
  const startNew = () => {
    chat.prepareNew();
    go({ screen: "conversation" });
  };
  const transfer = useCallback(
    (result: TransferResult & { conversationId: string }) => {
      chat.attachResearch(result.attachmentIds, result.conversationId);
      setActiveConversationId(result.conversationId);
      setGlobalNotice(
        `문헌 ${result.attachmentIds.length}개를 대화에 가져왔습니다.${result.submittedDocumentIds.length ? ` 공개 문헌 ${result.submittedDocumentIds.length}개가 검토 대기 자료로 제출되었습니다.` : ""}${result.warnings.length ? ` ${result.warnings.join(" ")}` : ""}`,
      );
      navigate({ screen: "conversation", id: result.conversationId });
      void chat.refreshList();
    },
    [chat.attachResearch, chat.refreshList, navigate],
  );
  const research = useResearchController(transfer);
  const wiki = useWikiController(
    route.screen === "personal-wiki",
    route.screen === "personal-wiki" ? route.id : undefined,
  );
  const review = useReviewController(route.screen === "review" && canReview);
  useEffect(() => {
    if (route.screen === "conversation") setActiveConversationId(route.id);
    document.title = `${{ conversation: "대화", research: "외부 문헌 조사", "personal-wiki": "개인 위키", review: "문헌 검토" }[route.screen]} · 반도체 지식 허브`;
  }, [route]);
  const openResearch = () => {
    const latestUser = [...chat.state.messages]
      .reverse()
      .find((message) => message.role === "user");
    research.begin(chat.state.id, chat.state.draft.text || latestUser?.content);
    go({ screen: "research", id: chat.state.id });
  };
  const questionDocument = useCallback(
    (id: string, title: string) => {
      chat.attachDocument(id, title);
      go({ screen: "conversation", id: chat.state.id });
    },
    [chat.attachDocument, chat.state.id, go],
  );
  const documentCreated = useCallback(
    (document: DocumentSummary) => {
      chat.attachDocument(document.currentRevisionId, document.title);
      setDialog(null);
      setGlobalNotice(
        `“${document.title}” 문헌을 등록하고 다음 질문에 추가했습니다. 공용 검색 반영 상태는 별도로 관리됩니다.`,
      );
      go({ screen: "conversation", id: chat.state.id });
    },
    [chat.attachDocument, chat.state.id, go],
  );
  const questionWiki = (text: string) => {
    chat.setFollowup({ title: "개인 위키 주제로 이어서 질문", text });
    go({ screen: "conversation", id: chat.state.id });
  };
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-workspace">
        본문으로 건너뛰기
      </a>
      <header className="mobile-bar">
        <button
          className="icon-button"
          onClick={() => setSidebarOpen(true)}
          aria-label="탐색 메뉴 열기"
        >
          <Menu size={21} />
        </button>
        <strong>
          <Cpu size={19} />
          반도체 지식 허브
        </strong>
        <button className="icon-button" onClick={startNew} aria-label="새 대화">
          <Plus size={20} />
        </button>
      </header>
      {sidebarOpen && (
        <button
          className="sidebar-backdrop"
          aria-label="탐색 메뉴 닫기"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <aside className={`app-sidebar ${sidebarOpen ? "is-open" : ""}`}>
        <div className="sidebar-brand">
          <div className="brand">
            <span className="brand-mark">
              <Cpu size={22} />
            </span>
            <div>
              <strong>반도체 지식 허브</strong>
              <span>KNOWLEDGE HUB</span>
            </div>
          </div>
          <button
            className="icon-button sidebar-close"
            aria-label="탐색 메뉴 닫기"
            onClick={() => setSidebarOpen(false)}
          >
            <ChevronLeft size={18} />
          </button>
        </div>
        <button className="new-conversation-button" onClick={startNew}>
          <Plus size={18} />새 대화
        </button>
        <nav className="main-nav" aria-label="작업 공간">
          <button
            className={route.screen === "conversation" ? "active" : ""}
            aria-current={route.screen === "conversation" ? "page" : undefined}
            onClick={() =>
              go({ screen: "conversation", id: activeConversationId })
            }
          >
            <MessageSquare size={17} />
            대화
          </button>
          <button
            className={route.screen === "research" ? "active" : ""}
            aria-current={route.screen === "research" ? "page" : undefined}
            onClick={openResearch}
          >
            <Compass size={17} />
            외부 문헌 조사
          </button>
          <button
            className={route.screen === "personal-wiki" ? "active" : ""}
            aria-current={route.screen === "personal-wiki" ? "page" : undefined}
            onClick={() => go({ screen: "personal-wiki" })}
          >
            <BookOpen size={17} />
            개인 위키
          </button>
          {canReview && (
            <button
              className={route.screen === "review" ? "active" : ""}
              aria-current={route.screen === "review" ? "page" : undefined}
              onClick={() => go({ screen: "review" })}
            >
              <FileCheck2 size={17} />
              문헌 검토<span className="nav-tag">관리</span>
            </button>
          )}
        </nav>
        <div className="conversation-list-heading">
          <span>내 대화</span>
          <span>{chat.conversations.length}</span>
        </div>
        <div className="sidebar-search">
          <Search size={13} />
          <input
            aria-label="대화 목록 검색"
            placeholder="대화 찾기"
            value={conversationFilter}
            onChange={(event) => setConversationFilter(event.target.value)}
          />
        </div>
        <div className="sidebar-conversations">
          {chat.conversations
            .filter((conversation) =>
              conversation.title
                .toLocaleLowerCase()
                .includes(conversationFilter.toLocaleLowerCase()),
            )
            .map((conversation) => (
              <button
                className={
                  selectedId === conversation.id &&
                  route.screen === "conversation"
                    ? "active"
                    : ""
                }
                key={conversation.id}
                onClick={() =>
                  go({ screen: "conversation", id: conversation.id })
                }
                title={conversation.title}
              >
                <MessageSquare size={14} />
                <span>{conversation.title || "제목 없는 대화"}</span>
              </button>
            ))}
          {!chat.conversations.length && !chat.listError && (
            <p className="sidebar-empty">
              첫 질문을 보내면
              <br />
              대화가 여기에 저장됩니다.
            </p>
          )}
          {chat.listError && (
            <div className="sidebar-list-error">
              <ErrorNotice>{chat.listError}</ErrorNotice>
              <button
                className="text-button"
                onClick={() => void chat.refreshList()}
              >
                목록 다시 읽기
              </button>
            </div>
          )}
        </div>
        <footer className="sidebar-footer">
          <button
            className="settings-nav"
            onClick={() => setDialog("settings")}
          >
            <Settings2 size={17} />
            <span>설정</span>
          </button>
          <div className="user-menu">
            <span className="avatar">
              {user.username.slice(0, 1).toUpperCase()}
            </span>
            <span>
              <strong>{user.username}</strong>
              <small>
                {user.role === "reviewer"
                  ? "문헌 검토자"
                  : user.role === "admin"
                    ? "관리자"
                    : "개인 작업 공간"}
              </small>
            </span>
            <button
              className="icon-button"
              onClick={onLogout}
              aria-label="로그아웃"
            >
              <LogOut size={16} />
            </button>
          </div>
        </footer>
      </aside>
      <main className="main-workspace" id="main-workspace" tabIndex={-1}>
        {environment?.providerMode === "fixture" && (
          <div className="fixture-banner" role="status">
            평가 환경 · Fixture 응답입니다. 실제 생성 모델을 호출하지 않습니다.
          </div>
        )}
        {globalNotice && (
          <div className="global-notice">
            <InfoNotice onClose={() => setGlobalNotice(null)}>
              {globalNotice}
            </InfoNotice>
          </div>
        )}
        {route.screen === "conversation" && (
          <ConversationView
            controller={chat}
            onSource={source.open}
            onResearch={openResearch}
            onResources={() => setDialog("resources")}
            onSettings={() => setDialog("settings")}
          />
        )}
        {route.screen === "research" && (
          <ResearchView
            controller={research}
            onBack={() =>
              go({
                screen: "conversation",
                id: research.originId || activeConversationId,
              })
            }
          />
        )}
        {route.screen === "personal-wiki" && (
          <PersonalWikiView
            controller={wiki}
            selectedId={route.id}
            onSelect={(id) => go({ screen: "personal-wiki", id })}
            onConversation={(id) => go({ screen: "conversation", id })}
            onSource={source.open}
            onSettings={() => setDialog("settings")}
            onQuestion={questionWiki}
          />
        )}
        {route.screen === "review" &&
          (canReview ? (
            <ReviewView
              controller={review}
              onQuestion={questionDocument}
              onUpload={() => setDialog("upload")}
              onBatchUpload={canBatchUpload ? () => setDialog("batch-upload") : undefined}
              canIndex={canIndex}
            />
          ) : (
            <EmptyState
              icon={<FileCheck2 size={30} />}
              title="문헌 검토 권한이 필요합니다"
            >
              현재 계정에는 공용 문헌의 검토 권한이 없습니다. 개인 대화와 자료는
              계속 사용할 수 있습니다.
            </EmptyState>
          ))}
      </main>
      <SourcePanel controller={source} onQuestion={questionDocument} />
      {dialog === "resources" && (
        <ResourcePicker
          onClose={() => setDialog(null)}
          onConcept={chat.addConcept}
          onDocument={chat.attachDocument}
          onUpload={() => setDialog("upload")}
          selectedConceptIds={chat.state.draft.conceptIds}
          selectedDocumentIds={chat.state.draft.documentContextIds}
          sourceGroups={chat.state.draft.sourceGroups}
          onSourceGroups={(groups) => chat.setDraft({ sourceGroups: groups })}
        />
      )}
      {dialog === "upload" && (
        <UploadDialog
          onClose={() => setDialog(null)}
          onCreated={documentCreated}
        />
      )}
      {dialog === "batch-upload" && canBatchUpload && (
        <BatchUploadDialog onClose={() => setDialog(null)} onChanged={() => void review.refresh()} />
      )}
      {dialog === "settings" && (
        <SettingsDialog
          onClose={() => setDialog(null)}
          user={user}
          config={chat.state.run?.generationConfig}
        />
      )}
      {sidebarOpen && (
        <button
          className="mobile-sidebar-dismiss icon-button"
          onClick={() => setSidebarOpen(false)}
          aria-label="메뉴 닫기"
        >
          <X size={18} />
        </button>
      )}
    </div>
  );
}
export default function App() {
  const auth = useAuthController();
  if (auth.loading)
    return (
      <div className="session-loading">
        <Cpu size={32} />
        <Loading label="작업 공간을 복원하는 중" />
      </div>
    );
  return auth.user ? (
    <Workspace key={auth.user.id} user={auth.user} onLogout={auth.logout} />
  ) : (
    <LoginView busy={auth.busy} error={auth.error} onLogin={auth.login} />
  );
}
