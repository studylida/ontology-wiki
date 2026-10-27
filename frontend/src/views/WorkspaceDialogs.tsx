import { useState } from "react";
import {
  BookOpen,
  Check,
  FilePlus2,
  FileText,
  GitBranch,
  Plus,
  Search,
  Upload,
  Users,
} from "lucide-react";
import { useConceptPicker } from "../controllers/useSourceController";
import {
  useDocumentPicker,
  useDocumentUploadController,
} from "../controllers/useDocumentController";
import { useSettingsController } from "../controllers/useSettingsController";
import type {
  Concept,
  DocumentForm,
  DocumentSummary,
  GenerationConfig,
  SourceGroup,
  User,
} from "../types/contracts";
import { documentFormLabels, indexLabel, reviewLabel } from "../services/display";
import {
  publisherOptions,
  setPublisherGroup,
} from "../services/sourceScopeService";
import {
  Badge,
  EmptyState,
  ErrorNotice,
  Loading,
  Modal,
  Toggle,
} from "./components/Primitives";

export function ResourcePicker({
  onClose,
  onConcept,
  onDocument,
  onUpload,
  selectedConceptIds,
  selectedDocumentIds,
  sourceGroups,
  onSourceGroups,
}: {
  onClose: () => void;
  onConcept: (concept: Concept) => void;
  onDocument: (id: string, title: string) => void;
  onUpload: () => void;
  selectedConceptIds: string[];
  selectedDocumentIds: string[];
  sourceGroups: SourceGroup[];
  onSourceGroups: (groups: SourceGroup[]) => void;
}) {
  const [tab, setTab] = useState<"documents" | "concepts" | "publishers">(
    "documents",
  );
  const concepts = useConceptPicker(tab === "concepts");
  const documents = useDocumentPicker(tab !== "concepts");
  const publishers = publisherOptions(documents.allItems);
  return (
    <Modal title="질문에 맥락 더하기" eyebrow="자료와 개념" onClose={onClose}>
      <div className="modal-body">
        <nav className="detail-tabs" aria-label="추가할 맥락">
          <button
            className={tab === "documents" ? "active" : ""}
            onClick={() => setTab("documents")}
            aria-pressed={tab === "documents"}
          >
            <FileText size={15} />
            문헌
          </button>
          <button
            className={tab === "concepts" ? "active" : ""}
            onClick={() => setTab("concepts")}
            aria-pressed={tab === "concepts"}
          >
            <GitBranch size={15} />
            개념
          </button>
          <button
            className={tab === "publishers" ? "active" : ""}
            onClick={() => setTab("publishers")}
            aria-pressed={tab === "publishers"}
          >
            <Users size={15} />
            발행처 범위
          </button>
        </nav>
        {tab === "documents" ? (
          <>
            <p className="muted">
              접근 가능한 문헌을 현재 대화에서 읽습니다. 공용 검색 반영 여부와는
              별개입니다.
            </p>
            <div className="search-input">
              <Search size={16} />
              <input
                aria-label="추가할 문헌 검색"
                value={documents.query}
                onChange={(event) => documents.setQuery(event.target.value)}
                placeholder="문헌 제목 검색"
              />
            </div>
            <ErrorNotice>{documents.error}</ErrorNotice>
            {documents.loading ? (
              <Loading />
            ) : (
              <div className="picker-list">
                {documents.items.map((document) => (
                  <button
                    key={document.id}
                    disabled={selectedDocumentIds.includes(
                      document.currentRevisionId,
                    )}
                    onClick={() =>
                      onDocument(document.currentRevisionId, document.title)
                    }
                  >
                    <FileText size={18} />
                    <span>
                      <strong>{document.title}</strong>
                      <small>
                        {reviewLabel[document.reviewStatus] ||
                          document.reviewStatus}{" "}
                        ·{" "}
                        {indexLabel[document.indexStatus] ||
                          document.indexStatus}
                      </small>
                    </span>
                    {selectedDocumentIds.includes(
                      document.currentRevisionId,
                    ) ? (
                      <Check size={17} />
                    ) : (
                      <Plus size={17} />
                    )}
                  </button>
                ))}
                {!documents.items.length && (
                  <EmptyState title="접근 가능한 문헌이 없습니다">
                    새 텍스트 문헌을 등록하거나 외부 조사에서 자료를 가져올 수
                    있습니다.
                  </EmptyState>
                )}
              </div>
            )}
          </>
        ) : tab === "concepts" ? (
          <>
            <p className="muted">
              등록된 개념과 별칭을 선택해 질문의 맥락을 명확하게 합니다.
            </p>
            <div className="search-input">
              <Search size={16} />
              <input
                aria-label="개념 검색"
                value={concepts.query}
                onChange={(event) => concepts.setQuery(event.target.value)}
                placeholder="개념 또는 약어 검색"
              />
            </div>
            <ErrorNotice>{concepts.error}</ErrorNotice>
            {concepts.loading ? (
              <Loading />
            ) : (
              <div className="picker-list">
                {concepts.items.map((concept) => (
                  <button
                    key={concept.id}
                    disabled={selectedConceptIds.includes(concept.id)}
                    onClick={() => onConcept(concept)}
                  >
                    <GitBranch size={17} />
                    <span>
                      <strong>{concept.name}</strong>
                      <small>
                        {concept.description ||
                          concept.aliases.join(" · ") ||
                          "등록 설명 없음"}
                      </small>
                    </span>
                    {selectedConceptIds.includes(concept.id) ? (
                      <Check size={17} />
                    ) : (
                      <Plus size={17} />
                    )}
                  </button>
                ))}
                {!concepts.items.length && (
                  <EmptyState title="등록된 개념이 없습니다">
                    개념을 선택하지 않아도 질문을 입력해 원문을 검색할 수
                    있습니다.
                  </EmptyState>
                )}
              </div>
            )}
          </>
        ) : null}
        {tab === "publishers" && (
          <div className="publisher-picker">
            <p className="muted">
              다음 질문에서 살펴볼 발행처를 선택합니다. 각 발행처의 근거를 따로
              확인하며, 부족한 관점은 구분해 표시합니다.
            </p>
            <p className="fine-print">
              발행처와 글의 저자·의견 귀속은 각각 확인합니다. 선택해도 모드와
              Extended는 바뀌지 않습니다.
            </p>
            <ErrorNotice>{documents.error}</ErrorNotice>
            {documents.loading ? (
              <Loading />
            ) : publishers.length ? (
              publishers.map((publisher) => {
                const matching = sourceGroups.filter(
                  (group) => group.publisherId === publisher.id,
                );
                const selected = matching.length > 0;
                const multiple = matching.length > 1;
                return (
                  <article key={publisher.id}>
                    <label className="selection-label">
                      <input
                        type="checkbox"
                        checked={selected}
                        onChange={(event) =>
                          onSourceGroups(
                            setPublisherGroup(
                              sourceGroups,
                              publisher.id,
                              event.target.checked,
                            ),
                          )
                        }
                      />
                      <span>
                        <strong>{publisher.name}</strong>
                        <small>
                          승인 문헌 {publisher.approvedCount}개 · {publisher.id}
                        </small>
                      </span>
                    </label>
                    <label className="publisher-type">
                      <span className="sr-only">
                        {publisher.name} 출처 유형
                      </span>
                      <select
                        disabled={!selected}
                        value={
                          multiple
                            ? "__multiple"
                            : matching[0]?.sourceType || ""
                        }
                        onChange={(event) =>
                          onSourceGroups(
                            setPublisherGroup(
                              sourceGroups,
                              publisher.id,
                              true,
                              event.target.value,
                            ),
                          )
                        }
                      >
                        {multiple && (
                          <option value="__multiple" disabled>
                            여러 유형 선택됨
                          </option>
                        )}
                        <option value="">모든 출처 유형</option>
                        {publisher.types.map((type) => (
                          <option key={type} value={type}>
                            {type === "unknown" ? "유형 미확인" : type}
                          </option>
                        ))}
                      </select>
                    </label>
                  </article>
                );
              })
            ) : (
              <EmptyState title="식별자가 등록된 발행처가 없습니다">
                등록된 문헌의 실제 발행처 정보가 있어야 범위를 선택할 수
                있습니다. 발행처를 추정해 만들지 않습니다.
              </EmptyState>
            )}
            <p className="fine-print">
              검색에는 현재 권한과 활성 색인 범위가 적용됩니다. 승인 문헌 수는
              내용의 정확성이나 질문별 근거 충족을 뜻하지 않습니다.
            </p>
          </div>
        )}
      </div>
      <footer className="modal-footer">
        <button className="secondary-button" onClick={onUpload}>
          <FilePlus2 size={16} />새 문헌 등록
        </button>
        <button className="primary-button" onClick={onClose}>
          선택 완료
        </button>
      </footer>
    </Modal>
  );
}
export function UploadDialog({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (document: DocumentSummary) => void;
}) {
  const upload = useDocumentUploadController(onCreated);
  return (
    <Modal
      title="문헌 등록"
      eyebrow="자료 등록"
      onClose={onClose}
      className="wide-modal"
    >
      <div className="modal-body">
        <p className="muted">
          텍스트 또는 Markdown 자료를 등록합니다. 저장 후 현재 대화에 바로
          추가할 수 있습니다.
        </p>
        <label className="file-upload">
          <Upload size={20} />
          <span>
            텍스트 파일 선택 <small>.md · .txt / 최대 2 MB</small>
          </span>
          <input
            type="file"
            accept=".md,.markdown,.txt,text/plain,text/markdown"
            onChange={(event) => void upload.readFile(event.target.files?.[0])}
          />
        </label>
        <label className="field">
          문헌 제목
          <input
            value={upload.values.title}
            onChange={(event) => upload.patch({ title: event.target.value })}
          />
        </label>
        <label className="field">
          저장할 본문
          <textarea
            rows={10}
            value={upload.values.content}
            onChange={(event) => upload.patch({ content: event.target.value })}
            placeholder="등록할 본문을 붙여 넣어 주세요."
          />
        </label>
        <details className="upload-metadata">
          <summary>출처 정보 추가</summary>
          <div className="form-grid">
            <label className="field">
              저장된 자료의 형태
              <select value={upload.values.documentForm || ""} onChange={(event) =>
                upload.patch({ documentForm: (event.target.value || null) as DocumentForm | null })}>
                <option value="">파일의 선언 사용 또는 미확인</option>
                {Object.entries(documentFormLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
              <small>편집본과 원자료를 구분합니다. 파일의 선언은 검토가 필요합니다.</small>
            </label>
            <label className="field wide">
              원문 URL
              <input
                type="url"
                value={upload.values.url || ""}
                onChange={(event) =>
                  upload.patch({ url: event.target.value || undefined })
                }
              />
            </label>
            <label className="field">
              발행처
              <input
                value={upload.values.publisher || ""}
                onChange={(event) =>
                  upload.patch({ publisher: event.target.value || undefined })
                }
              />
            </label>
            <label className="field">
              저자
              <input
                value={upload.values.author || ""}
                onChange={(event) =>
                  upload.patch({ author: event.target.value || undefined })
                }
              />
            </label>
            <label className="field">
              관점 귀속 주체
              <input
                value={upload.values.attributedTo || ""}
                onChange={(event) =>
                  upload.patch({
                    attributedTo: event.target.value || undefined,
                  })
                }
              />
            </label>
            <label className="field">
              귀속 판단 근거
              <input
                value={upload.values.attributionBasis || ""}
                onChange={(event) =>
                  upload.patch({
                    attributionBasis: event.target.value || "unknown",
                  })
                }
              />
            </label>
          </div>
        </details>
        <label className="selection-label upload-sharing">
          <input
            type="checkbox"
            checked={upload.values.visibility === "shared_candidate"}
            onChange={(event) =>
              upload.patch({
                visibility: event.target.checked
                  ? "shared_candidate"
                  : "private",
              })
            }
          />
          <span>
            <strong>공용 문헌 검토에 제출</strong>
            <small>
              선택하지 않으면 나만 접근합니다. 제출해도 검토 승인과 검색 반영은
              별도입니다.
            </small>
          </span>
        </label>
        <ErrorNotice>{upload.error}</ErrorNotice>
      </div>
      <footer className="modal-footer">
        <button className="secondary-button" onClick={onClose}>
          돌아가기
        </button>
        <button
          className="primary-button"
          disabled={upload.busy}
          onClick={() => void upload.submit()}
        >
          {upload.busy ? "등록하는 중" : "등록하고 대화에 추가"}
        </button>
      </footer>
    </Modal>
  );
}
export function SettingsDialog({
  onClose,
  user,
  config,
}: {
  onClose: () => void;
  user: User;
  config?: GenerationConfig;
}) {
  const settings = useSettingsController(true);
  const healthGeneration: GenerationConfig | undefined = settings.health
    ? {
        model:
          typeof settings.health.generationModel === "string"
            ? settings.health.generationModel
            : null,
        providerMode:
          typeof settings.health.providerMode === "string"
            ? settings.health.providerMode
            : null,
        effort:
          typeof settings.health.generationEffort === "string"
            ? settings.health.generationEffort
            : config?.effort,
      }
    : undefined;
  const shownConfig = healthGeneration || config;
  return (
    <Modal title="설정" onClose={onClose}>
      <div className="modal-body settings-body">
        <section>
          <h3>
            <BookOpen size={17} />
            개인 위키
          </h3>
          {settings.wiki ? (
            <>
              <Toggle
                label="유용한 대화 내용 자동 정리"
                description="완료된 답변의 설명·사례·조건과 근거를 개인 위키에 정리합니다."
                checked={settings.wiki.autoOrganize}
                disabled={settings.busy}
                onChange={(value) => void settings.setAutoOrganize(value)}
              />
              {settings.wiki.defaultIsAssumption && (
                <p className="fine-print">
                  첫 버전의 기본값은 켜짐입니다. 원하지 않으면 여기서 끄거나
                  특정 대화를 제외할 수 있습니다.
                </p>
              )}
            </>
          ) : (
            <Loading label="자동 정리 설정 확인 중" />
          )}
          <p className="fine-print">
            모든 메시지를 그대로 저장하지 않습니다. 정리 실패가 대화 답변의 성공
            상태를 바꾸지는 않습니다.
          </p>
        </section>
        <section>
          <h3>응답 모델</h3>
          <p className="muted">
            위키·분석 모드와 Extended는 아래 모델 설정을 변경하지 않습니다.
          </p>
          <dl className="settings-model">
            <div>
              <dt>모델</dt>
              <dd>
                {shownConfig?.model || "설정 정보를 아직 확인하지 못했습니다"}
              </dd>
            </div>
            <div>
              <dt>요청 Effort</dt>
              <dd>{shownConfig?.effort || "미확인"}</dd>
            </div>
            <div>
              <dt>실행 환경</dt>
              <dd>
                {shownConfig?.providerMode === "fixture" ? (
                  <Badge tone="amber">Fixture · 실제 모델 호출 없음</Badge>
                ) : (
                  shownConfig?.providerMode || "미확인"
                )}
              </dd>
            </div>
          </dl>
        </section>
        <section>
          <h3>내 계정</h3>
          <dl className="settings-model">
            <div>
              <dt>사용자</dt>
              <dd>{user.username}</dd>
            </div>
            <div>
              <dt>역할</dt>
              <dd>{user.role}</dd>
            </div>
          </dl>
          <p className="fine-print">
            입력 중인 초안과 다음 답변 설정은 사용자별로 이 브라우저에
            복원됩니다. 제출한 메시지와 응답은 서버에 보관됩니다.
          </p>
        </section>
        <ErrorNotice>{settings.error}</ErrorNotice>
      </div>
      <footer className="modal-footer">
        <button className="primary-button" onClick={onClose}>
          닫기
        </button>
      </footer>
    </Modal>
  );
}
