import { useState } from "react";
import {
  ArrowLeft,
  ArrowUpRight,
  BookOpen,
  Check,
  Clock3,
  FileText,
  History,
  Pencil,
  Search,
  Settings2,
  Trash2,
  Undo2,
} from "lucide-react";
import type { Citation } from "../types/contracts";
import type { useWikiController } from "../controllers/useWikiController";
import { formatDate, organizationReason } from "../services/display";
import {
  Badge,
  EmptyState,
  ErrorNotice,
  InfoNotice,
  Loading,
  Modal,
} from "./components/Primitives";
import { SafeMarkdown } from "./components/SafeMarkdown";
import { CitationList } from "./components/Evidence";

interface Props {
  controller: ReturnType<typeof useWikiController>;
  selectedId?: string;
  onSelect: (id?: string) => void;
  onConversation: (id: string) => void;
  onSource: (citation: Citation) => void;
  onSettings: () => void;
  onQuestion: (text: string) => void;
}
export function PersonalWikiView({
  controller: wiki,
  selectedId,
  onSelect,
  onConversation,
  onSource,
  onSettings,
  onQuestion,
}: Props) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const page = selectedId && wiki.page?.id === selectedId ? wiki.page : null;
  return (
    <div className="feature-page">
      <header className="page-header">
        <div className="page-heading">
          <span className="header-icon">
            <BookOpen size={18} />
          </span>
          <div>
            <h1>개인 위키</h1>
            <p>대화에서 배운 내용을 나만의 지식으로</p>
          </div>
        </div>
        <button className="secondary-button small" onClick={onSettings}>
          <Settings2 size={15} />
          자동 정리 설정
        </button>
      </header>
      <div className="wiki-workspace">
        <aside className="wiki-list-panel">
          <div className="search-input">
            <Search size={16} />
            <input
              aria-label="개인 위키 검색"
              placeholder="제목과 내용 검색"
              value={wiki.query}
              onChange={(event) => wiki.setQuery(event.target.value)}
            />
          </div>
          <div className="list-caption">
            <span>나의 기록</span>
            <span>{wiki.listLoading ? "조회 중" : wiki.items.length}</span>
          </div>
          {wiki.items.map((item) => (
            <button
              className={`wiki-list-item ${item.id === selectedId ? "active" : ""}`}
              key={item.id}
              onClick={() => onSelect(item.id)}
              disabled={wiki.editing && item.id !== selectedId}
            >
              <FileText size={16} />
              <span>
                <strong>{item.title}</strong>
                <small>{item.summary || "요약 없음"}</small>
                <em>{formatDate(item.updatedAt)}</em>
              </span>
            </button>
          ))}
          {wiki.listLoading && <Loading label="개인 위키 목록 읽는 중" />}
          {!wiki.listLoading && !wiki.items.length && !wiki.error && (
            <p className="inline-empty">
              {wiki.query.trim()
                ? "검색 조건에 맞는 기록이 없습니다."
                : "아직 저장된 개인 위키가 없습니다."}
            </p>
          )}
        </aside>
        <main className="wiki-detail">
          <ErrorNotice>{wiki.error}</ErrorNotice>
          <InfoNotice>{wiki.notice}</InfoNotice>
          {wiki.lastDeleted && (
            <button
              className="text-button restore-deleted"
              disabled={wiki.busy}
              onClick={async () => {
                const id = await wiki.restoreDeleted();
                if (id) onSelect(id);
              }}
            >
              <Undo2 size={14} />
              삭제 되돌리기
            </button>
          )}
          {wiki.loading ? (
            <Loading />
          ) : page ? (
            <>
              <header className="wiki-page-title">
                <div>
                  <p className="eyebrow">PRIVATE KNOWLEDGE</p>
                  <h2>{page.title}</h2>
                  <p className="muted">
                    <Badge>나만 보기</Badge>{" "}
                    <span>
                      판본 {page.version} · {formatDate(page.updatedAt)}
                    </span>
                  </p>
                </div>
                {!wiki.editing && !page.restricted && (
                  <button
                    className="secondary-button small"
                    onClick={wiki.startEdit}
                  >
                    <Pencil size={14} />
                    편집
                  </button>
                )}
              </header>
              <div className="wiki-origin-note">
                <BookOpen size={16} />
                <p>
                  개인 위키는 대화에서 정리한 기록입니다. 독립적인 원문 근거로
                  취급하지 않으며, 공용 지식으로 공개되지 않습니다.
                </p>
              </div>
              {page.warnings?.map((warning, index) => (
                <div className="notice notice-warning" key={index}>
                  {warning}
                </div>
              ))}
              {!!page.conditions?.length && (
                <section className="wiki-conditions">
                  <h3>적용 조건</h3>
                  <ul>
                    {page.conditions.map((condition, index) => (
                      <li key={index}>{condition}</li>
                    ))}
                  </ul>
                </section>
              )}
              {!!page.limitations?.length && (
                <section className="wiki-conditions">
                  <h3>한계와 부족한 부분</h3>
                  <ul>
                    {page.limitations.map((limit, index) => (
                      <li key={index}>{limit}</li>
                    ))}
                  </ul>
                </section>
              )}
              {wiki.editing ? (
                <div className="wiki-editor">
                  {wiki.conflictPage && (
                    <div className="notice notice-warning">
                      <p>
                        판본 {wiki.conflictPage.version}이 먼저 저장되었습니다.
                        작성 중인 내용은 유지했습니다.
                      </p>
                      <details className="evidence-details">
                        <summary>최신 저장 내용 확인</summary>
                        <h3>{wiki.conflictPage.title}</h3>
                        <SafeMarkdown
                          content={wiki.conflictPage.content}
                          citations={wiki.conflictPage.citations}
                          onCitation={onSource}
                        />
                      </details>
                      <button
                        className="secondary-button small"
                        onClick={wiki.adoptConflictBase}
                      >
                        최신 판본 기준으로 계속 편집
                      </button>
                    </div>
                  )}
                  <label className="field">
                    제목
                    <input
                      value={wiki.title}
                      onChange={(event) => wiki.setTitle(event.target.value)}
                    />
                  </label>
                  <label className="field">
                    본문
                    <textarea
                      rows={18}
                      value={wiki.content}
                      onChange={(event) => wiki.setContent(event.target.value)}
                    />
                  </label>
                  <p className="fine-print">
                    판본 {page.version}을 기준으로 저장합니다. 다른 수정이 먼저
                    저장되었다면 입력 내용을 보존하고 충돌을 알립니다.
                  </p>
                  <div className="button-row">
                    <button
                      className="secondary-button"
                      onClick={wiki.cancelEdit}
                      disabled={wiki.busy}
                    >
                      편집 취소
                    </button>
                    <button
                      className="primary-button"
                      onClick={() => void wiki.save()}
                      disabled={
                        wiki.busy ||
                        !!wiki.conflictPage ||
                        !wiki.title.trim() ||
                        !wiki.content.trim()
                      }
                    >
                      <Check size={16} />
                      변경 저장
                    </button>
                  </div>
                </div>
              ) : page.restricted ? null : (
                <>
                  <SafeMarkdown
                    content={page.content}
                    citations={page.citations}
                    onCitation={onSource}
                  />
                  <section className="wiki-evidence">
                    <h3>연결된 원문</h3>
                    <CitationList
                      citations={page.citations || []}
                      onOpen={onSource}
                    />
                    {!page.citations?.length && (
                      <p className="inline-empty">
                        이 기록에 연결된 원문 근거가 없습니다.
                      </p>
                    )}
                  </section>
                  <section className="wiki-origins">
                    <h3>정리의 출발점</h3>
                    {(page.originMessages || []).map((origin, index) => (
                      <button
                        className="origin-link"
                        key={origin.messageId || origin.id || index}
                        disabled={!origin.conversationId}
                        onClick={() =>
                          origin.conversationId &&
                          onConversation(origin.conversationId)
                        }
                      >
                        <Clock3 size={15} />
                        <span>
                          {origin.content || `원래 대화 · 메시지 ${index + 1}`}
                        </span>
                        <ArrowUpRight size={14} />
                      </button>
                    ))}
                    {!page.originMessages?.length && (
                      <p className="inline-empty">
                        접근 가능한 원메시지가 없습니다.
                      </p>
                    )}
                  </section>
                  <details className="wiki-history">
                    <summary>
                      <History size={15} />
                      수정 이력 ({page.versions?.length || 0})
                    </summary>
                    {(page.versions || []).map((version, index) => (
                      <div key={version.id || index}>
                        <Badge>판본 {version.version}</Badge>
                        <span>{formatDate(version.createdAt)}</span>
                        <span>{version.origin || "변경 종류 미확인"}</span>
                      </div>
                    ))}
                  </details>
                  <footer className="wiki-page-actions">
                    <button
                      className="secondary-button"
                      onClick={() =>
                        onQuestion(
                          `${page.title}에 대해 이어서 살펴보고 싶습니다. 관련 원문과 적용 조건을 확인해 주세요.`,
                        )
                      }
                    >
                      이 주제로 질문 준비 <ArrowUpRight size={15} />
                    </button>
                    <div className="button-row">
                      <button
                        className="quiet-button small"
                        onClick={() => void wiki.undo()}
                        disabled={wiki.busy}
                      >
                        <Undo2 size={14} />
                        마지막 변경 되돌리기
                      </button>
                      <button
                        className="danger-button small"
                        onClick={() => setConfirmDelete(true)}
                        disabled={wiki.busy}
                      >
                        <Trash2 size={14} />
                        삭제
                      </button>
                    </div>
                  </footer>
                </>
              )}
            </>
          ) : (
            <div className="wiki-welcome">
              <span className="eyebrow">YOUR UNDERSTANDING, OVER TIME</span>
              <EmptyState
                icon={<BookOpen size={32} />}
                title="대화가 나만의 지식으로 남습니다"
              >
                유용한 설명과 사례, 조건과 근거를 개념별로 모아 보세요. 저장된
                기록을 선택하면 수정 이력과 원래 대화를 함께 확인할 수 있습니다.
              </EmptyState>
              <div className="wiki-welcome-cards">
                <div>
                  <Pencil size={20} />
                  <h3>내가 다듬는 기록</h3>
                  <p>설명을 수정하고 이전 판본으로 되돌릴 수 있습니다.</p>
                </div>
                <div>
                  <History size={20} />
                  <h3>출발점을 잃지 않게</h3>
                  <p>원문 근거와 대화의 연결을 함께 보관합니다.</p>
                </div>
              </div>
            </div>
          )}
          {!!wiki.jobs.length && (
            <section className="wiki-jobs">
              <h3>개인 위키 정리 작업</h3>
              <p className="fine-print">
                작업 종료와 지식 저장을 구분합니다. 내용을 남기지 않은 경우도
                결과에 표시합니다.
              </p>
              {wiki.jobs.slice(0, 10).map((job) => (
                <article key={job.id}>
                  <Badge tone={job.status === "failed" ? "red" : ""}>
                    {job.status}
                  </Badge>
                  <span>
                    {job.error
                      ? typeof job.error === "string"
                        ? job.error
                        : job.error.message || job.error.code
                      : job.result?.action === "skipped"
                        ? organizationReason(job.result.reason)
                        : job.result?.action
                          ? (
                              {
                                add: "새 기록 저장",
                                merge: "기존 기록에 병합",
                                correct: "기록 정정",
                              } as Record<string, string>
                            )[job.result.action] || job.result.action
                          : "저장 결과를 기다리는 중"}
                  </span>
                  {job.result?.pageId && job.result.action !== "skipped" && (
                    <button
                      className="text-button"
                      onClick={() => onSelect(job.result!.pageId)}
                    >
                      기록 보기
                    </button>
                  )}
                </article>
              ))}
            </section>
          )}
        </main>
      </div>
      {confirmDelete && page && (
        <Modal
          title="이 개인 위키를 삭제할까요?"
          onClose={() => setConfirmDelete(false)}
        >
          <div className="modal-body">
            <p>
              <strong>{page.title}</strong> 기록을 삭제합니다. 연결된
              원메시지에서 자동으로 다시 생성하지 않습니다.
            </p>
            <p className="muted">공용 문헌과 원래 대화는 유지됩니다.</p>
          </div>
          <footer className="modal-footer">
            <button
              className="secondary-button"
              onClick={() => setConfirmDelete(false)}
            >
              돌아가기
            </button>
            <button
              className="danger-button"
              disabled={wiki.busy}
              onClick={async () => {
                if (await wiki.remove()) {
                  setConfirmDelete(false);
                  onSelect();
                }
              }}
            >
              <Trash2 size={15} />
              삭제
            </button>
          </footer>
        </Modal>
      )}
      <button
        className="mobile-back-wiki text-button"
        onClick={() => onSelect()}
      >
        <ArrowLeft size={14} />
        기록 목록
      </button>
    </div>
  );
}
