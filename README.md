# 반도체 지식 허브 — 대화 기반 재설계

하나의 대화에서 **위키/분석 답변 형식**과 **Extended 내부 탐색**을 독립적으로 선택합니다. 원문을 먼저 공용 위키로 재작성하지 않고 검색하며, 대화에서 얻은 내용은 개인 위키에 정리합니다. 공용 검토는 문헌 단위입니다.

기준: `fix/wiki-knowledge-flow` / `8e7fb58bd0c051fff99ab97a39278ef2bdc5ba0a`. 이 구현은 별도 브랜치와 개발 DB에서 작성했습니다. 운영 DB·배포·운영 인덱스를 변경하지 않았습니다.

## 먼저 읽을 문서

| 문서 | 목적 |
| --- | --- |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | 실제 모듈·레이어·데이터 저장 위치 |
| [frontend.md](docs/frontend.md), [backend-architecture.md](docs/backend-architecture.md) | 화면별 상태·네트워크 경계, 실제 실행·트랜잭션 경계 |
| [API.md](docs/API.md) | 요청·응답·이벤트·오류·인증 계약 |
| [DEBUGGING.md](docs/DEBUGGING.md) | runId로 검색/문맥/관계/생성 문제를 구분하는 방법 |
| [DECISIONS.md](docs/DECISIONS.md) | 확정 사항, 구현 가정, 중요한 대안과 선택 이유 |
| [MIGRATION.md](docs/MIGRATION.md) | 원문·출처·개념·수정/승인 이력 보존과 전환 절차 |
| [VERIFICATION.md](docs/VERIFICATION.md) | 실제 실행한 검증, 미실행 범위, 알려진 제한 |
| [LIVE_VERIFICATION.md](docs/LIVE_VERIFICATION.md) | GPT-6 Luna 실제 응답·개인 위키·관점·외부 조사·비용과 의미 검토 |
| [COMPOSE_SMOKE.md](docs/COMPOSE_SMOKE.md), [NETWORK.md](docs/NETWORK.md) | 격리된 컨테이너 검증과 공개 문헌 연결 설정 |
| [CHANGE_GUIDE.md](docs/CHANGE_GUIDE.md) | 모델·응답 형식·출처 유형 변경 지점 |
| [구현 계약](docs/design/CONTRACT.md) | 병렬 구현 시 고정한 세부 UI/API 계약 |

## 구현 범위

- 대화 생성·목록·지속 저장·복원, 실제 공급자 SSE 어댑터, 재연결·중복 제출 방지·취소·명시적 재시도.
- 기본 다문헌 검색, PostgreSQL의 정확 코사인 검색과 문자열 검색 결합, 독립적인 Extended 예산.
- 실제 원문 판본과 구간 출처, 근거를 펼치는 관계 카드, 출처별 설명/귀속/조건.
- 별도 외부 조사, 문헌별 카드, 실제 확보 범위, 선택 문헌의 대화 첨부와 검토 후보 등록.
- 문헌 등록·본문 새 판본·메타데이터 정정·승인/보류/반려/철회·일일 색인·명시적 즉시 색인.
- 개인 위키 자동 정리 작업, 검색·판본·사용자 수정·삭제·되돌리기·재생성 제외 기록.
- 다른 프로젝트를 위한 개념·관계·출처별 설명·검색·답변 API와 별도 서비스 계정 권한.

일반 파일 등록은 2MB 이하 Markdown·텍스트입니다. 공개 URL 가져오기는 HTML·PDF·텍스트를 제한적으로 읽습니다. PDF 업로드, Office 문서, OCR·표/그림 해석까지 구현했다는 뜻은 아닙니다. 실제 생성 품질, 공개 URL 본문 확보, 운영 이전·배포의 검증 범위는 [VERIFICATION.md](docs/VERIFICATION.md)를 확인하세요.

## 실행 전제

Python 3.12, Node.js 22 이상, PostgreSQL 16과 pgvector를 사용합니다. 이번 실제 실행은 Node.js 24.22.1에서 확인했습니다. 첫 버전은 **API 프로세스 하나 + DB 작업자 하나**입니다. Redis·분산 큐·로컬 모델은 필요하지 않습니다. `compose.dev.yml`은 새 개발 환경용이며 기존 배포 파일과 볼륨을 사용하지 않습니다.

생성 공급자의 기본값은 `disabled`입니다. 모델을 설정하지 않았을 때 성공한 답변을 꾸미거나 다른 모델로 대체하지 않습니다. `fixture`는 화면/상태 검증 전용이며 화면과 사용량에 명시합니다. 실제 API 실행은 `live`와 명시적인 모델 ID 및 서버의 `OPENAI_API_KEY`가 필요합니다. 브라우저에는 공급자 키를 저장하지 않습니다.

2026-10-26 사용자가 정확한 모델을 **`gpt-6-luna`**로 정정했습니다. 서버 기본 모델도 이 ID이며 effort는 명시적인 `medium`입니다. 제공 계정의 실제 응답에서 반환 모델·effort·service tier와 사용량을 확인했습니다. 대표 작업의 실행 및 제한된 의미 검토 결과는 [실제 검증 기록](docs/LIVE_VERIFICATION.md)에 있으며, 전문가 품질 인증이나 전체 질문의 정확도 보장을 뜻하지 않습니다.

