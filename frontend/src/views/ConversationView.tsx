import { useEffect, useLayoutEffect, useRef, useState } from "react";
import {
  ArrowDown,
  ArrowRight,
  ArrowUp,
  BookOpen,
  ChevronDown,
  Compass,
  FileText,
  GitBranch,
  Lightbulb,
  Link2,
  Plus,
  ScanSearch,
  SlidersHorizontal,
  Square,
  X,
} from "lucide-react";
import type { Citation } from "../types/contracts";
import type { useConversationController } from "../controllers/useConversationController";
import { MessageCard } from "./components/MessageCard";
import { replyFollowScrollTop } from "./components/replyScroll";
import {
  Badge,
  ErrorNotice,
  InfoNotice,
  Loading,
  Modal,
} from "./components/Primitives";

export type ConversationController = ReturnType<
  typeof useConversationController
>;
interface Props {
  controller: ConversationController;
  onSource: (citation: Citation) => void;
  onResearch: () => void;
  onResources: () => void;
  onSettings: () => void;
}
const suggestions = [
  {
    icon: BookOpen,
    title: "개념부터 차근차근",
    text: "열압착 본딩의 원리와 적용 조건을 설명해 줘.",
  },
  {
    icon: GitBranch,
    title: "공정 사이의 연결",
    text: "TSV 공정과 웨이퍼 박막화는 어떤 순서와 조건으로 연결돼?",
  },
  {
    icon: SlidersHorizontal,
    title: "조건을 두고 비교",
    text: "HBM 적층에서 접합 방식별 차이와 적용 한계를 비교해 줘.",
  },
  {
    icon: ScanSearch,
    title: "출처의 관점 살피기",
    text: "보유 자료의 기업·저자별 관점에서 식각과 증착의 역할을 비교해 줘.",
  },
];
export function ConversationView({
  controller: chat,
  onSource,
  onResearch,
  onResources,
  onSettings,
}: Props) {
  const { state } = chat;
  const scroll = useRef<HTMLDivElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const pinned = useRef(true);
  const [awayFromBottom, setAwayFromBottom] = useState(false);
  const scrollTimer = useRef<number | null>(null);
  const [showScope, setShowScope] = useState(false);
  const latestMessage = state.messages.at(-1);
  const followPosition = () =>
    scroll.current
      ? replyFollowScrollTop(scroll.current, latestMessage?.id)
      : 0;
  useLayoutEffect(() => {
    const element = scroll.current;
    return () => {
      if (element) chat.saveScroll(state.id, element.scrollTop);
    };
  }, [state.id, chat.saveScroll]);
  useLayoutEffect(() => {
    if (!scroll.current) return;
    scroll.current.scrollTop = state.draft.scrollTop ?? followPosition();
    pinned.current =
      Math.abs(scroll.current.scrollTop - followPosition()) < 100;
    setAwayFromBottom(!pinned.current);
  }, [state.id, state.loading]);
  useLayoutEffect(() => {
    if (pinned.current && scroll.current) {
      scroll.current.scrollTop = followPosition();
      setAwayFromBottom(false);
    }
  }, [latestMessage?.id, latestMessage?.content]);
  useEffect(
    () => () => {
      if (scrollTimer.current) clearTimeout(scrollTimer.current);
    },
    [],
  );
  useEffect(
    () => () => chat.suspendVisibleMeasurement(),
    [chat.suspendVisibleMeasurement],
  );
  const trackScroll = () => {
    const element = scroll.current;
    if (!element) return;
    pinned.current = Math.abs(element.scrollTop - followPosition()) < 100;
    setAwayFromBottom(!pinned.current);
    if (scrollTimer.current) clearTimeout(scrollTimer.current);
    const top = element.scrollTop;
    const id = state.id;
    scrollTimer.current = window.setTimeout(
      () => chat.saveScroll(id, top),
      160,
    );
  };
  const submit = () => {
    if (!chat.busy && state.draft.text.trim()) {
      pinned.current = true;
      void chat.send();
    }
  };
  const selectedCount =
    state.draft.documentContextIds.length +
    state.draft.sourceRevisionIds.length +
    state.draft.attachmentIds.length +
    state.draft.conceptIds.length +
    state.draft.sourceGroups.length +
    (state.draft.aspect ? 1 : 0);
  const lastUser = [...state.messages]
    .reverse()
    .find((message) => message.role === "user");
  const title =
    chat.conversations.find((conversation) => conversation.id === state.id)
      ?.title || state.title;
  return (
    <div className="conversation-page">
      <header className="page-header">
        <div className="page-heading">
          <span className="header-icon">
            <BookOpen size={18} />
          </span>
          <div>
            <h1>{state.id ? title : "새 대화"}</h1>
            <p>개념과 근거를 한 흐름으로</p>
          </div>
        </div>
        <div className="header-actions">
          {state.id && (
            <button
              className={`quiet-button small auto-wiki-button ${!state.autoWiki ? "is-off" : ""}`}
              onClick={() => void chat.toggleAutoWiki(!state.autoWiki)}
              title="전체 자동 정리가 켜져 있을 때 이 대화의 포함 여부를 설정합니다"
            >
              <BookOpen size={14} />
              자동 정리 {state.autoWiki ? "허용" : "제외"}
            </button>
          )}
          <button className="secondary-button small" onClick={onResearch}>
            <Compass size={16} />
            <span>외부 문헌 조사</span>
          </button>
          <button
            className="icon-button"
            onClick={onSettings}
            aria-label="설정"
          >
            <SlidersHorizontal size={18} />
          </button>
        </div>
      </header>
      <div className="conversation-scroll" ref={scroll} onScroll={trackScroll}>
        <div className="conversation-width">
          {state.loading ? (
            <Loading label="대화와 저장된 답변을 복원하는 중" />
          ) : state.messages.length === 0 ? (
            <section className="welcome">
              <div className="welcome-symbol">
                <span>
                  <BookOpen size={30} />
                </span>
                <i />
                <i />
              </div>
              <p className="eyebrow">A SPACE FOR CONNECTED UNDERSTANDING</p>
              <h2>
                반도체 지식,
                <br />
                <em>근거와 함께 이어서.</em>
              </h2>
              <p className="welcome-description">
                궁금한 개념에서 시작해 보세요.
                <br />
                원문과 관계, 서로 다른 관점을 같은 대화에서 살펴볼 수 있습니다.
              </p>
              <div className="suggestion-grid">
                {suggestions.map(({ icon: Icon, title, text }) => (
                  <button
                    key={title}
                    className="suggestion-card"
                    onClick={() => {
                      chat.setDraft({ text });
                      composer.current?.focus();
                    }}
                  >
                    <Icon size={18} />
                    <strong>{title}</strong>
                    <span>{text}</span>
                    <ArrowRight size={15} />
                  </button>
                ))}
              </div>
              <p className="welcome-tip">
                <Lightbulb size={14} /> 질문 예시를 누르면 입력창에 담깁니다.
                보내기 전 수정할 수 있어요.
              </p>
            </section>
          ) : (
            <div className="message-list">
              {state.messages.map((message, index) => (
                <MessageCard
                  key={message.id}
                  message={message}
                  run={state.run?.id === message.runId ? state.run : null}
                  onOpen={onSource}
                  onRelation={chat.relationFollowup}
                  onCompare={chat.compareViews}
                  onOrganize={(id) => void chat.organize(id)}
                  onFirstVisible={chat.reportFirstVisible}
                  onRetry={() =>
                    chat.setFollowup({
                      title: "새 시도로 질문",
                      overrides: { retryOfRunId: message.runId },
                      text:
                        [...state.messages.slice(0, index)]
                          .reverse()
                          .find((item) => item.role === "user")?.content || "",
                    })
                  }
                />
              ))}
            </div>
          )}
          {chat.busy && state.progress && (
            <div className="stream-status" role="status">
              <span className="status-dot" />
              {state.progress}
            </div>
          )}
          {state.connection === "disconnected" && state.run && (
            <div className="notice notice-warning">
              <span>연결이 끊어졌습니다. 수신한 내용은 유지됩니다.</span>
              <button className="text-button" onClick={chat.reconnect}>
                같은 실행에 다시 연결
              </button>
            </div>
          )}
          <ErrorNotice
            action={
              state.retryRequest ? (
                <button className="text-button" onClick={chat.retryCreation}>
                  같은 요청 확인·재시도
                </button>
              ) : undefined
            }
          >
            {state.error}
          </ErrorNotice>
          <InfoNotice onClose={() => chat.setNotice(null)}>
            {chat.notice}
          </InfoNotice>
          {!!state.messages.length && !chat.busy && (
            <div className="continue-research">
              <Compass size={17} />
              <span>보유 자료로 부족한 근거가 있나요?</span>
              <button className="text-button" onClick={onResearch}>
                외부 문헌 찾아보기 <ArrowRight size={13} />
              </button>
              {lastUser && (
                <button
                  className="text-button"
                  onClick={() =>
                    chat.setFollowup({
                      title: "보유 자료에서 추가 탐색",
                      text: lastUser.content,
                      overrides: { extended: true },
                    })
                  }
                >
                  내부 추가 탐색
                </button>
              )}
            </div>
          )}
        </div>
      </div>
      {awayFromBottom && (
        <button
          className="jump-latest"
          onClick={() => {
            if (scroll.current) {
              pinned.current = true;
              scroll.current.scrollTop = followPosition();
              setAwayFromBottom(false);
            }
          }}
        >
          <ArrowDown size={15} /> 최신 응답
        </button>
      )}
      <div className="composer-wrap">
        <div className="composer-inner">
          {!!selectedCount && (
            <div className="selected-materials">
              {state.draft.conceptIds.map((id) => (
                <span className="material-chip" key={id} title={id}>
                  <GitBranch size={12} />
                  {state.draft.conceptLabels[id] || "개념 · 이름 미확인"}
                  <button
                    aria-label={`${state.draft.conceptLabels[id] || "복원한 개념"} 선택 해제`}
                    onClick={() =>
                      chat.setDraft({
                        conceptIds: state.draft.conceptIds.filter(
                          (value) => value !== id,
                        ),
                      })
                    }
                  >
                    <X size={12} />
                  </button>
                </span>
              ))}
              {[
                ...new Set([
                  ...state.draft.documentContextIds,
                  ...state.draft.sourceRevisionIds,
                ]),
              ].map((id) => (
                <span
                  className="material-chip"
                  key={id}
                  title={
                    state.draft.documentContextIds.includes(id)
                      ? "현재 대화에서 읽는 자료 · 공용 색인 반영과 별개"
                      : "공용 검색 범위를 좁히는 자료"
                  }
                >
                  <FileText size={12} />
                  {state.draft.sourceLabels[id] || "문헌 · 제목 미확인"}
                  <button
                    aria-label={`${state.draft.sourceLabels[id] || "복원한 문헌"} 자료 해제`}
                    onClick={() => chat.removeDocument(id)}
                  >
                    <X size={12} />
                  </button>
                </span>
              ))}
              {state.draft.sourceGroups.map((group) => (
                <span className="material-chip" key={group.groupId}>
                  출처:{" "}
                  {[group.publisherId, group.sourceType]
                    .filter(Boolean)
                    .join(" · ") || group.groupId}
                  <button
                    aria-label="출처 그룹 해제"
                    onClick={() =>
                      chat.setDraft({
                        sourceGroups: state.draft.sourceGroups.filter(
                          (value) => value.groupId !== group.groupId,
                        ),
                      })
                    }
                  >
                    <X size={12} />
                  </button>
                </span>
              ))}
              {state.draft.aspect && (
                <span className="material-chip">
                  관점: {state.draft.aspect}
                  <button
                    aria-label="관점 조건 해제"
                    onClick={() => chat.setDraft({ aspect: null })}
                  >
                    <X size={12} />
                  </button>
                </span>
              )}
              {state.draft.attachmentIds.length > 0 && (
                <span className="material-chip">
                  <Link2 size={12} />
                  조사 문헌 {state.draft.attachmentIds.length}개
                  <button
                    aria-label="조사 문헌 첨부 해제"
                    onClick={() => chat.setDraft({ attachmentIds: [] })}
                  >
                    <X size={12} />
                  </button>
                </span>
              )}
              <button
                className="text-button small"
                onClick={() => setShowScope(!showScope)}
              >
                자료 범위 <ChevronDown size={12} />
              </button>
            </div>
          )}
          {showScope && (
            <div className="scope-note">
              선택 원문은 현재 질문에 직접 사용됩니다. 승인과 공용 검색 반영은
              별개입니다. 개념 선택은 질문 맥락을 보강합니다.
              {state.draft.sourceGroups.length > 0 && (
                <p>
                  출처 그룹 {state.draft.sourceGroups.length}개로 검색 범위가
                  설정되어 있습니다.{" "}
                  <button
                    className="text-button"
                    onClick={() =>
                      chat.setDraft({ sourceGroups: [], aspect: null })
                    }
                  >
                    범위 해제
                  </button>
                </p>
              )}
            </div>
          )}
          <div className={`composer ${chat.busy ? "is-busy" : ""}`}>
            <textarea
              ref={composer}
              aria-label="질문 입력"
              placeholder="개념, 공정, 비교하고 싶은 조건을 질문해 보세요"
              value={state.draft.text}
              rows={2}
              onChange={(event) => chat.setDraft({ text: event.target.value })}
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey &&
                  !event.nativeEvent.isComposing
                ) {
                  event.preventDefault();
                  submit();
                }
              }}
            />
            <div className="composer-toolbar">
              <div className="composer-options">
                <button
                  className="icon-button add-material"
                  aria-label="자료 또는 개념 추가"
                  onClick={onResources}
                >
                  <Plus size={19} />
                </button>
                <div
                  className="mode-toggle"
                  role="group"
                  aria-label="다음 답변 형식"
                >
                  <button
                    aria-pressed={state.draft.responseMode === "wiki"}
                    className={
                      state.draft.responseMode === "wiki" ? "active" : ""
                    }
                    onClick={() => chat.setDraft({ responseMode: "wiki" })}
                  >
                    <BookOpen size={14} />
                    위키
                  </button>
                  <button
                    aria-pressed={state.draft.responseMode === "analysis"}
                    className={
                      state.draft.responseMode === "analysis" ? "active" : ""
                    }
                    onClick={() => chat.setDraft({ responseMode: "analysis" })}
                  >
                    <SlidersHorizontal size={14} />
                    분석
                  </button>
                </div>
                <button
                  className={`extended-toggle ${state.draft.extended ? "active" : ""}`}
                  aria-pressed={state.draft.extended}
                  onClick={() =>
                    chat.setDraft({ extended: !state.draft.extended })
                  }
                  title="다음 질문에서 보유 자료를 추가 탐색합니다. 외부 조사는 실행하지 않습니다."
                >
                  <ScanSearch size={15} />
                  Extended<span>{state.draft.extended ? "ON" : "OFF"}</span>
                </button>
              </div>
              {chat.busy ? (
                <button
                  className="send-button stop-button"
                  aria-label="답변 생성 중단"
                  onClick={() => void chat.cancel()}
                  disabled={state.starting || state.connection === "cancelling"}
                >
                  <Square size={17} fill="currentColor" />
                </button>
              ) : (
                <button
                  className="send-button"
                  aria-label="질문 보내기"
                  onClick={submit}
                  disabled={!state.draft.text.trim() || state.loading}
                >
                  <ArrowUp size={20} />
                </button>
              )}
            </div>
          </div>
          <div className="composer-hint">
            <span>다음 답변에만 적용 · Shift + Enter 줄바꿈</span>
            <span>중요한 내용은 원문과 적용 조건을 확인하세요.</span>
          </div>
        </div>
      </div>
      {chat.followup && (
        <Modal
          title={chat.followup.title}
          eyebrow="같은 대화에서 이어가기"
          onClose={() => chat.setFollowup(null)}
        >
          <div className="modal-body">
            <p className="muted">
              입력창의 초안은 그대로 보관합니다. 이 질문은 별도의 후속 메시지로
              전송됩니다.
            </p>
            <label className="field">
              후속 질문
              <textarea
                rows={6}
                value={chat.followup.text}
                onChange={(event) =>
                  chat.setFollowup({
                    ...chat.followup!,
                    text: event.target.value,
                  })
                }
              />
            </label>
            <div className="followup-settings">
              <Badge tone="blue">
                {(chat.followup.overrides?.responseMode ||
                  state.draft.responseMode) === "wiki"
                  ? "위키"
                  : "분석"}
              </Badge>
              <Badge>
                Extended{" "}
                {(chat.followup.overrides?.extended ?? state.draft.extended)
                  ? "ON"
                  : "OFF"}
              </Badge>
              {chat.followup.overrides?.sourceGroups && (
                <Badge>
                  선택 출처 그룹 {chat.followup.overrides.sourceGroups.length}개
                </Badge>
              )}
            </div>
            {state.draft.text && (
              <div className="preserved-draft">
                <strong>보관되는 입력 초안</strong>
                <p>{state.draft.text}</p>
              </div>
            )}
          </div>
          <footer className="modal-footer">
            <button
              className="secondary-button"
              onClick={() => chat.setFollowup(null)}
            >
              돌아가기
            </button>
            <button
              className="primary-button"
              disabled={chat.busy || !chat.followup.text.trim()}
              onClick={() => {
                pinned.current = true;
                void chat.send(
                  chat.followup!.text,
                  chat.followup!.overrides,
                  true,
                );
              }}
            >
              후속 질문 보내기 <ArrowUp size={16} />
            </button>
          </footer>
        </Modal>
      )}
    </div>
  );
}
