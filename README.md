# Ontology Wiki — 사내 지식 기반 AI 어시스턴트

[목표 아키텍처](docs/ARCHITECTURE.md)가 설계 기준이다. **현재 구현 범위는 1·2단계: 인증·개인 대화와 공용 문헌 업로드·자동 색인**이다. RAG 답변·스트리밍은 3단계, 새 사용자 화면은 4단계에서 연결한다. 현재 메시지 저장은 AI 답변 생성이 아니다.

## 실행과 스키마

Python 3.12, PostgreSQL 16 및 pgvector가 필요하다. API와 작업자는 같은 DB와 지속 원문 저장 경로를 사용한다. 새 환경은 별도의 빈 개발 DB로 시작한다. 이미 1단계 v3 DB가 있다면 같은 명령으로 `002_documents.sql`만 추가 적용하며 대화 기록은 유지한다. v2 DB는 이관하지 않는다. 기존 DB·원문을 삭제하는 명령은 제공하지 않는다.

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
# 위와 같은 환경변수를 사용하는 별도 셸에서:
.venv/bin/python scripts/v2/dev.py worker
# 또는 대기 작업 한 건만 처리:
.venv/bin/python scripts/v2/dev.py worker --once
```

`fixture`는 동작 검증용 1536차원 해시 벡터이며 의미 검색 품질을 보증하지 않는다. 명시적 `live` 설정은 승인된 공급자 계정·자료·비용 범위에서만 사용한다. `disabled`이면 파싱 후 임베딩 구성 오류가 기록되며 fixture로 자동 대체되지 않는다. API 기동은 계정/마이그레이션/작업자/모델 호출을 자동 시작하지 않는다. **작업자를 실행하지 않으면 업로드는 대기 상태다.**

비밀번호는 대화식으로 최소 12자를 입력한다. `OW_BOOTSTRAP_PASSWORD`는 자동화용이며 Git·로그에 남기지 않는다. `OW_AUTH_SECRET`은 재시작 후에도 같은 비공개 값을 유지한다. 명시적 프로세스 환경변수는 `.env`보다 우선한다. Windows에서는 `.venv\Scripts\python.exe`와 PowerShell의 `$env:...`를 사용한다. pgvector 확장 설치 권한이 없는 DB 계정은 관리자가 확장을 먼저 설치해야 한다.

## 인증과 개인 대화 API

서버 `http://127.0.0.1:8000`, OpenAPI `/docs`. 아래 경로는 `/api/v1` 아래다. 로그인 이후 `Authorization: Bearer <accessToken>`을 사용한다.

| 메서드·경로 | 동작 |
| --- | --- |
| `POST /auth/login` | `{ "username": "alice", "password": "..." }` → `accessToken` |
| `GET /auth/me` | 현재 사용자 |
| `POST /conversations` | `{ "title": "질문 기록" }` 또는 `{}` |
| `GET /conversations` | 본인의 최근 100개 대화 |
| `GET /conversations/{id}` | 본인의 대화·메시지 |
| `PATCH /conversations/{id}` | 대화 제목 변경 |
| `POST /conversations/{id}/messages` | `{ "content": "질문" }` 저장. 생성 호출 없음 |
| `GET /health` | DB 연결·구현된 기능 목록. 작업자 가동 여부를 보증하는 지표는 아님 |

관리자도 다른 직원의 개인 대화에 접근할 수 없다. 문헌을 공용으로 올린다는 사실은 질문 이력 공개와 무관하다.

## 공용 문헌 API

**로그인한 직원 누구나 사내 전체 공유가 허용된 자료를 등록한다. 승인 대기 단계는 없다.** `multipart/form-data`의 `file`은 필수, `title`은 선택이며 생략하면 파일명이다. `metadata`는 JSON 문자열로 author/publisher/publishedAt/sourceType/documentForm만 받는다. 파서가 확인한 정보는 `processing`에 별도로 보존한다. 자료 등록·검색 반영은 회사의 공식 입장이나 사실 인증이 아니다.

| 메서드·경로 | 동작 |
| --- | --- |
| `POST /documents` | 파일 저장·작업 등록 후 **202**. 검색 완료가 아님 |
| `GET /documents` | 최신 100개 문헌과 처리 상태 |
| `GET /documents/{id}` | 최신 판본, 활성 판본, 작업 진행·오류·보류 개수 |
| `POST /documents/{id}/revisions` | 같은 문헌의 새 파일 판본 등록 |
| `GET /documents/{id}/passages` | 보존 추출문·구간·원문 위치·보류 사유 |
| `GET /documents/{id}/raw` | 해시 검증한 원본 파일 다운로드 |
| `POST /documents/{id}/reprocess` | 실패한 최신 작업 재시도. pending/running/succeeded는 중복 실행하지 않음 |
| `POST /documents/{id}/deactivate` | 검색·원문 열람 제외 및 대기/진행 작업 취소 |

