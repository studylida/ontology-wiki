import { useState } from "react";
import {
  ArrowUpRight,
  BookOpen,
  ChevronDown,
  GitBranch,
  Search,
  Users,
} from "lucide-react";
import type {
  Citation,
  Relation,
  RetrievalSummary,
  SourceGroup,
  SourceView,
} from "../../types/contracts";
import { useSourceViewsController } from "../../controllers/useSourceController";
import { documentFormLabel, formatDate } from "../../services/display";
import { Badge, ErrorNotice, Loading } from "./Primitives";

export function GroupCoverageList({
  summary,
  groups = [],
  citations,
}: {
  summary?: RetrievalSummary | null;
  groups?: SourceGroup[];
  citations: Citation[];
}) {
  if (!summary?.groupCoverage?.length) return null;
  return (
    <div className="group-coverage">
      <h4>검색 당시 출처별 근거 범위</h4>
      <div>
        {summary.groupCoverage.map((coverage) => {
          const group = groups.find(
            (group) => group.groupId === coverage.groupId,
          );
          const citation =
            group &&
            citations.find(
              (citation) =>
                (!group.publisherId ||
                  citation.publisherId === group.publisherId) &&
                (!group.sourceType || citation.sourceType === group.sourceType),
            );
          const label =
            citation?.publisher || group?.publisherId || coverage.groupId;
          return (
            <article key={coverage.groupId}>
              <strong>
                {label}
                {group?.sourceType ? ` · ${group.sourceType}` : ""}
              </strong>
              <Badge tone={coverage.status === "missing" ? "amber" : "blue"}>
                {coverage.status === "missing"
                  ? "근거 부족"
                  : `근거 구간 ${coverage.hitCount}개`}
              </Badge>
              {coverage.status === "missing" && (
                <p>선택한 범위에서 이 질문에 사용할 근거를 찾지 못했습니다.</p>
              )}
              {!!coverage.missingAspects?.length && (
                <p>부족한 측면: {coverage.missingAspects.join(" · ")}</p>
              )}
              {coverage.reason && <p>{coverage.reason}</p>}
            </article>
          );
        })}
      </div>
      <p className="fine-print">
        구간 수는 질문의 의미 정확성을 평가한 점수가 아닙니다.
      </p>
    </div>
  );
}

