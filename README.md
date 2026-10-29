# Ontology Wiki — 사내 지식 기반 AI 어시스턴트

[채팅·RAG 아키텍처](docs/CHAT_ARCHITECTURE.md)는 현재 구현된 기능의 설계 기준이다. [공용 개념 위키 아키텍처](docs/WIKI_ARCHITECTURE.md)는 별도로 합의 중인 **신규 위키의 제품 설계 기준**이다. 위키 1단계의 직원 직접 작성·수정·이력·복구·보호 화면/API를 연결했다. AI 편집·의미 검색·본문 자동 링크·채팅 근거 연동은 후속 단계다. 기존 채팅·RAG는 유지하고 신규 위키는 과거 위키 설계를 승계하지 않는다. **기존 채팅 1~5단계 구현 범위: 인증·개인 대화, 공용 문헌 업로드·자동 색인, 내부 검색·답변·각주·스트리밍과 브라우저 화면, 통합 회귀·합성 질문 추적 평가**다. 외부 조사·개인 위키·모드 선택과 구 화면/답변의 호환은 제공하지 않는다. 실제 모델 품질과 현업 유용성 평가를 완료했다는 의미는 아니다.

## 실행과 스키마

Python 3.12, PostgreSQL 16, pgvector를 사용한다. API와 문헌 작업자는 같은 DB와 지속 원문 저장 경로를 사용한다. 새 환경은 별도의 빈 개발 DB로 시작한다. 기존 v3 DB에는 같은 migrate 명령으로 미적용 SQL만 추가한다. 1단계 `001_foundation.sql`, 2단계 `002_documents.sql`은 변경하지 않았고 3단계는 `003_answers.sql`이다. 4·5단계는 새 스키마가 필요하지 않다. v2 데이터 이관이나 DB·원문 삭제 명령은 제공하지 않는다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
export OW_DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@127.0.0.1:5432/ontology_assistant_dev'
export OW_AUTH_SECRET="$(.venv/bin/python -c 'import secrets; print(secrets.token_hex(32))')"
export OW_STORAGE_PATH="$PWD/var/shared-raw"
export OW_PROVIDER_MODE=fixture
.venv/bin/python scripts/v2/dev.py migrate --database-name ontology_assistant_dev
# 최초 한 번만 생성. 기존 계정은 덮어쓰지 않는다.
.venv/bin/python scripts/v2/dev.py create-user --username alice
.venv/bin/python scripts/v2/dev.py create-user --username bob
.venv/bin/python scripts/v2/dev.py serve
# 같은 환경변수를 사용하는 별도 셸에서:
.venv/bin/python scripts/v2/dev.py worker
# 대기 문헌 작업 한 건만 처리:
.venv/bin/python scripts/v2/dev.py worker --once
```

**현재 MVP는 DB당 API 프로세스 하나(`--workers 1`)와 별도 문헌 작업자 하나를 사용한다.** 각각 다른 PostgreSQL 세션 advisory lock을 사용한다. 두 번째 API는 명확한 오류로 기동을 거부하여 살아 있는 다른 프로세스의 실행을 중단 상태로 복구하지 않도록 한다. 동시에 여러 대화의 요청은 한 비동기 API 프로세스에서 처리한다. 다중 API 인스턴스 운영을 지원한다고 주장하지 않는다.

`fixture`는 해시 임베딩과 제공받은 근거를 표시하는 검증용 응답이다. 검색 의미 품질이나 AI 해석 능력을 보증하지 않는다. fixture의 분할·대기는 취소/재연결 검사 전용이며 실제 공급자 응답을 인위적으로 타이핑하지 않는다. `live`는 승인된 공급자 계정·자료·비용 범위에서만 사용한다. 키·모델 설정 실패 시 다른 모델이나 fixture로 자동 대체하지 않는다. `disabled`는 명시적 구성 오류를 기록한다.

API 기동은 계정·migration·문헌 작업자·모델 호출을 자동 시작하지 않는다. 이전에 중단된 답변 실행은 `interrupted`로 기록하고 저장된 부분만 복원한다. **새 생성은 POST 요청이나 명시적 재시도로만 시작**한다. 작업자를 실행하지 않으면 업로드는 대기 상태로 남는다.

비밀번호는 대화식으로 최소 12자를 입력한다. `OW_BOOTSTRAP_PASSWORD`는 자동화용이며 Git·로그에 남기지 않는다. `OW_AUTH_SECRET`은 재시작 후에도 같은 비공개 값을 유지한다. 명시적 프로세스 환경변수는 `.env`보다 우선한다. Windows에서는 `.venv\Scripts\python.exe`와 PowerShell의 `$env:...`를 사용한다. pgvector 설치 권한이 없다면 DB 관리자가 확장을 먼저 설치해야 한다.

## 브라우저 실행과 사용

프론트엔드는 기존 React·TypeScript·Vite 구성과 lockfile을 사용한다. CI의 Node 버전은 22다. API와 문헌 작업자를 실행한 상태에서 별도 셸을 연다.

```bash
cd frontend
npm ci
npm run dev
# 타입 검사와 배포 파일 생성:
npm run build
# 빌드 결과를 로컬에서 확인:
npm run preview
```

개발 화면은 `http://127.0.0.1:5173`이다. Vite가 `/api`를 기본 `http://127.0.0.1:8000`으로 프록시한다. API 주소가 다르면 Vite 실행 전에 `OW_API_PROXY_TARGET`을 설정한다. preview도 같은 프록시를 사용하며 주소는 실행 로그에서 확인한다. 별도 배포에서는 `/api/v1` 프록시 또는 빌드 시 `VITE_API_BASE_URL`이 필요하다. 모델 API 키는 프론트엔드 환경변수에 넣지 않는다. 루트의 구 HTML/JS 시안 진입점은 삭제했으며 `frontend`만 실행한다. dev/preview를 운영 배포로 취급하지 않는다.

