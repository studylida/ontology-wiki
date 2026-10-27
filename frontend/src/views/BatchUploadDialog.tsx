import { useBatchDocumentController } from "../controllers/useBatchDocumentController";
import { ErrorNotice, Modal } from "./components/Primitives";

export function canBatchDocumentUpload(
  permissions: string[] | undefined,
): boolean {
  return Boolean(
    permissions?.includes("documents:review") &&
    permissions.includes("documents:write"),
  );
}

export function BatchUploadDialog({
  onClose,
  onChanged,
}: {
  onClose: () => void;
  onChanged: () => void;
}) {
  const batch = useBatchDocumentController(onChanged);
  const fixedSelection = batch.items.some(
    (item) => item.state === "created" || item.state === "unknown",
  );
  const canSubmit = batch.items.some(
    (item) => item.state === "ready" || item.state === "failed",
  );
  return (
    <Modal
      title="여러 문헌 등록"
      eyebrow="자료 등록"
      onClose={() => {
        if (!batch.busy) onClose();
      }}
      className="wide-modal"
    >
      <div className="modal-body">
        <p>
          선택한 파일을 각각 검토 대기로 등록합니다. 승인과 검색 반영은 검토
          화면에서 따로 진행합니다.
        </p>
        <p className="fine-print">
          파일에 적힌 출처 정보는 본문과 함께 보존됩니다. 원문 URL은 등록할 때
          각 파일에 입력해 주세요. 발행처·저자·출처 유형도 여기에서 입력하거나
          검토 화면에서 확인할 수 있습니다. 같은 제목만 비교하므로 다른 이름의
          중복은 발견하지 못할 수 있습니다.
        </p>
        <label className="field">
          Markdown 또는 텍스트 파일 선택 (최대 200개, 파일당 2 MB)
          <input
            type="file"
            multiple
            accept=".md,.markdown,.txt,text/plain,text/markdown"
            disabled={batch.busy || fixedSelection}
            onChange={(event) =>
              batch.select(Array.from(event.target.files || []))
            }
          />
        </label>
        {fixedSelection && (
          <p className="fine-print">
            처리한 파일의 결과를 보존하기 위해 선택을 변경할 수 없습니다. 다른
            파일은 결과 확인 후 새로 등록해 주세요.
          </p>
        )}
        {batch.limitedList && (
          <p role="status">
            기존 자료 목록은 최근 250건까지만 확인하므로 더 오래된 자료의 제목
            중복은 확인되지 않았습니다.
          </p>
        )}
        <ErrorNotice>{batch.error}</ErrorNotice>
        <div aria-live="polite">
          {batch.items.map((item, index) => (
            <div className="field" key={`${item.file.name}-${index}`}>
              <label>
                <span>{item.file.name} 제목</span>
                <input
                  value={item.title}
                  maxLength={500}
                  disabled={
                    batch.busy ||
                    item.state === "created" ||
                    item.state === "unknown"
                  }
                  onChange={(event) =>
                    batch.setTitle(index, event.target.value)
                  }
                />
              </label>
              <details>
                <summary>{item.file.name} 출처 정보</summary>
                <div className="form-grid">
                  <label className="field wide">
                    원문 URL
                    <input
                      aria-label={`${item.file.name} 원문 URL`}
                      type="url"
                      value={item.url}
                      maxLength={4000}
                      disabled={
                        batch.busy ||
                        item.state === "created" ||
                        item.state === "unknown"
                      }
                      onChange={(event) =>
                        batch.setMetadata(index, { url: event.target.value })
                      }
                    />
                  </label>
                  <label className="field">
                    발행처
                    <input
                      aria-label={`${item.file.name} 발행처`}
                      value={item.publisher}
                      maxLength={500}
                      disabled={
                        batch.busy ||
                        item.state === "created" ||
                        item.state === "unknown"
                      }
                      onChange={(event) =>
                        batch.setMetadata(index, {
                          publisher: event.target.value,
                        })
                      }
                    />
                  </label>
                  <label className="field">
                    저자
                    <input
                      aria-label={`${item.file.name} 저자`}
                      value={item.author}
                      maxLength={500}
                      disabled={
                        batch.busy ||
                        item.state === "created" ||
                        item.state === "unknown"
                      }
                      onChange={(event) =>
                        batch.setMetadata(index, { author: event.target.value })
                      }
                    />
                  </label>
                  <label className="field">
                    출처 유형
                    <input
                      aria-label={`${item.file.name} 출처 유형`}
                      value={item.sourceType}
                      maxLength={80}
                      disabled={
                        batch.busy ||
                        item.state === "created" ||
                        item.state === "unknown"
                      }
                      onChange={(event) =>
                        batch.setMetadata(index, {
                          sourceType: event.target.value,
                        })
                      }
                    />
                  </label>
                </div>
              </details>
              <small>
                {item.state === "created"
                  ? "검토 대기로 등록됨"
                  : item.state === "unknown"
                    ? "등록 여부 확인 필요"
                    : item.state === "failed"
                      ? "등록하지 못함"
                      : "등록 대기"}
                {item.message ? ` · ${item.message}` : ""}
              </small>
            </div>
          ))}
        </div>
      </div>
      <footer className="modal-footer">
        <button
          className="secondary-button"
          disabled={batch.busy}
          onClick={onClose}
        >
          닫기
        </button>
        <button
          className="primary-button"
          disabled={batch.busy || !canSubmit}
          onClick={() => void batch.submit()}
        >
          {batch.busy ? "등록하는 중" : "검토 대기로 등록"}
        </button>
      </footer>
    </Modal>
  );
}
