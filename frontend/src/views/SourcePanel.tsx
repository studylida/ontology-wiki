import { useState } from "react";
import {
  ArrowUpRight,
  ExternalLink,
  FileText,
  Link2,
  List,
} from "lucide-react";
import type { useSourceController } from "../controllers/useSourceController";
import {
  formatDate,
  documentFormLabel,
  indexLabel,
  readScopeLabel,
  reviewLabel,
  safeUrl,
} from "../services/display";
import { Badge, ErrorNotice, Loading, Modal } from "./components/Primitives";
import { DocumentMarkdown } from "./components/SafeMarkdown";

export function SourcePanel({
  controller: source,
  onQuestion,
}: {
  controller: ReturnType<typeof useSourceController>;
  onQuestion: (id: string, title: string) => void;
}) {
  const [tab, setTab] = useState<"text" | "passages">("text");
  if (!source.selection) return null;
  const revision = source.revision;
  const citation = source.selection.citation;
  const formLabel = revision
    ? documentFormLabel(revision.metadata.documentForm, revision.metadata.sourceType)
    : documentFormLabel(citation?.documentForm, citation?.sourceType);
  const isDerived = ["편집 요약", "편집본", "원문 텍스트 추출본"].includes(formLabel);
  const url = safeUrl(revision?.metadata.url || citation?.url);
  return (
    <Modal
      title={isDerived ? `${formLabel}과 근거` : "자료와 근거"}
      eyebrow="SOURCE READER"
      onClose={source.close}
      className="source-panel"
    >
      <div className="source-panel-body">
        {source.loading ? (
          <Loading label="현재 권한으로 원문을 확인하는 중" />
        ) : (
          <>
            <ErrorNotice>{source.error}</ErrorNotice>
            {revision && (
              <>
                <h3 className="source-title">{revision.title}</h3>
                <p className="fine-print">자료 형태: {formLabel}. {isDerived ? "저장된 자료를 연결된 원문과 구분해 확인하세요." : "등록 정보이며 검증 결과가 아닙니다."}</p>
                {isDerived && <p className="fine-print">연결된 링크는 인용 구간의 개별 근거와 다를 수 있습니다. 개별 근거의 출처는 저장된 본문에서 확인하세요.</p>}
                <div className="badge-row">
                  <Badge tone="blue">
                    {readScopeLabel[revision.readScope] || revision.readScope}
                  </Badge>
                  <Badge>
                    {reviewLabel[revision.reviewStatus] ||
                      revision.reviewStatus}
                  </Badge>
                  <Badge>
                    {indexLabel[revision.indexStatus] || revision.indexStatus}
                  </Badge>
                </div>
                <dl className="source-metadata">
                  <div>
                    <dt>발행처</dt>
                    <dd>{revision.metadata.publisher || "미확인"}</dd>
                  </div>
                  <div>
                    <dt>저자</dt>
                    <dd>{revision.metadata.author || "미확인"}</dd>
                  </div>
                  <div>
                    <dt>관점 귀속</dt>
                    <dd>{revision.metadata.attributedTo || "미확인"}</dd>
                  </div>
                  <div>
                    <dt>발행 날짜</dt>
                    <dd>{formatDate(revision.metadata.publishedAt)}</dd>
                  </div>
                </dl>
                {citation && (
                  <section className="quoted-evidence">
                    <p>
                      <Link2 size={14} />
                      답변에 연결된 근거 · {citation.locator || "위치 미확인"}
                    </p>
                    <blockquote>
                      {citation.excerpt || "인용 발췌가 제공되지 않았습니다."}
                    </blockquote>
                  </section>
                )}
                <div className="source-actions">
                  {url && (
                    <a
                      className="text-button"
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {isDerived ? "자료에 연결된 링크 열기" : "발행처에서 열기"} <ExternalLink size={13} />
                    </a>
                  )}
                  <button
                    className="text-button"
                    onClick={() => {
                      onQuestion(revision.id, revision.title);
                      source.close();
                    }}
                  >
                    이 문헌으로 질문 <ArrowUpRight size={14} />
                  </button>
                </div>
                <nav className="detail-tabs" aria-label="원문 표시 방식">
                  <button
                    className={tab === "text" ? "active" : ""}
                    onClick={() => setTab("text")}
                    aria-pressed={tab === "text"}
                  >
                    <FileText size={14} />
                    저장된 본문
                  </button>
                  <button
                    className={tab === "passages" ? "active" : ""}
                    onClick={() => setTab("passages")}
                    aria-pressed={tab === "passages"}
                  >
                    <List size={14} />
                    구간 {revision.passages.length}
                  </button>
                </nav>
                {tab === "text" ? (
                  <DocumentMarkdown content={revision.content} />
                ) : (
                  <div className="passage-list">
                    {revision.passages.map((passage) => (
                      <article
                        className={
                          citation?.passageId === passage.id
                            ? "highlighted-passage"
                            : ""
                        }
                        key={passage.id}
                      >
                        <div>
                          <Badge>구간 {passage.ordinal + 1}</Badge>
                          <span>{passage.locator}</span>
                        </div>
                        <p>{passage.text}</p>
                      </article>
                    ))}
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </Modal>
  );
}