로그인 → **공용 문헌**에서 전사 공유 안내 확인·파일 업로드 → 처리 상태 확인 → **새 대화**에서 질문 → 문장 옆 각주로 해당 판본·구간 확인 순서로 사용한다. 최신 판본 상태와 실제 검색 가능 여부를 따로 표시하므로 새 판본이 실패해도 이전 유효 판본이 검색에 쓰이는지 알 수 있다. 처리 중에는 서버 상태만 표시하며 가짜 진행률은 없다.

같은 대화에서 후속 질문을 보낸다. 진행 중 **답변 중단**은 실제 취소 요청이며, 실패·취소·중단 후 **답변 다시 생성**은 명시적 새 실행이다. **저장된 실행 다시 연결**과 페이지 새로고침은 GET으로 저장 상태를 복원할 뿐 생성하지 않는다. POST 응답을 못 받은 경우 **같은 요청 다시 전송**은 같은 requestId를 재사용한다. 연결 종료나 전송 중 상태를 성공으로 바꾸지 않는다.

원문 패널은 각주 번호·문헌·판본·근거 구간을 함께 표시하고 원본 파일을 인증된 API로 받는다. Markdown의 원시 HTML·외부 이미지는 렌더링하지 않고, 확인된 인용 ID만 각주 버튼으로 만든다. 본문·출처 목록·원문 패널은 서버의 인용 번호를 공유한다.

공용 문헌 화면에서 최신/활성 판본, 보류 이유, 처리 오류와 재처리·비활성화를 확인한다. 변경 버튼은 서버의 `canManage`를 사용하며 실제 권한/상태 검사는 서버가 수행한다. 비활성화에는 확인 단계가 있고 승인 대기열은 없다. 새 파일 판본 등록 API는 유지하지만 새 판본 업로드 전용 UI는 이번 최소 화면에 포함하지 않는다.

새 서비스의 sessionStorage에는 로그인 토큰, 사용자별 선택 대화 ID, 전송 결과 미확인 요청과 위키 저장 복구용 제출 요청·확인된 영수증을 저장한다. 답변 본문은 서버에서 복원하며 구 초안·모드·위키 상태를 읽거나 변환하지 않는다. 로그아웃하면 해당 사용자 세션 상태와 화면을 비운다. 문헌 목록은 화면이 열려 있을 때 갱신하고, 원문 패널도 현재 접근 가능 여부를 재확인한다. 과거 대화의 자료 변경은 대화 재조회에 반영된다. 이미 내려받은 자료를 원격 삭제한다는 의미는 아니다.

## 공용 위키 1단계 — 직원 직접 작성·편집