export function CitationList({
  citations,
  onOpen,
  compact = false,
  citedIds,
}: {
  citations: Citation[];
  onOpen: (citation: Citation) => void;
  compact?: boolean;
  citedIds?: ReadonlySet<string>;
}) {
  if (!citations.length) return null;
  const indexed = citations.map((citation, index) => ({ citation, number: index + 1 }));
  const groupKey = (citation: Citation) => citation.lineageKey
    ? `lineage:${citation.lineageKey}`
    : `revision:${citation.sourceRevisionId || citation.id}`;
  const groupCount = new Set(citations.map(groupKey)).size;
  const revisionCount = new Set(citations.map((citation) => citation.sourceRevisionId || citation.id)).size;
  const renderGroups = (items: typeof indexed) => {
    const groups = new Map<string, typeof indexed>();
    items.forEach((item) => {
      const key = groupKey(item.citation);
      const entries = groups.get(key) || [];
      entries.push(item);
      groups.set(key, entries);
    });
    return [...groups.entries()].map(([key, entries]) => {
        const first = entries[0].citation;
        const versions = new Set(entries.map(({ citation }) => citation.sourceRevisionId || citation.id)).size;
        return (
          <details className="citation-group" key={key}>
            <summary>
              <strong>{first.title || "제목 미확인 문헌"}</strong>
              <span>
                {first.historicalMetadata ? "과거 등록 정보 · " : ""}
                {versions > 1 ? `자료 판본 ${versions}개` : documentFormLabel(first.documentForm, first.sourceType)} · {""}
                {first.publisher ? `${first.publisher} · ` : ""}{entries.length}개 구간
              </span>
            </summary>
            <div className="citation-group-passages">
              {entries.map(({ citation, number }) => (
                <button
                  key={citation.id}
                  className="citation-card"
                  onClick={() => onOpen(citation)}
                  aria-label={`출처 ${number}: ${citation.title || "제목 미확인 문헌"} · ${citation.locator || "위치 미확인"}`}
                >
                  <span className="citation-number">{number}</span>
                  <span>
                    <strong>{citation.locator || "위치 미확인"}</strong>
                    {versions > 1 && <small>{citation.title || "제목 미확인 문헌"} · {documentFormLabel(citation.documentForm, citation.sourceType)}</small>}
                    {citation.contextOrigin === "earlier_answer" && <small>이전 답변의 출처</small>}
                    {!compact && citation.excerpt && (
                      <span className="citation-excerpt">{citation.excerpt}</span>
                    )}
                  </span>
                  <ArrowUpRight size={15} />
                </button>
              ))}
            </div>
          </details>
        );
      });
  };
  const cited = citedIds ? indexed.filter(({ citation }) => citedIds.has(citation.id)) : indexed;
  const other = citedIds ? indexed.filter(({ citation }) => !citedIds.has(citation.id)) : [];
  return (
    <div className={`citation-list ${compact ? "compact" : ""}`}>
      <p className="fine-print">출처 묶음 {groupCount}개 · 자료 판본 {revisionCount}개 · 근거 구간 {citations.length}개</p>
      {citedIds && cited.length > 0 && <strong>답변에 인용한 자료</strong>}
      {citedIds && !cited.length && <p className="fine-print">답변 본문에 연결된 인용을 확인하지 못했습니다.</p>}
      {renderGroups(cited)}
      {other.length > 0 && (
        <details className="other-citations">
          <summary>본문에 인용되지 않은 다른 근거 · {other.length}개 구간</summary>
          <p className="fine-print">검색 결과 또는 이전 대화에서 가져온 근거입니다.</p>
          {renderGroups(other)}
        </details>
      )}
    </div>
  );
}
const relationshipLabels: Record<string, string> = {
  is_a: "상위 개념",
  parent: "상위 개념",
  child: "하위 개념",
  part_of: "상위 모듈",
  has_part: "하위 모듈",
  precedes: "후속 절차",
  follows: "선행 절차",
  alternative: "대체 개념",
  alternative_to: "대체 개념",
  prerequisite: "선행 조건",
  related: "관련 개념",
};
export function RelationCards({
  relations,
  onOpen,
  onFollowup,
}: {
  relations: Relation[];
  onOpen: (citation: Citation) => void;
  onFollowup: (relation: Relation) => void;
}) {
  const [expanded, setExpanded] = useState<string[]>([]);
  return (
    <div className="relation-list">
      {relations.map((relation) => {
        const open = expanded.includes(relation.id);
        return (
          <article
            className={`relation-card ${open ? "is-expanded" : ""}`}
            key={relation.id}
          >
            <button
              className="relation-trigger"
              onClick={() =>
                setExpanded((ids) =>
                  open
                    ? ids.filter((id) => id !== relation.id)
                    : [...ids, relation.id],
                )
              }
              aria-expanded={open}
              aria-controls={`relation-${relation.id}`}
            >
              <span className="relation-icon">
                <GitBranch size={17} />
              </span>
              <span>
                <small>
                  {relation.fromName} ·{" "}
                  {relationshipLabels[relation.type] || relation.type}
                </small>
                <strong>{relation.toName}</strong>
                {relation.summary && <span>{relation.summary}</span>}
              </span>
              <ChevronDown size={17} className={open ? "rotated" : ""} />
            </button>
            <div
              className="accordion-content"
              id={`relation-${relation.id}`}
              hidden={!open}
            >
              <div className="relation-details">
                {relation.conditions && (
                  <p>
                    <strong>적용 조건</strong> {relation.conditions}
                  </p>
                )}
                <p className="muted">
                  관계 상태: {relation.status || "미확인"}
                </p>
                {relation.evidence.length ? (
                  <CitationList
                    citations={relation.evidence}
                    onOpen={onOpen}
                    compact
                  />
                ) : (
                  <p className="muted">
                    이 관계의 원문 근거가 응답에 제공되지 않았습니다.
                  </p>
                )}
                <button
                  className="text-button"
                  onClick={() => onFollowup(relation)}
                >
                  이 개념으로 이어서 질문 <ArrowUpRight size={14} />
                </button>
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}
export function SourceViewCards({
  views,
  onOpen,
  onCompare,
}: {
  views: SourceView[];
  onOpen: (citation: Citation) => void;
  onCompare: (views: SourceView[]) => void;
}) {
  const conceptIds = [
    ...new Set(views.map((view) => view.conceptId).filter(Boolean)),
  ];
  const controller = useSourceViewsController(
    views,
    conceptIds.length === 1 ? conceptIds[0] : undefined,
  );
  const publishers = [
    ...new Map(
      views
        .filter((view) => view.publisherId)
        .map((view) => [
          view.publisherId!,
          view.publisher || view.publisherId!,
        ]),
    ).entries(),
  ];
  const aspects = [...new Set(views.map((view) => view.aspect))];
  const sourceTypes = [...new Set(views.map((view) => view.sourceType))];
  if (!views.length) return null;
  return (
    <details className="source-views">
      <summary className="subsection-header">
        <h4>
          <Users size={16} /> 자료에서 정리한 관점
        </h4>
        <span>
          {conceptIds.length === 1
            ? "같은 개념의 조건과 근거"
            : "여러 개념의 조건과 근거"}
        </span>
        <ChevronDown className="source-views-chevron" size={14} aria-hidden="true" />
      </summary>
      <p className="fine-print">
        자료를 바탕으로 자동 정리한 설명입니다. 연결된 자료는 답변의 출처에서 확인할 수 있습니다. 관점을 선택하면 출처와 항목을 기준으로 비교 질문 초안을 준비합니다. 과거 판본은 현재 검색 범위에서 제외될 수 있습니다.
      </p>
      <div className="view-filters">
        <label>
          <span className="sr-only">발행처 필터</span>
          <select
            value={controller.publisherId}
            onChange={(event) =>
              controller.changeFilter("publisherId", event.target.value)
            }
          >
            <option value="">모든 발행처</option>
            {publishers.map(([id, name]) => (
              <option key={id} value={id}>
                {name}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="sr-only">출처 유형 필터</span>
          <select
            value={controller.sourceType}
            onChange={(event) =>
              controller.changeFilter("sourceType", event.target.value)
            }
          >
            <option value="">모든 출처 유형</option>
            {sourceTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="sr-only">관점 항목 필터</span>
          <select
            value={controller.aspect}
            onChange={(event) =>
              controller.changeFilter("aspect", event.target.value)
            }
          >
            <option value="">모든 관점 항목</option>
            {aspects.map((aspect) => (
              <option key={aspect} value={aspect}>
                {aspect}
              </option>
            ))}
          </select>
        </label>
        {conceptIds.length === 1 && (
          <button
            className="quiet-button small"
            onClick={() => void controller.load()}
            disabled={controller.loading}
          >
            <Search size={14} /> 등록 관점 조회
          </button>
        )}
      </div>
      <p className="fine-print">
        필터는 이 관점 목록만 바꿉니다. 기존 답변을 다시 생성하지 않습니다.
      </p>
      <ErrorNotice>{controller.error}</ErrorNotice>
      {controller.loading && <Loading label="등록된 관점을 읽는 중" />}
      {!controller.loading && !controller.items.length && (
        <p className="inline-empty">이 조건으로 확인된 관점이 없습니다.</p>
      )}
      {controller.items.map((view) => (
        <article className="source-view-card" key={view.id}>
          <div className="source-view-top">
            <label className="selection-label">
              <input
                type="checkbox"
                checked={controller.selectedIds.includes(view.id)}
                onChange={() => controller.toggleSelection(view.id)}
              />
              <strong>
                {view.attributedTo || view.author || "귀속 미확인"}
              </strong>
            </label>
            <Badge>{view.aspect}</Badge>
          </div>
          <p className="view-byline">
            발행처 {view.publisher || "미확인"}
            {view.author ? ` · 저자 ${view.author}` : " · 저자 미확인"} ·{" "}
            {formatDate(view.publishedAt)} · {documentFormLabel(view.documentForm, view.sourceType)}
          </p>
          <p>{view.summary}</p>
          {view.conditions && (
            <div className="condition-box">
              <span>적용 조건</span>
              {view.conditions}
            </div>
          )}
          <details className="evidence-details">
            <summary>
              <BookOpen size={14} /> 근거와 귀속 기준
            </summary>
            <p className="fine-print">
              귀속 기준: {view.attributionBasis || "미확인"} · 자료 유형:{" "}
              {view.sourceType || "미확인"} · 상태: {view.status || "미확인"}
            </p>
            {view.contentDate && (
              <p className="fine-print">
                내용의 기준 시점: {formatDate(view.contentDate)}
              </p>
            )}
            <CitationList
              citations={view.evidence || []}
              onOpen={onOpen}
              compact
            />
            {!view.evidence?.length && (
              <p className="muted">제공된 원문 근거가 없습니다.</p>
            )}
          </details>
        </article>
      ))}
      {!!controller.selected.length && (
        <div className="selection-footer">
          <span>{controller.selected.length}개 관점 선택</span>
          <button
            className="secondary-button small"
            onClick={() => onCompare(controller.selected)}
          >
            선택 관점으로 질문 준비 <ArrowUpRight size={14} />
          </button>
        </div>
      )}
    </details>
  );
}
