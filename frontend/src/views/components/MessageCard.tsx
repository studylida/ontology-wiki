import {
  BookOpen,
  Check,
  ChevronDown,
  Copy,
  FileText,
  Sparkles,
} from "lucide-react";
import { useCallback, useLayoutEffect, useRef, useState } from "react";
import type {
  Citation,
  Message,
  Relation,
  SourceView,
} from "../../types/contracts";
import type { ActiveRun } from "../../services/chatState";
import { useRunDetailsController } from "../../controllers/useRunDetailsController";
import { formatCount, formatDuration } from "../../services/display";
import {
  isTerminal,
  splitWiki,
  WIKI_SECTIONS,
} from "../../services/conversationService";
import { Badge, ErrorNotice } from "./Primitives";
import { SafeMarkdown } from "./SafeMarkdown";
import {
  CitationList,
  GroupCoverageList,
  RelationCards,
  SourceViewCards,
} from "./Evidence";

interface Props {
  message: Message;
  run?: ActiveRun | null;
  onOpen: (citation: Citation) => void;
  onRelation: (relation: Relation) => void;
  onCompare: (views: SourceView[]) => void;
  onOrganize: (messageId: string) => void;
  onRetry: () => void;
  onFirstVisible: (runId: string) => void;
}
export function MessageCard({
  message,
  run,
  onOpen,
  onRelation,
  onCompare,
  onOrganize,
  onRetry,
  onFirstVisible,
}: Props) {
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState<string | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [citationScan, setCitationScan] = useState<{ content: string; key: string; ids: string[] } | null>(null);
  const citationKey = JSON.stringify(message.citations.map((citation) => citation.id));
  const onCitationsFound = useCallback((ids: string[]) => {
    setCitationScan({ content: message.content, key: citationKey, ids });
  }, [message.content, citationKey]);
  const historical = useRunDetailsController(
    message.runId,
    detailsOpen,
    !!run?.metrics,
  );
  const info = run || historical.run;
  const observed = useRef<string | null>(null);
  const hasText = message.role === "assistant" && !!message.content.trim();
  useLayoutEffect(() => {
    if (!hasText || !message.runId || observed.current === message.runId)
      return;
    const runId = message.runId;
    let second = 0;
    let delivered = false;
    observed.current = runId;
    // DOM commit + two animation frames is a client observation, not a paint-time guarantee.
    const first = requestAnimationFrame(() => {
      second = requestAnimationFrame(() => {
        delivered = true;
        onFirstVisible(runId);
      });
    });
    return () => {
      cancelAnimationFrame(first);
      cancelAnimationFrame(second);
      if (!delivered) observed.current = null;
    };
  }, [hasText, message.runId, onFirstVisible]);
  if (message.role === "user")
    return (
      <article
        className="user-message"
        id={`message-${message.id}`}
        aria-label="내 질문"
      >
        <div>{message.content}</div>
      </article>
    );
  const parts = splitWiki(message.content);
  const terminal = isTerminal(message.status);
  const citedIds = terminal && citationScan?.content === message.content && citationScan.key === citationKey
    ? new Set(citationScan.ids) : undefined;
  const partial = ["failed", "cancelled", "interrupted"].includes(
    message.status,
  );
  const usage = message.usage || info?.usage;
  const fixture =
    usage?.source === "fixture" ||
    usage?.costStatus === "fixture" ||
    info?.generationConfig?.providerMode === "fixture";
  const generationCalls =
    usage?.components?.filter(
      (component) => component.operation === "answer_generation",
    ) || [];
  const distinct = (values: (string | null | undefined)[]) =>
    [...new Set(values.filter((value): value is string => !!value))].join(
      " · ",
    );
  const generationProvider = distinct(
    generationCalls.map((component) => component.provider),
  );
  const requestedModel =
    distinct(generationCalls.map((component) => component.requestedModel)) ||
    info?.generationConfig?.model;
  const returnedModel = distinct(
    generationCalls
      .filter((component) => component.modelSource === "provider")
      .map((component) => component.model),
  );
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setCopyError(null);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopyError(
        "복사를 허용하지 않는 브라우저입니다. 답변 텍스트를 선택해 복사해 주세요.",
      );
    }
  };
  const shared = { onOpen, onCompare };
  return (
    <article
      className={`assistant-message ${partial ? "is-partial" : ""}`}
      id={`message-${message.id}`}
      aria-label={`${message.responseMode === "analysis" ? "분석" : "위키"} 답변`}
    >
      <header className="message-header">
        <span className="assistant-mark">
          <Sparkles size={15} />
        </span>
        <strong>지식 허브</strong>
        <Badge tone="blue">
          {message.responseMode === "analysis" ? "분석" : "위키"}
        </Badge>
        {message.extended && <Badge>Extended</Badge>}
        {fixture && <Badge tone="amber">Fixture · 실제 모델 응답 아님</Badge>}
        {partial && (
          <Badge tone="amber">
            {message.status === "cancelled"
              ? "중단됨 · 부분 응답"
              : "완료되지 않은 응답"}
          </Badge>
        )}
      </header>
      {terminal && message.content && !!message.citations.length && (
        <div hidden aria-hidden="true">
          <SafeMarkdown content={message.content} citations={message.citations} onCitationsFound={onCitationsFound} />
        </div>
      )}
      {message.content ? (
        message.responseMode === "analysis" ? (
          <div className="answer-body analysis-answer">
            <SafeMarkdown
              content={message.content}
              citations={message.citations}
              onCitation={onOpen}
            />
            <SourceViewCards views={message.sourceViews} {...shared} />
            {message.relations.length > 0 && (
              <section className="answer-section">
                <h3>관련 개념과 근거</h3>
                <RelationCards
                  relations={message.relations}
                  onOpen={onOpen}
                  onFollowup={onRelation}
                />
              </section>
            )}
            <section className="answer-section">
              <h3>출처</h3>
              <CitationList citations={message.citations} onOpen={onOpen} citedIds={citedIds} />
              <GroupCoverageList
                summary={info?.retrievalSummary}
                groups={info?.request?.sourceGroups}
                citations={message.citations}
              />
              {terminal && !message.citations.length && (
                <p className="inline-empty">
                  이 답변에 연결된 원문 출처가 없습니다.
                </p>
              )}
            </section>
          </div>
        ) : (
          <div className="answer-body wiki-answer">
            {WIKI_SECTIONS.map((title, index) => (
              <section className="answer-section" key={title}>
                <h3>
                  <span className="section-number">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  {title}
                </h3>
                {parts[index] && (
                  <SafeMarkdown
                    content={parts[index]}
                    citations={message.citations}
                    onCitation={onOpen}
                  />
                )}
                {index === 2 && (
                  <SourceViewCards views={message.sourceViews} {...shared} />
                )}
                {index === 3 && (
                  <RelationCards
                    relations={message.relations}
                    onOpen={onOpen}
                    onFollowup={onRelation}
                  />
                )}
                {index === 4 && (
                  <>
                    <CitationList
                      citations={message.citations}
                      onOpen={onOpen}
                      citedIds={citedIds}
                    />
                    <GroupCoverageList
                      summary={info?.retrievalSummary}
                      groups={info?.request?.sourceGroups}
                      citations={message.citations}
                    />
                  </>
                )}
                {!parts[index] &&
                  !(index === 2 && message.sourceViews.length) &&
                  !(index === 3 && message.relations.length) &&
                  !(index === 4 && message.citations.length) && (
                    <p className="inline-empty">
                      {terminal
                        ? index === 3
                          ? "이 답변에 근거가 연결된 관계가 제공되지 않았습니다."
                          : index === 4
                            ? "이 답변에 연결된 원문 출처가 없습니다."
                            : "이 항목의 내용이 응답에 제공되지 않았습니다."
                        : "응답이 도착하면 여기에 이어집니다."}
                    </p>
                  )}
              </section>
            ))}
          </div>
        )
      ) : (
        <p className="awaiting-answer">
          {partial
            ? "저장된 답변 본문이 없습니다."
            : terminal
              ? "저장된 답변 내용이 없습니다."
              : "질문에 필요한 근거와 문맥을 확인하고 있습니다."}
        </p>
      )}
      {!!message.warnings.length && (
        <div className="answer-warnings">
          {message.warnings.map((warning, index) => (
            <p key={index}>{warning}</p>
          ))}
        </div>
      )}
      {partial && (
        <div className="partial-note">
          <span>
            지금까지 수신한 내용입니다. 완성된 답변으로 표시하지 않습니다.
          </span>
          {message.runId && (
            <button className="text-button" onClick={onRetry}>
              새 시도 준비
            </button>
          )}
        </div>
      )}
      <ErrorNotice>{copyError}</ErrorNotice>
      {terminal && (
        <footer className="message-footer">
          <div className="message-actions">
            {message.content && (
              <button
                className="quiet-button small"
                onClick={() => void copy()}
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? "복사됨" : "복사"}
              </button>
            )}
            {message.status === "completed" && !fixture && (
              <button
                className="quiet-button small"
                onClick={() => onOrganize(message.id)}
              >
                <BookOpen size={14} /> 개인 위키 정리
              </button>
            )}
          </div>
          <details
            className="run-details"
            onToggle={(event) => setDetailsOpen(event.currentTarget.open)}
          >
            <summary>
              <FileText size={13} /> 실행 정보 <ChevronDown size={12} />
            </summary>
            <dl>
              <div>
                <dt>생성 공급자</dt>
                <dd>{fixture ? "fixture" : generationProvider || "미확인"}</dd>
              </div>
              <div>
                <dt>요청 생성 모델</dt>
                <dd>{requestedModel || "미확인"}</dd>
              </div>
              <div>
                <dt>공급자 반환 모델</dt>
                <dd>
                  {fixture
                    ? "해당 없음 · fixture"
                    : returnedModel || "공급자 미반환"}
                </dd>
              </div>
              <div>
                <dt>요청 Effort</dt>
                <dd>
                  {usage?.requestedEffort ||
                    info?.generationConfig?.effort ||
                    "미확인"}
                </dd>
              </div>
              <div>
                <dt>공급자 반환 Effort</dt>
                <dd>
                  {fixture
                    ? "해당 없음 · fixture"
                    : usage?.effectiveEffort || "공급자 미반환"}
                </dd>
              </div>
              <div>
                <dt>요청 / 반환 서비스 등급</dt>
                <dd>
                  {fixture
                    ? "해당 없음 · fixture"
                    : `${usage?.requestedServiceTier || "미확인"} / ${usage?.serviceTier || "공급자 미반환"}`}
                </dd>
              </div>
              <div>
                <dt>호출 수</dt>
                <dd>{formatCount(usage?.calls)}</dd>
              </div>
              <div>
                <dt>전체 입력 / 출력 토큰</dt>
                <dd>
                  {formatCount(usage?.inputTokens)} /{" "}
                  {formatCount(usage?.outputTokens)}
                </dd>
              </div>
              <div>
                <dt>확인 가능한 비용</dt>
                <dd>
                  {usage?.costUsd == null
                    ? "미확인"
                    : `$${usage.costUsd.toFixed(6)}`}
                  {usage?.costUsd == null &&
                  usage?.knownCostUsd != null &&
                  usage.knownCostUsd > 0
                    ? ` · 확인된 일부 $${usage.knownCostUsd.toFixed(6)}`
                    : ""}
                  {usage?.costStatus === "estimated"
                    ? " (단가 기준 추정)"
                    : usage?.costStatus === "fixture"
                      ? " (fixture)"
                      : ""}
                </dd>
              </div>
              <div>
                <dt>검색 / 생성</dt>
                <dd>
                  {formatDuration(info?.metrics?.retrievalMs)} /{" "}
                  {formatDuration(info?.metrics?.generationMs)}
                </dd>
              </div>
              <div>
                <dt>첫 실제 텍스트 · 서버</dt>
                <dd>
                  {fixture
                    ? "해당 없음 · fixture"
                    : formatDuration(info?.metrics?.firstTextMs)}
                </dd>
              </div>
              <div>
                <dt>첫 화면 반영 · 클라이언트</dt>
                <dd>
                  {formatDuration(info?.metrics?.clientFirstVisibleTextMs)}
                  {fixture ? " (fixture 관측)" : ""}
                </dd>
              </div>
              <div>
                <dt>전체 시간</dt>
                <dd>{formatDuration(info?.metrics?.totalMs)}</dd>
              </div>
              {message.runId && (
                <div>
                  <dt>실행 ID</dt>
                  <dd className="mono">{message.runId}</dd>
                </div>
              )}
            </dl>
            {!!usage?.components?.length && (
              <details className="usage-breakdown">
                <summary>호출별 모델·토큰·비용</summary>
                <dl>
                  {usage.components.map((component, index) => (
                    <div key={index}>
                      <dt>
                        {component.operation === "answer_generation"
                          ? "답변 생성"
                          : component.operation === "query_embedding"
                            ? "검색 임베딩"
                            : component.operation || "호출 종류 미확인"}
                      </dt>
                      <dd>
                        <span>{component.model || "모델 미확인"}</span>
                        <br />
                        {component.operation === "query_embedding"
                          ? `입력 ${formatCount(component.inputTokens)} 토큰`
                          : `입력 ${formatCount(component.inputTokens)} / 출력 ${formatCount(component.outputTokens)} 토큰`}
                        <br />
                        {component.costUsd == null
                          ? "비용 미확인"
                          : `$${component.costUsd.toFixed(6)} (단가 기준 추정)`}
                      </dd>
                    </div>
                  ))}
                </dl>
              </details>
            )}
            <ErrorNotice>{historical.error}</ErrorNotice>
            <p className="fine-print">
              미확인 사용량과 비용은 0으로 간주하지 않습니다. 추정 금액은 청구
              내역과 다를 수 있습니다. 화면 반영 시간은 이 브라우저의 관측값이며
              정확한 paint 시각을 보장하지 않습니다.
            </p>
          </details>
        </footer>
      )}
    </article>
  );
}