새 위키는 채팅/문헌 등록자의 소유권과 별개다. 로그인한 모든 직원이 일반 페이지를 읽고 편집한다. 문서 제목은 중복 가능하며 `pageId`가 지속 식별자다. 작성자·수정자·시각과 모든 내용 판본을 보존한다. 보호·해제는 관리자만 수행하고 보호된 문서의 직접 저장·복구도 관리자만 가능하다. 작성자에게 독점 편집권을 주지 않는다.

기존 `001~003` migration은 수정하지 않았다. API를 종료한 뒤 **기존 DB 이름과 일치하는 이름**으로 다음 명령을 실행하면 `004_shared_wiki.sql`만 추가된다. DB나 원문을 초기화하지 않는다.

```bash
python scripts/v2/dev.py migrate --database-name <실제_개발_DB_이름>
python scripts/v2/dev.py serve
# 별도 셸에서 기존 frontend 실행:
cd frontend
npm ci
npm run dev
```

위키의 직접 저장·읽기에는 문헌 worker나 모델 API 키가 필요하지 않으며 `OW_PROVIDER_MODE=disabled`에서도 동작한다. 기존 문헌 업로드·색인에는 이전과 같이 별도 worker가 필요하다. 기존 계정을 사용하고 관리자가 없을 때만 `python scripts/v2/dev.py create-user --username <새_관리자명> --role admin`으로 명시적으로 생성한다.

브라우저에서 **공용 위키 → 새 위키 문서 → 제목·Markdown·선택적인 근거/업무 맥락 → 저장**으로 시작한다. 다른 직원도 문서를 열고 수정할 수 있다. **변경 이력**에서 이전 판본과 현재 판본의 차이를 보고 **이 판본으로 복구**하면 과거 이력은 그대로 남은 채 새 판본이 생성된다. 관리자만 보호 버튼을 본다. 잠긴 문서도 모든 직원이 읽고 과거 판본을 확인할 수 있다.

| 메서드·경로(`/api/v1` 아래) | 계약 |
| --- | --- |
| `GET /wiki/pages?q=...&limit=30&offset=0` | 제목 키워드 검색·목록. 의미 검색 아님 |
| `POST /wiki/pages` | `requestId`, `title`, `markdown`, 선택 `sourceNote`, `changeSummary` |
| `GET /wiki/pages/{id}` | 현재 판본, 작성자·편집자, `version`, `canEdit`, `canProtect` |
| `POST /wiki/pages/{id}/revisions` | 작성 요청과 같은 필드 + `baseVersion` |
| `GET /wiki/pages/{id}/revisions` | 이력 목록·페이지네이션 |
| `GET /wiki/pages/{id}/revisions/{revisionId}` | 해당 페이지의 이전 판본 원문 |
| `GET /wiki/pages/{id}/compare?fromRevisionId=...&toRevisionId=...` | 두 판본 원문과 변경 비교 |
| `POST /wiki/pages/{id}/restore` | `requestId`, `baseVersion`, `revisionId` |
| `PATCH /wiki/pages/{id}/protection` | 관리자만. `requestId`, `baseVersion`, `locked` |

쓰기 결과는 `pageId`, `revisionId`, `version`, `replayed`를 반환한다. `version`은 내용 수정뿐 아니라 보호 상태 변경도 포함하는 편집 기준이며 내용 판본의 `revisionNumber`와 다르다. 모든 변경은 같은 페이지 잠금 안에서 현재 권한·기준 상태를 검사한다. 충돌은 409이고 일반 직원의 잠금 우회는 403이다. 복구는 대상 페이지에 속한 판본만 허용한다. 보호 상태는 과거 본문 복구로 해제되지 않는다.

네트워크 실패로 접수 여부가 불분명하면 동일한 `requestId`와 동일한 본문으로 재전송한다. 이는 기존 저장 영수증을 확인할 뿐 중복 판본을 만들지 않는다. 이미 저장된 요청의 영수증 재확인은 이후 보호 상태를 바꾸거나 새로운 쓰기를 수행하지 않는다. 같은 요청 ID를 다른 작업·본문으로 쓰면 409다. 실패한 저장을 성공으로 표시하지 않으며 페이지·판본·재전송 영수증은 한 트랜잭션에서 저장한다.

