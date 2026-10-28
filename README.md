# Ontology Wiki — 사내 지식 기반 AI 어시스턴트

[목표 아키텍처](docs/ARCHITECTURE.md)가 설계 기준이다. **현재 구현 범위는 1단계: 인증·개인 대화·메시지 저장**이다. 문헌 업로드/자동 색인은 2단계, RAG·생성·스트리밍은 3단계, 새 사용자 화면은 4단계에서 연결한다. 현재 메시지 저장은 AI 답변 생성이 아니다.

## 1단계 실행

Python 3.12와 PostgreSQL 16을 사용한다. 기존 DB를 덮어쓰지 말고 `ontology_assistant_dev` 등 **새 빈 데이터베이스**와 개발 전용 계정을 준비한다. 애플리케이션은 DB 생성·삭제를 수행하지 않는다. v2 데이터/스키마는 이관하지 않는다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
export OW_DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@127.0.0.1:5432/ontology_assistant_dev'
export OW_AUTH_SECRET="$(.venv/bin/python -c 'import secrets; print(secrets.token_hex(32))')"
export OW_PROVIDER_MODE=disabled
.venv/bin/python scripts/v2/dev.py migrate --database-name ontology_assistant_dev
.venv/bin/python scripts/v2/dev.py create-user --username alice
.venv/bin/python scripts/v2/dev.py create-user --username bob
.venv/bin/python scripts/v2/dev.py serve
```

비밀번호는 대화식으로 입력하며 최소 12자다. 자동화에서는 `OW_BOOTSTRAP_PASSWORD`를 사용할 수 있으나 Git·로그에 남기지 않는다. `OW_AUTH_SECRET`은 재시작 후에도 같은 값을 비공개 환경에 유지한다. 위 USER/PASSWORD는 실제 개발 DB 계정으로 바꾼다. Windows에서는 `.venv\Scripts\python.exe`와 PowerShell의 `$env:OW_DATABASE_URL`, `$env:OW_AUTH_SECRET`을 사용한다.

명시적 프로세스 환경변수는 저장소 `.env`보다 우선한다. 이전 `.env`의 DB를 실수로 지정하지 않도록 확인한다. 첫 마이그레이션은 비어 있지 않은 DB를 거부하고, 재실행 시 적용 SQL의 해시를 검증한다. 서버 시작은 마이그레이션이나 기본 계정을 자동 생성하지 않는다.

## 현재 API

API: `http://127.0.0.1:8000`; OpenAPI: `/docs`.

| 메서드·경로 (`/api/v1` 아래) | 동작 |
| --- | --- |
| `POST /auth/login` | `{ "username": "alice", "password": "..." }` → `accessToken`, 사용자 정보 |
| `GET /auth/me` | 현재 사용자 확인 |
| `POST /conversations` | `{ "title": "질문 기록" }` 또는 `{}` → 새 대화 |
| `GET /conversations` | 본인의 최근 100개 대화 |
| `GET /conversations/{id}` | 본인의 대화와 저장 메시지 |
| `PATCH /conversations/{id}` | `{ "title": "변경 제목" }` |
| `POST /conversations/{id}/messages` | `{ "content": "질문 내용" }` → 사용자 메시지 저장. **모델 호출 없음** |
| `GET /health` | DB 연결과 현재 제공 기능 |

개인 API에는 `Authorization: Bearer <accessToken>`이 필요하다. 관리자도 타인의 대화를 조회/변경할 수 없다. 클라이언트가 ownerId/role/autoWiki/Extended 등을 보내면 거부한다. 인증은 기존 JWT·비밀번호 해시 구현을 재사용한다.

## 실제 PostgreSQL 통합 검증

```bash
export OW_TEST_DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@127.0.0.1:5432/ontology_assistant_test'
.venv/bin/python scripts/v2/dev.py test -q
```

테스트 계정에는 테스트용 DB 생성 권한이 필요하다. 로컬 주소와 `_test` DB만 허용하며 각 실행이 만든 무작위 이름의 임시 DB만 삭제한다. 실제 migration/CLI/Uvicorn/HTTP를 사용하고, 서버 프로세스 종료·재시작 후 저장 내용을 확인한다. 모델 호출과 fixture 답변은 없다.

기존 `.github/workflows/shared-assistant.yml`이 같은 PostgreSQL 통합 테스트를 실행한다. `tests/foundation`은 **이번 단계의 명시적 검증 범위**이며, 과거 전체 `backend/tests`의 통과를 뜻하지 않는다. 후속 기능의 테스트는 해당 구현 단계에서 새 계약에 맞게 정리한다.

## 다음 단계의 경계

새 런타임은 `identity`와 `conversations`만 조립하고 v3 초기 스키마에는 사용자·대화·메시지만 있다. 문헌/전처리/색인/RAG/provider 코드와 이전 기능 코드는 후속 작업을 위해 아직 저장소에 남아 있으나 이 런타임에서 등록·실행되지 않는다. 예전 프론트엔드와 worker 명령은 현재 서비스의 사용 경로가 아니다. `worker`, `import-legacy`, `import-evaluation` CLI는 노출하지 않는다. 제거 기능은 해당 영역 이전 단계에서 완전히 정리한다.

사용자의 원문·기존 DB·비밀값을 삭제하지 않았다. 모델 품질·현업 유용성·브라우저 UI는 이번 단계의 검증 범위가 아니다.
