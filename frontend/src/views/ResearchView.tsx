import {
  ArrowLeft,
  ArrowRight,
  Compass,
  ExternalLink,
  FileSearch,
  FileText,
  Search,
} from "lucide-react";
import type { useResearchController } from "../controllers/useResearchController";
import { formatDate, readScopeLabel, safeUrl } from "../services/display";
import {
  Badge,
  EmptyState,
  ErrorNotice,
  Loading,
} from "./components/Primitives";
import { SafeMarkdown } from "./components/SafeMarkdown";

export function ResearchView({
  controller: research,
  onBack,
}: {
  controller: ReturnType<typeof useResearchController>;
  onBack: () => void;
}) {
  return (
    <div className="feature-page research-page">
      <header className="page-header">
        <div className="page-heading">
          <span className="header-icon">
            <Compass size={18} />
          </span>
          <div>
            <h1>외부 문헌 조사</h1>
            <p>질문에 필요한 문헌을 고르고, 대화로 가져오기</p>
          </div>
        </div>
        <button className="secondary-button small" onClick={onBack}>
          <ArrowLeft size={15} />
          대화로 돌아가기
        </button>
      </header>
      <div className="feature-scroll">
        <div className="research-content">
          <section className="research-search-panel">
            <p className="eyebrow">START WITH THE LITERATURE</p>
            <h2>어떤 근거를 더 찾고 싶으신가요?</h2>
            <p className="muted">
              한 번의 검색으로 문헌 후보를 확인합니다. 내용을 읽은 범위와 적용
              한계를 구분해 살펴보세요.
            </p>
            <form
              onSubmit={(event) => {
                event.preventDefault();
                void research.search();
              }}
            >
              <div className="search-input large">
                <Search size={18} />
                <input
                  aria-label="외부 문헌 검색 질문"
                  value={research.query}
                  onChange={(event) => research.setQuery(event.target.value)}
                  placeholder="예: HBM 열압착 본딩의 접합 조건과 수율"
                />
                <button
                  className="primary-button"
                  type="submit"
                  disabled={
                    research.busy ||
                    research.transferring ||
                    !!research.fetchingIds.length ||
                    !research.query.trim()
                  }
                >
                  {research.busy ? "검색 중" : "문헌 검색"}
                </button>
              </div>
            </form>
            <details className="research-conditions">
              <summary>대화에 함께 가져갈 목적·조건</summary>
              <label className="field">
                <span className="sr-only">문헌 조사 조건</span>
                <textarea
                  rows={3}
                  value={research.conditions}
                  onChange={(event) =>
                    research.setConditions(event.target.value)
                  }
                  placeholder="적용 대상, 비교 기준, 알고 싶은 한계 등을 적어 주세요."
                />
              </label>
            </details>
          </section>
          <ErrorNotice>{research.error}</ErrorNotice>
          {research.warnings.map((warning, index) => (
            <div className="notice notice-warning" key={index}>
              {warning}
            </div>
          ))}
          <div className="section-heading">
            <div>
              <h3>
                문헌 후보{" "}
                {research.searchedQuery && <span>{research.items.length}</span>}
              </h3>
              {research.searchedQuery && (
                <p>검색 질문: {research.searchedQuery}</p>
              )}
            </div>
            <span className="fine-print">문헌 1개 · 카드 1개</span>
          </div>
          {research.busy && <Loading label="외부 문헌 정보를 가져오는 중" />}
          {!research.busy && !research.items.length && (
            <EmptyState
              icon={<FileSearch size={29} />}
              title={
                research.searchedQuery
                  ? "검색된 문헌이 없습니다"
                  : "문헌을 먼저 확인하세요"
              }
            >
              {research.searchedQuery
                ? "질문이나 검색어를 직접 조정해 다시 찾아볼 수 있습니다."
                : "검색 결과를 확인한 뒤 필요한 문헌을 선택하세요. 내용을 가져오지 못한 자료는 읽은 것으로 표시하지 않습니다."}
            </EmptyState>
          )}
          <div className="research-results">
            {research.items.map((card) => {
              const fetching = research.fetchingIds.includes(card.id);
              const metadataOnly = card.readScope === "metadata";
              const url = safeUrl(card.url);
              return (
                <article
                  className={`literature-card ${research.selectedIds.includes(card.id) ? "selected" : ""}`}
                  key={card.id}
                >
                  <div className="literature-top">
                    <label className="selection-label">
                      <input
                        type="checkbox"
                        aria-label={`${card.title} 선택`}
                        checked={research.selectedIds.includes(card.id)}
                        disabled={
                          research.busy || research.transferring || fetching
                        }
                        onChange={() => research.toggleSelection(card.id)}
                      />
                      <Badge tone={metadataOnly ? "amber" : "blue"}>
                        {readScopeLabel[card.readScope] || "확인 범위 미확인"}
                      </Badge>
                    </label>
                    <span className="fine-print">
                      {formatDate(card.publishedAt)}
                    </span>
                  </div>
                  <h3>{card.title || "제목 미확인"}</h3>
                  <p className="literature-byline">
                    {card.author || "저자 미확인"} ·{" "}
                    {card.publisher || "발행처 미확인"}
                  </p>
                  {metadataOnly ? (
                    <div className="unread-note">
                      <FileText size={17} />
                      <p>
                        본문을 확인하지 않았습니다. 이 질문에 대한 실제 내용과
                        적용 한계는 판단하지 못했습니다.
                      </p>
                    </div>
                  ) : (
                    <div className="literature-relevance">
                      <h4>질문에 도움이 되는 부분</h4>
                      <p>
                        {card.relevance ||
                          "확보한 내용을 아래에서 확인할 수 있습니다. 질문에 대한 관련성 평가는 제공되지 않았습니다."}
                      </p>
                    </div>
                  )}
                  {!!card.limitations?.length && (
                    <div className="literature-limits">
                      <h4>확인 범위와 적용 한계</h4>
                      <ul>
                        {card.limitations.map((limit, index) => (
                          <li key={index}>{limit}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {card.content && (
                    <details className="evidence-details">
                      <summary>실제로 확보한 내용 보기</summary>
                      <div className="research-excerpt">
                        <SafeMarkdown content={card.content} />
                      </div>
                    </details>
                  )}
                  <footer className="literature-footer">
                    {url && (
                      <a
                        className="text-button"
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        발행처 원문 <ExternalLink size={13} />
                      </a>
                    )}
                    <span className="fine-print">
                      상태: {card.status || "미확인"}
                    </span>
                    {card.readScope !== "full" && (
                      <button
                        className="secondary-button small"
                        onClick={() => void research.fetchContent(card)}
                        disabled={
                          fetching ||
                          research.busy ||
                          research.transferring ||
                          !url
                        }
                      >
                        {fetching ? "본문 확인 중" : "내용 가져오기"}
                      </button>
                    )}
                  </footer>
                </article>
              );
            })}
          </div>
        </div>
      </div>
      <footer className="research-transfer">
        <div>
          <strong>{research.selectedIds.length}개 문헌 선택</strong>
          <p>
            선택한 공개 문헌은 검토 대기 자료로 제출됩니다. 가져오기만으로
            답변을 생성하지 않습니다.
          </p>
        </div>
        <button
          className="primary-button"
          onClick={() => void research.transfer()}
          disabled={
            !research.selectedIds.length ||
            research.transferring ||
            research.busy ||
            !!research.fetchingIds.length
          }
        >
          {research.transferring ? "가져오는 중" : "원래 대화에 가져오기"}
          <ArrowRight size={16} />
        </button>
      </footer>
    </div>
  );
}
