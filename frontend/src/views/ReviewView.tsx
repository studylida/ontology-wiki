import { useState } from "react";
import {
  ArrowUpRight,
  Check,
  FileCheck2,
  FileText,
  ListChecks,
  Pause,
  Pencil,
  Play,
  RefreshCw,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";
import type { DocumentForm, DocumentMetadata, ReviewStatus } from "../types/contracts";
import type { useReviewController } from "../controllers/useReviewController";
import { documentFormLabels, indexLabel, reviewLabel } from "../services/display";
import {
  Badge,
  EmptyState,
  ErrorNotice,
  InfoNotice,
  Loading,
} from "./components/Primitives";
import { DocumentMarkdown } from "./components/SafeMarkdown";

export function ReviewView({
  controller: review,
  onQuestion,
  onUpload,
  onBatchUpload,
  canIndex,
}: {
  controller: ReturnType<typeof useReviewController>;
  onQuestion: (id: string, title: string) => void;
  onUpload: () => void;
  onBatchUpload?: () => void;
  canIndex: boolean;
}) {
  const [tab, setTab] = useState<"content" | "passages" | "metadata">(
    "content",
  );
  const [query, setQuery] = useState("");
  const revision = review.revision;
  const metadataField = (
    key: keyof DocumentMetadata,
    label: string,
    hint?: string,
  ) => (
    <label className="field" key={key}>
      {label}
      <input
        value={String(review.metadata[key] || "")}
        onChange={(event) =>
          review.setMetadata({
            ...review.metadata,
            [key]: event.target.value || null,
          })
        }
      />
      {hint && <small>{hint}</small>}
    </label>
  );
  return (
    <div className="feature-page review-page">
      <header className="page-header">
        <div className="page-heading">
          <span className="header-icon">
            <FileCheck2 size={18} />
          </span>
          <div>
            <h1>문헌 검토</h1>
            <p>공용으로 쓸 문헌을 확인하고, 검색 반영 상태를 살펴보기</p>
          </div>
        </div>
        <div className="header-actions">
          <button
            className="quiet-button small"
            onClick={() => void review.refresh()}
          >
            <RefreshCw size={15} />
            새로고침
          </button>
          <button className="secondary-button small" onClick={onUpload}>
            문헌 등록
          </button>
          {onBatchUpload && (
            <button className="secondary-button small" onClick={onBatchUpload}>
              여러 문헌 등록
            </button>
          )}
        </div>
      </header>
      <div className="review-workspace">
        <aside className="review-queue">
          <label className="field">
            <span className="sr-only">검토 상태 필터</span>
            <select
              value={review.filter}
              onChange={(event) =>
                review.setFilter(event.target.value as ReviewStatus)
              }
            >
              {Object.entries(reviewLabel).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <div className="search-input">
            <Search size={15} />
            <input
              aria-label="검토 문헌 검색"
              placeholder="문헌 제목 검색"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>
          <div className="list-caption">
            <span>문헌 단위 검토</span>
            <span>{review.items.length}</span>
          </div>
          {review.items
            .filter((item) =>
              item.title
                .toLocaleLowerCase()
                .includes(query.toLocaleLowerCase()),
            )
            .map((item) => (
              <button
                className={`review-queue-item ${item.currentRevisionId === review.selectedId ? "active" : ""}`}
                key={item.id}
                onClick={() => review.select(item.currentRevisionId)}
                disabled={review.busy}
              >
                <FileText size={17} />
                <span>
                  <strong>{item.title}</strong>
                  <small>{item.publisher || "발행처 미확인"}</small>
                  <Badge tone={item.indexStatus === "failed" ? "red" : ""}>
                    {indexLabel[item.indexStatus] || item.indexStatus}
                  </Badge>
                </span>
              </button>
            ))}
          {!review.items.length && (
            <p className="inline-empty">이 상태의 문헌이 없습니다.</p>
          )}
          <div className="review-explainer">
            <ShieldCheck size={19} />
            <h3>문헌을 검토합니다</h3>
            <p>
              승인은 공용 자료로 사용할 수 있다는 판단입니다. 모든 주장과 수치가
              사실로 검증되었다는 뜻은 아닙니다.
            </p>
          </div>
        </aside>
        <div className="review-detail">
          <ErrorNotice>{review.error}</ErrorNotice>
          <InfoNotice>{review.notice}</InfoNotice>
          {review.loading ? (
            <Loading label="문헌 판본과 구간을 불러오는 중" />
          ) : revision ? (
            <>
              <header className="review-document-heading">
                <div>
                  <p className="eyebrow">LITERATURE REVIEW</p>
                  <h2>{revision.title}</h2>
                  <div className="badge-row">
                    <Badge
                      tone={
                        revision.reviewStatus === "approved" ? "green" : "amber"
                      }
                    >
                      {reviewLabel[revision.reviewStatus] ||
                        revision.reviewStatus}
                    </Badge>
                    <Badge
                      tone={
                        ["indexed", "ready", "active"].includes(
                          revision.indexStatus,
                        )
                          ? "blue"
                          : ""
                      }
                    >
                      {indexLabel[revision.indexStatus] || revision.indexStatus}
                    </Badge>
                  </div>
                </div>
                <button
                  className="secondary-button small"
                  onClick={() => onQuestion(revision.id, revision.title)}
                >
                  이 문헌으로 질문 <ArrowUpRight size={15} />
                </button>
              </header>
              <p className="review-status-note">
                승인과 검색 반영은 별도입니다. 승인된 문헌은 하루 한 번
                갱신되며, 권한이 있으면 즉시 반영을 요청할 수 있습니다. 이
                문헌은 현재 대화에서 먼저 읽을 수 있습니다.
              </p>
              <nav className="detail-tabs" aria-label="문헌 미리보기">
                {[
                  { id: "content", label: "본문", icon: FileText },
                  {
                    id: "passages",
                    label: `검색 구간 (${revision.passages.length})`,
                    icon: ListChecks,
                  },
                  {
                    id: "metadata",
                    label: "서지·귀속 정보",
                    icon: ShieldCheck,
                  },
                ].map(({ id, label, icon: Icon }) => (
                  <button
                    key={id}
                    className={tab === id ? "active" : ""}
                    aria-pressed={tab === id}
                    onClick={() => setTab(id as typeof tab)}
                  >
                    <Icon size={15} />
                    {label}
                  </button>
                ))}
              </nav>
              {tab === "content" && (
                <section className="review-content">
                  {review.editingContent ? (
                    <>
                      <label className="field">
                        정제 본문 · 새 판본
                        <textarea
                          rows={18}
                          value={review.content}
                          onChange={(event) =>
                            review.setContent(event.target.value)
                          }
                        />
                      </label>
                      <p className="fine-print">
                        이전 판본을 덮어쓰지 않습니다. 새 판본은 다시 검토한 후
                        검색에 반영됩니다.
                      </p>
                      <div className="button-row">
                        <button
                          className="secondary-button small"
                          onClick={() => {
                            review.setContent(revision.content);
                            review.setEditingContent(false);
                          }}
                        >
                          편집 취소
                        </button>
                        <button
                          className="primary-button small"
                          onClick={() => void review.saveRevision()}
                          disabled={review.busy || !review.content.trim()}
                        >
                          새 판본 저장
                        </button>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="content-toolbar">
                        <span className="fine-print">
                          현재 판본의 저장된 본문
                        </span>
                        <button
                          className="quiet-button small"
                          onClick={() => review.setEditingContent(true)}
                        >
                          <Pencil size={14} />
                          본문 수정
                        </button>
                      </div>
                      <DocumentMarkdown content={revision.content} />
                    </>
                  )}
                </section>
              )}
              {tab === "passages" && (
                <section className="passage-list">
                  <p className="fine-print">
                    검색 입력의 구간을 확인합니다. 벡터 값은 편집하지 않습니다.
                  </p>
                  {revision.passages.map((passage) => (
                    <article key={passage.id}>
                      <div>
                        <Badge>구간 {passage.ordinal + 1}</Badge>
                        <span>{passage.locator}</span>
                      </div>
                      <p>{passage.text}</p>
                    </article>
                  ))}
                  {!revision.passages.length && (
                    <EmptyState title="아직 구간이 없습니다">
                      본문 처리와 색인 작업 상태를 확인해 주세요.
                    </EmptyState>
                  )}
                </section>
              )}
              {tab === "metadata" && (
                <section className="metadata-editor">
                  <p className="fine-print">
                    발행처와 의견의 귀속 주체를 구분합니다. 회사 사이트에 실린
                    외부 칼럼을 그 회사의 공식 관점으로 간주하지 않습니다.
                  </p>
                  <div className="form-grid">
                    {metadataField("publisher", "발행처")}
                    {metadataField(
                      "publisherId",
                      "발행처 식별자",
                      "등록된 식별자를 확인해 입력합니다.",
                    )}
                    {metadataField("author", "저자")}
                    {metadataField("attributedTo", "관점 귀속 주체")}
                    {metadataField("sourceType", "출처 유형")}
                    <label className="field">
                      저장된 자료의 형태
                      <select value={review.metadata.documentForm || "unknown"} onChange={(event) =>
                        review.setMetadata({ ...review.metadata, documentForm: event.target.value as DocumentForm })}>
                        {Object.entries(documentFormLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                      </select>
                      <small>원자료의 출처 유형과 구분해 선택합니다.</small>
                    </label>
                    {metadataField(
                      "publishedAt",
                      "발행 날짜",
                      "확인되지 않으면 비워 둡니다.",
                    )}
                    <label className="field wide">
                      귀속 판단 근거
                      <textarea
                        rows={3}
                        value={review.metadata.attributionBasis || ""}
                        onChange={(event) =>
                          review.setMetadata({
                            ...review.metadata,
                            attributionBasis: event.target.value || null,
                          })
                        }
                      />
                    </label>
                  </div>
                  <button
                    className="primary-button small"
                    onClick={() => void review.saveMetadata()}
                    disabled={review.busy}
                  >
                    <Check size={15} />
                    서지·귀속 저장
                  </button>
                </section>
              )}
              <section className="review-decision">
                <div>
                  <h3>문헌 검토 결과</h3>
                  <p>이 문헌 판본 전체에 대한 판단과 사유를 남깁니다.</p>
                </div>
                <label className="field">
                  <span className="sr-only">검토 사유</span>
                  <textarea
                    rows={3}
                    value={review.reason}
                    onChange={(event) => review.setReason(event.target.value)}
                    placeholder="사용 범위, 누락 내용, 보류 또는 반려 사유를 기록해 주세요."
                  />
                </label>
                <div className="decision-buttons">
                  <button
                    className="primary-button"
                    disabled={review.busy || !review.reason.trim()}
                    onClick={() => void review.decide("approve")}
                  >
                    <Check size={16} />
                    승인
                  </button>
                  <button
                    className="secondary-button"
                    disabled={review.busy || !review.reason.trim()}
                    onClick={() => void review.decide("hold")}
                  >
                    <Pause size={15} />
                    보류
                  </button>
                  <button
                    className="secondary-button"
                    disabled={review.busy || !review.reason.trim()}
                    onClick={() => void review.decide("reject")}
                  >
                    <X size={15} />
                    반려
                  </button>
                  {revision.reviewStatus === "approved" && (
                    <button
                      className="danger-button"
                      disabled={review.busy || !review.reason.trim()}
                      onClick={() => void review.decide("withdraw")}
                    >
                      승인 철회
                    </button>
                  )}
                </div>
                {canIndex && revision.reviewStatus === "approved" && (
                  <div className="index-action">
                    <span>
                      다음 일일 갱신을 기다리지 않고 이 문헌을 반영합니다.
                    </span>
                    <button
                      className="secondary-button small"
                      disabled={review.busy}
                      onClick={() => void review.index()}
                    >
                      <Play size={13} />이 문헌 즉시 반영
                    </button>
                  </div>
                )}
              </section>
            </>
          ) : (
            <EmptyState
              icon={<FileCheck2 size={32} />}
              title="검토할 문헌을 선택하세요"
            >
              원문과 정제 본문, 구간, 발행처와 저자 정보를 확인하고 문헌 단위로
              판단합니다.
            </EmptyState>
          )}
          <section className="jobs-section">
            <div className="section-heading">
              <h3>최근 작업</h3>
              <span className="fine-print">
                실제 저장된 상태 · 15초마다 갱신
              </span>
            </div>
            {review.jobs.length ? (
              <div className="jobs-table-wrap">
                <table className="jobs-table">
                  <thead>
                    <tr>
                      <th>작업</th>
                      <th>상태</th>
                      <th>확인 내용</th>
                      <th>동작</th>
                    </tr>
                  </thead>
                  <tbody>
                    {review.jobs.map((job) => (
                      <tr key={job.id}>
                        <td>
                          {job.kind}
                          <small className="mono">{job.id.slice(0, 12)}</small>
                        </td>
                        <td>
                          <Badge
                            tone={
                              job.status === "failed"
                                ? "red"
                                : job.status === "completed"
                                  ? "green"
                                  : ""
                            }
                          >
                            {job.status}
                          </Badge>
                        </td>
                        <td>
                          {job.error
                            ? typeof job.error === "string"
                              ? job.error
                              : job.error.message || job.error.code
                            : typeof job.progress === "number"
                              ? `${job.progress}`
                              : "—"}
                        </td>
                        <td>
                          {["failed", "cancelled"].includes(job.status) ? (
                            <button
                              className="text-button"
                              disabled={review.busy}
                              onClick={() =>
                                void review.jobAction(job.id, "retry")
                              }
                            >
                              재시도
                            </button>
                          ) : ["pending", "queued", "running"].includes(
                              job.status,
                            ) ? (
                            <button
                              className="text-button"
                              disabled={review.busy}
                              onClick={() =>
                                void review.jobAction(job.id, "cancel")
                              }
                            >
                              취소
                            </button>
                          ) : (
                            "—"
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="inline-empty">조회 가능한 작업이 없습니다.</p>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