다른 직원이 먼저 저장하면 편집 입력을 유지하고 최신 판본 비교를 제공한다. 사용자가 최신 내용을 직접 반영한 뒤 **최신 판본 확인 후 편집 계속**을 선택해야 다시 저장할 수 있다. 자동 병합은 없다. 같은 로그인에서 대화/문헌 탭으로 이동해도 편집 입력은 메모리에 남는다. 브라우저를 닫거나 새로고침하면 미저장 입력이 사라질 수 있어 경고하며 자동 복구용 개인 초안 저장소는 만들지 않았다. 로그아웃 시 화면과 미저장 편집은 비운다. 다만 **이미 전송한 위키 저장 요청**은 사용자별 sessionStorage에 동일한 요청 ID·본문과 확인된 영수증을 보관한다. 같은 탭을 새로고침한 뒤에는 명시적인 확인 동작으로 이어받으며 자동 POST하지 않는다. 저장은 확인됐지만 문서 조회만 실패한 경우에는 GET만 재시도한다. 로그아웃하면 이 복구 상태도 삭제하며 아직 전송하지 않은 초안이나 브라우저 종료 이후의 복구를 보장하지 않는다.

근거 메모는 원본 문헌의 제목·판본·위치 또는 직원 경험을 자유롭게 적는 선택 필드다. 파일을 강제로 요구하거나 인용의 정확성을 인증하지 않는다. 미리보기·현재 문서·과거 판본·근거 메모는 기존 안전한 Markdown 렌더러를 공유하며 원시 HTML·스크립트·외부 이미지·위험한 URL을 실행하지 않는다.

**이번에 구현하지 않은 것:** AI 제안·의미 검색·유사 문서 안내·자동 하이퍼링크·동음이의어 탐색 UI·위키 RAG 연결·외부 전용 Markdown API·삭제·분류·승인 플랫폼. 현재 위키 내용은 기존 채팅의 검색 근거에 자동 포함되지 않는다. 해당 사항은 후속 위키 단계다.

## 인증과 개인 대화

서버 `http://127.0.0.1:8000`, OpenAPI `/docs`. 아래 API 경로는 `/api/v1` 아래이며 로그인 이후 `Authorization: Bearer <accessToken>`을 사용한다.

| 메서드·경로 | 동작 |
| --- | --- |
| `POST /auth/login` | `{ "username": "alice", "password": "..." }` → `accessToken` |
| `GET /auth/me` | 현재 사용자 |
| `POST /conversations` | `{ "title": "질문 기록" }` 또는 `{}` |
| `GET /conversations` | 본인의 최근 100개 대화 |
| `GET /conversations/{id}` | 본인의 대화·메시지·답변 상태·인용 |
| `PATCH /conversations/{id}` | 대화 제목 변경 |
| `POST /conversations/{id}/messages` | `{ "content": "질문" }` 저장 전용. **AI 답변을 생성하지 않음** |
| `GET /health` | DB 연결·구현 기능 목록. 공급자 품질이나 문헌 작업자 가동 여부의 보증은 아님 |

관리자도 다른 직원의 대화·실행·이벤트에 접근할 수 없다. 대화에 진행 중인 답변이 있으면 다른 질문/메시지 추가는 409다. 문헌의 공용 정책은 질문 이력 공개와 무관하다.

## 질문·답변 API — 화면 연결 기준

| 메서드·경로 | 동작 |
| --- | --- |
| `POST /conversations/{id}/turns` | `{ "question": "질문", "requestId": "client-unique-id" }` → **202** 실행 접수 |
| `POST /answer-runs` | 같은 계약에 `conversationId`를 추가하는 대체 진입점 |
| `GET /answer-runs/{runId}` | 저장된 상태·답변·인용·오류·검색 진단 |
| `GET /answer-runs/{runId}/events?after=0` | 저장 이벤트와 이후 이벤트를 SSE로 전달 |
| `POST /answer-runs/{runId}/cancel` | 명시적 취소. 저장된 부분 본문 보존 |
| `POST /answer-runs/{runId}/retry` | `{ "requestId": "new-client-id" }` → 가장 최근 실패/취소/중단 질문의 새 실행 |