## 로컬 시작

작업 디렉터리에서 실행합니다. 비밀값을 출력하거나 기존 `.env`를 덮어쓰지 않습니다.

```bash
python3 scripts/v2/init_dev_env.py
docker compose --env-file .env -f compose.dev.yml up -d db
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
.venv/bin/python scripts/v2/dev.py migrate --database-name ontology_wiki_dev
.venv/bin/python scripts/v2/dev.py create-user --username my-reviewer --role reviewer
```

계정 비밀번호는 프롬프트에서 입력합니다. 서버가 기본 계정을 자동 생성하지 않습니다. 이미 별도 PostgreSQL이 있다면 `.env`의 `OW_DATABASE_URL`을 그 개발 DB로 설정하고 DB 컨테이너 단계는 생략합니다. 기존 운영 DB를 지정하지 마세요.

Windows 네이티브 실행과 이번 로컬 환경의 접속·종료·재시작 방법은 [Windows 로컬 실행 안내](docs/WINDOWS_LOCAL.md)를 따릅니다.

화면·상태 검증은 `.env`의 `OW_PROVIDER_MODE=fixture`를 명시적으로 설정합니다. 테스트용 임베딩·응답이며 외부 모델을 호출하지 않습니다. 실제 실행은 `OW_PROVIDER_MODE=live`, `OW_GENERATION_MODEL=gpt-6-luna`, `OW_GENERATION_EFFORT=medium`, 서버의 `OPENAI_API_KEY`를 설정합니다. 키는 예제·브라우저·Git에 넣지 않습니다.

각 터미널에서 실행합니다.

```bash
.venv/bin/python scripts/v2/dev.py serve
```

```bash
.venv/bin/python scripts/v2/dev.py worker
```

```bash
cd frontend
npm ci
npm run dev
```

웹은 `http://127.0.0.1:5173`, API 명세는 `http://127.0.0.1:8000/docs`입니다. 개발 서버는 `.env` 변경 후 재시작합니다. 전체 컨테이너 실행은 먼저 DB와 마이그레이션을 준비한 다음 `api worker web`을 시작하세요. 격리된 GitHub Actions 컨테이너 검증의 실행 방법과 확인 범위는 [COMPOSE_SMOKE.md](docs/COMPOSE_SMOKE.md)에 기록합니다.

빈 DB의 첫 작업은 **문헌 등록 → 검토 → 승인 → 선택 문헌 즉시 색인 → 대화에서 질문 → 원문 확인 → 개인 위키 확인**입니다. 문헌 승인과 검색 반영 완료는 별도 상태입니다.

## 기존 임베딩 평가 캐시 사용

129개 문헌과 고정 평가 묶음은 외부 입력입니다. 키 파일과 평가 캐시를 Git에 넣지 않습니다. 제공된 묶음의 SHA-256을 확인한 뒤 개발 DB에만 반입합니다.

```bash
.venv/bin/python scripts/v2/dev.py import-evaluation \
  --corpus-zip /absolute/path/ontology-wiki-sources-129-20261026.zip \
  --evaluation-dir /absolute/path/evaluation \
  --owner my-reviewer --approve-for-development
```

이 명령은 API 호출을 하지 않습니다. 1,088개 원 구간은 보존하고 고정 메뉴 필터로 282개를 제외한 806개를 검색에 사용합니다. 이 반입의 승인은 개발 검증용이며 운영 검토·전문가 인증이 아닙니다.

기존 large 캐시는 `api3072 → prefix1536 + L2` 프로필입니다. 사용할 때 `.env`에 `OW_EMBEDDING_API_DIMENSIONS=3072`, `OW_EMBEDDING_TRANSFORM=prefix_l2`를 설정합니다. 새 자료의 기본 직접 1536차원 프로필과 조용히 섞지 않습니다. 다른 프로필을 쓰려면 해당 프로필로 별도 색인해야 합니다.

## 검증

```bash
.venv/bin/python scripts/v2/dev.py test -q
cd frontend
npm test
npm run build
```

백엔드 통합 테스트는 `_dev` 또는 테스트 DB 안에 **테스트마다 별도 스키마**를 만들고 삭제합니다. `schema_translate_map`으로 테이블 범위를 강제하고 원래 개발 자료를 사용하지 않습니다. 실제 모델 호출은 테스트에 없습니다. `docs/VERIFICATION.md`에서 실제 실행 결과와 API 소량 확인을 구분합니다.

## 데이터와 책임의 경계

원문 파일은 지속 볼륨, 판본·구간·벡터·대화·근거·관계·검토·개인 위키·작업은 PostgreSQL에 보존합니다. 실행 중 질문 벡터·후보 점수·취소 이벤트·짧은 스트림 버퍼는 메모리에 있습니다. API 재시작 후 중단된 생성은 실패 상태로 복구되며 자동으로 새 과금 호출을 시작하지 않습니다.

개인 위키 정리 기본 켜짐과 선택한 공개 외부 문헌의 자동 검토 후보 등록은 문서화한 **초기 가정**입니다. 사용자가 변경할 수 있습니다. 개인 대화/위키/비공개 자료는 공용 검색에 자동 편입되지 않습니다.