`raw`와 `passages`는 `?revisionId=...`를 받을 수 있다. 생략하면 활성 판본, 없으면 최신 판본이다. 추출문 조회에 표시되는 보류 구간은 관리·확인용이며 검색에서 제외된다. 비활성 문헌의 원문과 추출문은 노출하지 않는다. 전체 상태 목록에는 비활성 항목을 남긴다.

업로드·조회는 모든 직원에게 허용하지만, **기존 문헌의 갱신·재시도·비활성화는 등록자 또는 관리자**에게만 허용한다. 이는 업로드 승인 체계가 아니라 타인의 공유 자료 변경 방지를 위한 최소 경계다. 부서별 ACL과 승인 역할은 만들지 않았다.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F 'file=@sample.md' -F 'title=공유 기술자료' \
  -F 'metadata={"sourceType":"internal","documentForm":"original"}'
```

응답의 `documentId`로 상태를 조회한다. `queued/processing/ready/partial/failed/inactive`와 `searchable`을 구분한다. 새 판본이 실패해도 이전 유효 판본이 있으면 `latestRevision`은 실패이지만 `activeRevision`과 `searchable`은 유지된다. 새 판본의 모든 유효 구간 색인이 준비된 뒤 활성 판본을 한 번에 전환한다. 비활성화는 자동 재시도로 취소되지 않는다.

같은 파일·해석 형식·제목·메타데이터는 중복 판본/작업을 만들지 않는다. 실패한 등록을 반복 업로드해도 자동 재시도하지 않으며 `reprocess`를 사용한다. 파싱 성공 결과와 임베딩 캐시는 실패 후 재시도에 재사용한다. 완료/부분 사용 판본의 구간을 수동 교정하거나 강제로 재추출하는 편집기는 현재 제공하지 않는다. 원문 수정은 새 판본으로 등록한다.

## 전처리·작업자 경계

Markdown·UTF-8 텍스트는 기존 문단/표 청킹을 사용한다. 기본 PDF는 별도 제한 프로세스의 pypdf 텍스트 추출이며 페이지 위치를 유지하지만 **표·이미지·수식의 완전성을 보증하지 않으므로 partial**로 표시한다. 업로드 상한은 20MiB이고 기본 PDF/JATS 변환 입력 한도는 5MiB다. 큰 PDF는 기존 Docling 설정을 사용한다.

Docling PDF/JATS는 기존 변환기·원문 위치·표/수식 품질 보류 기능을 연결했다. `OW_PDF_PARSER=docling`, `OW_DOCLING_PYTHON_PATH`, `OW_DOCLING_ARTIFACTS_PATH`를 명시적으로 준비해야 하며 모델을 자동 설치/다운로드하지 않는다. JATS에는 Docling과 OCR 비활성 설정이 필요하다. 실행 환경이 없거나 파싱에 실패하면 원문은 보존하고 오류를 기록한다. 정상 처리로 위장하거나 다른 파서로 조용히 바꾸지 않는다. 정상 JATS DOCTYPE은 허용하고 엔티티 확장·외부 파일 접근은 기존 정규화기에서 차단한다.

Jobs는 접수·진행·재시도를, `indexing/service.py`는 변환·임베딩·색인 활성화를 담당한다. 이전 승인/일일 예약/자동 온톨로지 색인 코드는 실행 경로에서 제거했다. MVP 작업자는 DB advisory lock으로 한 번에 하나만 실행하며 여러 인스턴스가 중복 소비하지 않는다. 작업자 중단 후 다음 시작 시 running 작업을 실패로 기록하고 명시적 재시도를 기다린다. 자동 유료 재호출을 숨기지 않는다.

## 검증과 다음 단계

```bash
export OW_TEST_DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@127.0.0.1:5432/ontology_assistant_test'
.venv/bin/python scripts/v2/dev.py test -q
```

테스트 계정에는 임시 DB 생성 권한이 필요하다. 로컬 주소의 `_test` DB만 허용하며 각 실행이 만든 임시 DB만 삭제한다. 기존 `shared-assistant.yml`에서 `tests/foundation`을 실행한다. 실제 PostgreSQL·Uvicorn·HTTP·파일·작업자·프로세스 재시작을 사용하고 임베딩만 명시적 fixture다. PDF 텍스트 추출은 실제 수행한다. 구조화 전처리와 JATS 호출 연결은 fixture/계약 검사이며 **실제 Docling PDF/JATS 변환 성공을 검증했다는 뜻이 아니다.**

3단계는 `DocumentRepository.resolve_snapshot/search_candidates/search/get_neighbors`와 실제 활성 구간·원문 API를 사용해 답변 경로를 연결하면 된다. API 서버에 답변/RAG 라우트, 개인 위키, 외부 조사, 자동 온톨로지 작업은 등록하지 않았다. 전처리 핵심 자산은 재사용하고 이후 이전 대상인 RAG·답변·옛 화면 소스는 아직 남아 있다. 옛 전체 backend 테스트·프론트엔드와 새 계약의 호환을 주장하지 않는다. 실제 모델 품질·현업 유용성·브라우저 UI는 이번 검증 범위가 아니다.