화면에서 답변을 요청할 때는 **turns만 호출**한다. messages 저장과 turns를 동시에 호출하면 같은 질문을 두 번 저장하게 된다. turns는 사용자 메시지·빈 답변·실행을 한 트랜잭션에서 접수한다.

requestId는 사용자 범위에서 멱등하다. 동일 요청 재전송은 같은 runId를 돌려주며 새 모델 호출을 만들지 않는다. 같은 ID를 다른 질문·대화에 쓰면 409다. 명시적 retry는 새 requestId를 사용하며 원래 사용자 메시지를 재사용하고 새 답변·실행을 만든다. 완료 답변이나 뒤에 새 질문이 있는 과거 답변의 retry는 허용하지 않는다.

```json
{
  "runId": "run_...",
  "conversationId": "conv_...",
  "userMessageId": "msg_...",
  "messageId": "msg_...",
  "requestId": "client-unique-id",
  "status": "accepted",
  "durableSeq": 1,
  "eventsUrl": "/api/v1/answer-runs/run_.../events"
}
```

위 ID는 형식 설명용 예시다. GET 실행 응답에는 `answer`, `error`, `usage`, `retrievalRunId`, `retrieval`이 추가된다. 검색 진단은 실행 소유자만 읽을 수 있고, 질의·후보 ID/점수·최종 전달 근거·문맥 크기·재순위화 사용 여부를 담는다. `no_evidence`는 사용 가능한 근거를 확보하지 못한 상태이며 DB/임베딩 실패와 다르다. 장애는 실패 상태와 `error.phase`로 구분한다. 실행 상세는 짧은 DB 잠금 아래 본문과 durableSeq를 함께 읽어 복원 시 서로 다른 저장 시점의 본문·커서가 섞이지 않게 한다.

### SSE와 각주

```text
id: 4
event: delta
data: {"runId":"run_...","seq":4,"type":"delta","data":{"text":"본문 조각"}}

```

| 이벤트 | data |
| --- | --- |
| `state` | `status`: accepted/retrieving/generating. generating에는 retrievalRunId·evidenceStatus·warnings |
| `citation` | 실제 passageId·sourceRevisionId·documentId·title·locator·excerpt·number |
| `delta` | `text`: 누적할 본문 조각 |
| `complete` | `status: completed`, warnings. **본문과 이벤트 DB commit 성공 후에만 공개** |
| `error` | `status: failed`, error(code/message/retryable/phase) |
| `cancelled` / `interrupted` | 해당 종료 상태와 error |
| `stream_error` | 전송/현재 접근 문제. durable seq/id가 없으며 답변 완료 이벤트가 아님 |

연결 종료 자체는 실행 취소가 아니다. 재연결은 마지막 적용 seq를 `after` 또는 `Last-Event-ID` 헤더로 보내고 이후 이벤트만 적용한다. 두 값이 있으면 큰 값을 사용한다. 저장된 마지막 번호보다 큰 커서는 409다. SSE는 Bearer 헤더가 필요하므로 브라우저 구현은 헤더를 지원하는 스트리밍 HTTP 경로를 사용한다. 연결 복원 시 POST를 자동 반복하거나 새 requestId를 만들지 않는다. 주석 heartbeat는 본문에 표시하지 않는다.

모델 내부 표식 `[[C1]]`은 서버가 **최종 문맥에 실제로 전달한** 구간의 `[[passageId]]`로 정규화한다. citation의 `number`는 해당 답변 내 최초 인용 순서이며 같은 구간은 같은 번호다. 화면은 제공된 citation 맵에 있는 ID만 클릭 가능한 각주로 표시하고 자체적으로 다른 출처를 만들어내지 않는다. 출처 패널은 `/documents/{documentId}/passages?revisionId={sourceRevisionId}`에서 구간 ID를 찾아 보여주고 raw API로 원문을 확인한다. 스트림 중 나눠진 표식은 화면의 누적 Markdown/인용 렌더러에서 처리한다.

없는 alias는 출처 확인 불가로 표시하고 클릭 가능한 근거를 만들지 않는다. 이 검사는 **인용 ID의 실재성과 연결**을 확인하는 것이지 모델 문장의 의미가 원문으로 완전히 입증됐다는 인증이 아니다. 의미적 근거 적합성은 실제 모델 평가에서 별도로 확인한다.

문헌 비활성화는 새 검색뿐 아니라 과거 답변 상세·대화 조회·이벤트 재생에도 반영된다. 근거 접근이 불가능하면 본문/각주를 숨기고 `sourceUnavailable`을 표시하며 재생을 거부한다. 판본만 교체되고 원문이 계속 공개된 경우에는 과거 답변을 `historicalSources`와 경고로 구분한다. 후속 생성에는 비활성 또는 구판본을 사용한 이전 답변을 회사의 현행 사실처럼 재투입하지 않는다. 이미 사용자가 내려받은 내용을 원격 삭제한다는 의미는 아니다.

## 공용 문헌 API

로그인한 직원 누구나 사내 공유가 허용된 자료를 등록한다. 관리자 승인 대기열은 없다. multipart `file` 필수, `title` 선택(기본 파일명), `metadata`는 author/publisher/publishedAt/sourceType/documentForm의 JSON 문자열이다. 파서가 확인한 정보는 processing에 따로 보존한다. 자료 등록은 공식 입장이나 사실 인증이 아니다.

| 메서드·경로 | 동작 |
| --- | --- |
| `POST /documents` | 파일 저장·작업 등록 후 202 |
| `GET /documents` | 최신 100개 문헌·처리 상태 |
| `GET /documents/{id}` | 최신/활성 판본·작업 상태·오류·보류 개수 |
| `POST /documents/{id}/revisions` | 새 파일 판본 등록 |
| `GET /documents/{id}/passages` | 추출문·구간·위치·보류 사유 |
| `GET /documents/{id}/raw` | 해시 검증한 원본 파일 |
| `POST /documents/{id}/reprocess` | 실패한 최신 작업 재시도 |
| `POST /documents/{id}/deactivate` | 검색·원문 접근 제외와 진행 작업 취소 |

raw/passages의 `revisionId`를 생략하면 활성 판본, 없으면 최신 판본을 사용한다. 보류 구간은 원문 확인용으로 표시하되 검색에는 넣지 않는다. 비활성 문헌의 원문·추출문은 노출하지 않으며 상태 목록에는 비활성 항목을 남긴다. 업로드/조회는 전 직원, 기존 문헌의 갱신·재처리·비활성화는 등록자 또는 관리자에게 허용한다.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F 'file=@sample.md' -F 'title=공유 기술자료' \
  -F 'metadata={"sourceType":"internal","documentForm":"original"}'
```

`queued/processing/ready/partial/failed/inactive`와 `searchable`은 구분된다. 새 판본 실패 시 기존 유효 판본은 유지하고 새 판본의 유효 구간 색인이 모두 준비된 뒤에만 활성 판본을 교체한다. 비활성화는 작업 완료나 재시도로 취소되지 않는다. 같은 입력·형식·제목·메타데이터의 반복 업로드는 중복 작업을 만들지 않는다. 실패 재시도는 reprocess로 명시하고, 성공한 파싱/임베딩을 재사용한다. 완료/부분 사용 판본의 강제 재추출 편집기는 없으며 원문 수정은 새 판본으로 등록한다.

## 전처리·검색·작업자

Markdown·UTF-8 텍스트는 기존 구조 보존 청킹을 사용한다. 기본 PDF는 제한 프로세스의 pypdf 텍스트 추출로 페이지 위치를 보존하지만 표·이미지·수식의 완전성은 보증하지 않아 partial로 표시한다. 업로드 상한 20MiB, 기본 PDF/JATS 변환 입력은 5MiB다. 큰 PDF는 기존 Docling 설정을 사용한다.

Docling PDF/JATS는 `OW_PDF_PARSER=docling`, `OW_DOCLING_PYTHON_PATH`, `OW_DOCLING_ARTIFACTS_PATH`를 준비한다. 모델을 자동 설치·다운로드하지 않는다. JATS에는 Docling과 OCR 비활성 설정이 필요하다. 환경 부재나 변환 실패는 원문을 보존하고 오류를 기록하며 다른 변환기로 조용히 바꾸지 않는다.

Jobs는 접수·진행·재시도를, Indexing은 변환·임베딩·원자적 활성화를 담당한다. 중단 문헌 작업은 다음 worker 시작에 실패로 기록하며 명시적 재시도를 기다린다. 일일 승인 예약과 자동 온톨로지 실행은 없다.

RAG는 활성 유효 Passage의 벡터/문자열 후보, 문헌별 다양성, 필요한 원문 조건/불일치 주석, 앞뒤 구간을 사용한다. 문맥 예산은 원문 구간 전체와 메타데이터를 포함해 한 곳에서 적용한다. `OW_RERANKER_MODE=cross_encoder`와 기존 로컬 모델 설정을 사용할 수 있지만 실패 시 경고를 남기고 기본 검색으로 계속한다. Extended·외부 검색·충돌 해결 에이전트·개인 위키는 답변 경로에 없다.

## 검증

```bash
export OW_TEST_DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@127.0.0.1:5432/ontology_assistant_test'
.venv/bin/python scripts/v2/dev.py test -q
cd frontend
npm ci
npm run build
npm test
cd ..
# 실제 Chromium 검증용 추가 도구:
.venv/bin/python -m pip install -r backend/requirements-browser.txt
.venv/bin/python -m playwright install chromium
PYTHONPATH=backend .venv/bin/python -m pytest tests/browser -q
```

로컬 주소의 `_test` DB와 임시 DB 생성 권한이 필요하다. 각 테스트가 만든 임시 DB만 삭제한다. Linux의 Chromium 시스템 패키지가 없으면 Playwright의 `install --with-deps chromium`이 필요할 수 있다. 브라우저 검증은 빌드된 UI·실제 PostgreSQL·Uvicorn·HTTP/SSE·파일 저장·문헌 작업자를 사용하며 임베딩과 생성만 fixture다. `shared-assistant.yml`에 backend 회귀와 frontend 빌드/테스트/Chromium 작업을 함께 둔다. 합성 자료의 XML/스크린샷 산출물은 CI 임시 artifact에만 보관한다.

`tests/foundation`은 업로드·검색·각주·후속 질문·동시 요청·취소·재연결·프로세스 재시작·철회·실제 저장 오류를 검사한다. `tests/browser`는 직원 로그인부터 업로드·질문·각주·원본 파일, 새로고침, 취소/재시도, 미확인 POST 재전송, 연결 실패, 운영 API와 자료 비활성화를 검사한다. 프론트 단위 테스트는 SSE, 안전한 Markdown과 인용, HTTP와 사용자별 저장 경계를 검사한다. 라이브 공급자 스트림 프로토콜 검사는 MockTransport다. 실제 모델 호출·의미 정확도·업무 유용성 평가와 여러 OS/브라우저의 전체 호환성 검증은 별도다.

기본 PDF 텍스트 추출은 실제 실행한다. 구조화 전처리와 JATS 연결은 fixture/계약 검사이며 실제 Docling PDF/JATS 변환 성공을 뜻하지 않는다. 실제 로컬 변환기는 `tests/optional/test_docling_jats.py`에서 명시적으로 따로 검사하며 기본 통과 수에 포함하지 않는다. 유용한 독립 전처리·공급자·재순위화 검사는 `tests/unit`으로 이전했고, 구 모드/승인/개인 위키/외부 조사/구 스키마만을 위한 검사는 삭제 또는 현재 계약 검사로 교체했다. 기본 검증 명령은 `tests/foundation tests/unit tests/evaluation`을 실행한다. Linux 실행에서는 기존 Windows Job Object 전용 검사 한 건을 건너뛴다. 검증에서 제외한 구현을 통과한 것으로 표시하지 않는다.

### 18개 합성 업무 질문과 단계별 추적

`tests/evaluation/cases.json`은 **합성 문헌 12개와 질문 18개**다. 실제 회사 사실·실험·승인·정책이 아니다. 조건 비교, 사내 선택 이유와 범위, 현행/과거/초안, 같은 조건의 미해결 상충, 단위, 근거 부족, 후속 질문, 문헌 속 지시문을 포함한다. 각 문항에는 핵심 사실, 필요한 문헌, 허용 해석/불확실성, 피해야 할 오류를 기록하고 정답 문장을 강제하지 않는다.

```bash
# 기존과 다른 폐기 가능한 로컬 *_test DB 및 임시 DB 생성 권한이 필요하다.
# 출력은 민감한 자료가 섞이지 않도록 합성 데이터에 한정한다.
export OW_EVALUATION_OUTPUT="$PWD/evaluation-output"
PYTHONPATH=backend .venv/bin/python -m pytest tests/evaluation -q -s
```

실제 업로드·worker·PostgreSQL·검색·답변 API를 거치되 임베딩/생성은 명시적 fixture다. `trace.json`에는 코드/자료 해시, 원문, 전처리 구간/위치, 검색 후보, 최종 전달 근거, 실행 ID, 답변/인용, 관측 지연과 수동 검토 칸이 연결된다. `summary.json`의 필요한 문헌 포함 수는 **그 fixture 실행의 관측값이지 의미 검색 정확도나 출시 점수는 아니다.** 근거가 빠졌다면 trace에서 확인하며 정답을 제품 프롬프트에 하드코딩하지 않는다. 답변 품질은 `not_evaluated_fixture`, 현업 유용성은 미평가로 남긴다. 실제 모델·현업 평가에는 별도 승인된 자료·계정·비용과 사람이 필요하다.

초기 fixture 실행(`528947c`)에서는 18문항을 실행했고 필요한 문헌 29건 중 후보에는 29건, 최종 문맥에는 24건이 남았다. Q15~Q18의 5개 문헌 요구가 최종 문맥에서 빠졌다. 이 결과를 통과 점수로 포장하지 않는다. 실제 임베딩 환경에서 후보 선정·재순위화·문맥 예산을 다시 확인할 품질 과제이며, 합성 문항별 정답이나 필수 문헌 ID를 제품 코드에 주입해 맞추지 않는다.

### 격리된 새 Compose 환경 확인

```bash
# Docker가 준비된 Linux 환경. 기존 .env·DB·볼륨 대신 무작위 프로젝트를 만든다.
python3 scripts/v2/compose_smoke.py run --state-dir /tmp/ontology-assistant-smoke
# 생성한 프로젝트의 컨테이너/볼륨만 정리한다. 기존 개발 환경에 down -v를 하지 않는다.
python3 scripts/v2/compose_smoke.py cleanup --state-dir /tmp/ontology-assistant-smoke
```

이 검사는 빈 DB migration → 일반 직원 → 파일 업로드 → 자동 worker 색인 → 웹 프록시 → SSE 답변·실제 각주 → 후속 질문 복원 → 비활성화 반영을 확인한다. HTTP 기반이며 Chromium 화면 검증은 `tests/browser`가 별도로 담당한다. 상태 디렉터리의 생성 비밀값은 공유·커밋하지 않으며 CI에는 비밀값 없는 `result.json`만 보관한다.

## 남은 범위와 공개 전 주의

온톨로지 추출·관리와 다이어그램 렌더링은 **후속·미구현**이다. 옛 스키마/승인 흐름에 결합된 추출 서비스·Entity·라우트는 새 런타임에 남기지 않는다. 실제로 필요한 시점에 독립 기능으로 구현하며, 그 전까지 검색·답변 완료 조건으로 삼지 않는다. 새 판본 업로드 전용 UI, 부분 사용 판본의 수동 교정 편집기도 미구현이다. 새 판본 등록은 현재 API로 가능하다.

2026-10-28의 기존 lockfile 감사에서는 전체 의존성 **6건(critical 2, high 1, moderate 3)**, `npm audit --omit=dev` **0건**이 관측됐다. `vite/vite-node/esbuild/vitest/@vitest/mocker/tinypool` 개발 도구 경로다. 배포용 목록 0건은 개발 환경이나 전체 서비스의 안전 인증이 아니다. 개발/테스트 서버는 비공개 loopback에서만 사용하고, 알려진 경고는 유지보수된 버전의 호환성 검증과 함께 해결해야 한다. loopback 자체가 모든 취약점의 완화책은 아니다. 이번 최종 정리는 강제 major 업그레이드로 범위를 확대하거나 audit 실패를 숨기지 않는다. CI의 감사 결과 파일을 별도 확인한다.

실제 LLM의 의미 정확성·인용 적합성·현업 유용성, 실제 Docling 모델 실행, 다중 API 인스턴스, 모든 OS/브라우저·접근성·부하·보안 검증은 완료되지 않았다. 전사 배포에는 데이터 전송 허용 범위·보관·운영 지원·의존성 보안 검토가 별도로 필요하다. main 병합과 운영 배포는 이 단계에 포함하지 않는다.
