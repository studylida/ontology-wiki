# 구현 검증과 인계 범위

기준일: **2026-10-26**. 기준 커밋: `8e7fb58bd0c051fff99ab97a39278ef2bdc5ba0a`.
구현 브랜치: `feat/conversation-rag-redesign-20261026`.

이 문서는 실제 실행한 검증을 기록합니다. 제품의 실행·상태·권한을 확인한 테스트와 실제 생성 모델의 의미 품질 평가는 서로 다릅니다. 운영 DB·배포·운영 인덱스는 변경하지 않았습니다. 사용자가 모델명을 `gpt-6-luna`로 정정하고 남은 검증과 push를 요청한 뒤 실제 공급자 검증을 추가했습니다. 상세 기록은 [LIVE_VERIFICATION.md](LIVE_VERIFICATION.md)에 있습니다.

## 1. 최종 결과

| 구분 | 실행 결과 | 해석 가능한 범위 | 증거 |
| --- | --- | --- | --- |
| 백엔드 | **200 passed, 44.51s** | PostgreSQL의 격리 스키마, 명시적 fixture/HTTP mock 기반 계약·상태·권한·경쟁 조건 | [backend-tests.xml](verification/backend-tests.xml) |
| 프론트엔드 | **28개 테스트 통과**, TypeScript/Vite production build 성공 | 스트림 파싱, reducer, 출처 그룹, 인용 표시와 화면 계약 | [frontend-tests.json](verification/frontend-tests.json), [frontend.md](frontend.md) |
| 실제 브라우저 | fixture 대표 흐름 및 실제 GPT-6 Luna 대화 복원·스트림 재연결·취소 통과 | 새 생성 1회로 부분 응답을 받은 뒤 같은 run을 복원·중단·재복원. GET 검증은 새 모델 호출 없음 | [LIVE_VERIFICATION.md](LIVE_VERIFICATION.md), [기존 fixture 기록](verification/frontend-browser-result.json) |
| pgvector small | 28개 질문·806개 구간·top 10, 최대 코사인 거리 차이 `1.3834569256854223e-07` | 기존 캐시와 실제 PostgreSQL exact cosine의 일치 | [pgvector-cache-small.json](verification/pgvector-cache-small.json) |
| pgvector large | 같은 28개 질문·806개 구간·top 10, 최대 차이 `1.8492246212087338e-07` | 별도 large 프로필의 저장·검색 일치 | [pgvector-cache.json](verification/pgvector-cache.json) |
| 실제 임베딩 API | large direct1536, 구간 2개, **1회·353 입력 토큰** | 어댑터 요청·차원·실제 usage 수신. 품질 재평가 아님 | [embedding-api-smoke.json](verification/embedding-api-smoke.json) |
| 실제 외부 검색 | Crossref 명시적 단일 검색 200, 문헌 2개 | 서지 메타데이터 확보. 본문을 읽었다고 판단하지 않음 | [research-smoke.json](verification/research-smoke.json) |
| 실제 URL 본문 확보 | 공개 Lam Research 문헌 **200**, 30,371자 부분 텍스트 확보·대화 전송·근거 답변 완료 | 명시적으로 설정한 DoH/egress 경로. 시스템 DNS 기본 경로의 실패도 보존. HTML 동적 내용·표·이미지 완전성은 보장하지 않음 | [research-roundtrip.json](verification/live/research-roundtrip.json), [NETWORK.md](NETWORK.md) |
| 실제 생성 API | **GPT-6 Luna 17회 호출**, 임베딩 8회 추가 | 대화·개인 위키·온톨로지·외부 문헌 설명·취소. 초기 오류 관측과 재검증을 포함하며 모든 호출이 품질 성공이라는 뜻은 아님 | [usage-ledger.json](verification/live/usage-ledger.json), [의미 검토](verification/live/semantic-review.md) |
| Docker / 운영 전환 | 컨테이너 smoke는 GitHub Actions에서 별도 확인, 운영 전환 미실행 | CI 결과는 [COMPOSE_SMOKE.md](COMPOSE_SMOKE.md)에 기록. 운영 DB·원문 저장소 export 미제공 | [MIGRATION.md](MIGRATION.md) |

검증 런타임은 Python 3.12, PostgreSQL 16.15, pgvector 0.8.7, Node.js 24.22.1과 Chromium을 사용했습니다. 공개 개발 DB의 문헌·대화는 통합 테스트의 임시 스키마와 분리했습니다. fixture를 실제 외부 호출이나 무료 운영 모델로 표시하지 않습니다.

최초 인계 전 511개 파일과 후속 게시 대상에서 제공된 키·개발 비밀값의 포함 여부를 확인했습니다. 키·개발 인증 파일·런타임 DB·평가 벡터 캐시는 게시 대상에 포함하지 않습니다. 주요 문서의 상대 링크도 확인했습니다. `git diff --check`의 지적은 이미 적용·해시 고정된 생성 SQL `001_initial.sql`의 줄 끝 공백 300개뿐이었습니다. 기능상 변경 없이 이미 적용된 마이그레이션 바이트를 바꾸지 않기 위해 유지했습니다. 이 파일을 제외한 코드·문서에는 해당 공백 오류가 없었습니다.

## 2. 최초 fixture 브라우저 검증과 후속 실제 검증

1. 로그인 후 빈 대화에서 위키/Extended 꺼짐 기본값을 확인했습니다.
2. 입력 중 모드와 Extended를 바꾸고 초안이 유지되며 요청이 발생하지 않는지 확인했습니다.
3. 외부 조사 공간으로 이동했다가 돌아와 초안·다음 응답 설정이 유지되는지 확인했습니다.
4. 실제 문헌 메타데이터에 있는 발행처 두 개를 선택할 때 API 호출이 발생하지 않는지 확인했습니다.
5. 질문 제출 후 실제 로컬 SSE로 fixture 본문과 출처를 수신했고 위키의 5파트 순서와 fixture 표시를 확인했습니다.
6. 원문 패널을 열어 서버가 현재 권한으로 반환한 실제 저장 문헌을 확인했습니다.
7. 첫 본문 DOM 반영 관측이 `client-metrics`로 정확히 한 번 전송되고 서버에 저장되는지 확인했습니다.
8. 새로고침 후 저장된 메시지·초안·모드를 복원했고 새 생성이나 새 최초 표시 관측이 발생하지 않는지 확인했습니다.
9. 모바일 내비게이션, 가로 넘침 없음, 승인 문헌의 검토 미리보기를 확인했습니다.
10. 명시적인 새 대화에서 빈 입력창과 위키/Extended 꺼짐으로 다시 시작하는지 확인했습니다.

이 절의 초기 `frontend-01`~`frontend-09` 스크린샷은 fixture 문장입니다. 후속 `verification/live/`의 스크린샷과 기록은 실제 GPT-6 Luna 답변이며 서로 구분합니다. fixture 검색 프로필은 제공된 OpenAI 벡터와 다르므로 브라우저 검증의 검색 경로와 아래 실제 OpenAI 캐시 cosine 검증도 구분합니다.

## 3. 백엔드 회귀가 다루는 경계

테스트는 단순히 내부 함수와 같은 값을 재현하기보다 다음 실패·권한·경쟁 조건을 확인합니다.

| 영역 | 검증한 동작 | 주요 테스트 |
| --- | --- | --- |
| 대화·스트림 | 같은 요청 멱등성, 동시 제출, 부분 저장, 명시적 취소·재시도, 재연결, 최종 저장 전 성공 금지, 재시작 중단 | `test_answers.py` |
| 검색·문맥 | 승인 snapshot, 현재 권한·그룹 필터, 기본 다문헌, Extended 시간/호출/문맥 상한, 기본 근거 보존, 중복 근거 예산 | `test_rag_contract.py`, `test_grounding_budget.py` |
| 문헌·색인 | 승인/검색 반영 분리, 변경 입력만 계산, 현재 승인·판본 재검사, 재승인·재시도, 작업자 재시작 상태 복구 | `test_documents_indexing.py` |
| 귀속·과거 답변 | 귀속 메타데이터 정정, source view 무효화, 과거 답변 보존·경고, 현재 접근 철회, service 계정 범위 | `test_metadata_history.py`, `test_identity.py` |
| 개인 위키 | private 소유권, 조건·근거 보존, 사용자 편집 충돌, 삭제/되돌리기 제외 기록, 늦은 결과 저장 전 설정·권한 재확인 | `test_personal_wiki.py` |
| 외부 조사 | 전송의 원자성, 동시 중복 방지, 원래 파일/귀속 보존, 공개 URL·redirect/DNS 검증, 파서 경계 | `test_research_transfer.py`, `test_public_fetch.py` |
| 공급자·사용량 | 실제 Responses 이벤트 형태의 mock, 오류/취소/잘못된 JSON, 실제 usage 보존, fixture 호출 수 분리 | `test_providers.py` |
| 이전 | dry-run 무변경, 원본 바이트·정밀 JSON 수 보존, 중복/변경 export 처리, migration 해시 불변, 트랜잭션 롤백 | `test_legacy_migration.py` |

작업자 강제 중단 이후 Job만 실패하고 문헌이 계속 indexing으로 보이던 문제를 수정했습니다. 복구는 Job과 해당 진행 중 판본을 같은 트랜잭션에서 실패로 전환하고 이미 ready인 활성 판본은 유지합니다. 취소 직후 재시도 사이에 늦게 도착한 공급자 usage도 새 시도와 섞지 않고 이전 시도 이력에 보존합니다.

일반 전체 suite는 실제 OpenAI·Google 생성/임베딩을 호출하지 않습니다. live 비용은 분리한 opt-in 검증에서만 발생했습니다.

## 4. 두 임베딩 프로필과 기존 평가 재사용

129개 문헌, 1,088개 원 구간을 보존하고 고정 메뉴 필터의 제외 구간 282개를 제외한 **806개**를 사용했습니다. 두 모델의 캐시는 같은 원문/구간에 별도 프로필로 연결했습니다. 검증 과정에서 corpus 전체를 다시 임베딩하지 않았습니다.

- small: `openai:text-embedding-3-small:api1536:stored1536:native:v1`
- 기존 large: `openai:text-embedding-3-large:api3072:stored1536:prefix_l2:v1`
- 소량 API 확인의 large: `openai:text-embedding-3-large:api1536:stored1536:native:v1`

large direct1536과 기존3072-prefix 결과는 두 샘플에서 매우 유사했지만 같지 않았습니다. 따라서 동등한 벡터라고 합치지 않고 프로필을 구분합니다. 임베딩 입력·모델·차원·변환이 달라지면 재색인 대상으로 판단합니다.

이번 PostgreSQL 검증의 허용 차이는 `1e-5`였고 두 모델 모두 통과했습니다. 이는 저장/검색 구현의 일치 검증입니다. 새로운 질문 holdout, 실제 답변 품질 향상, Extended 효과를 입증하는 결과가 아닙니다.

이전 단계의 고정 질문 평가에서는 답변 가능 24문항의 all-facets@5가 필터 적용 후 small 17/24, large 18/24였고, 관점 4문항에서는 small 2/4, large 1/4였습니다. 이전 평가를 독립적인 전문가 정답 검증으로 표현하지 않습니다. 원래 평가 묶음과 상세 제한은 이전에 전달한 `ontology-wiki-embedding-evaluation-20261026.zip`을 사용합니다.

### 입력 식별

| 입력 | SHA-256 |
| --- | --- |
| 문헌 ZIP | `2b4c1e438414d10f997b7460112270329547d1c5fea97fd925453e4caac9117d` |
| 고정 chunks | `8e57dd5ef4d81cf8b2d4c3b6c88115b43f79973eb03db9a1ad962ae08fff563c` |
| 제외 필터 | `40f212a2d1c3f6a711bc1d5c8250bb3da37ce387cc1501d033b6dada3fd511f1` |
| 질문 세트 | `0056c803cdef7edbde493fe695d001a2e85e5414d7fa17c5112aa0258d21dc31` |

### 비용

모델 정정 전 초기 구현 단계의 임베딩 API 확인은 1회, 실제 usage 353 입력 토큰입니다. 기록된 단가로 계산한 값은 **약 $0.00004589**이며 추정 비용입니다. 청구서 확정 금액이 아닙니다. 이전 평가의 호출·비용과 합쳐 새로 실행한 것처럼 세지 않았습니다. Google 키는 사용하지 않았습니다. 이후 모델 정정 뒤 진행한 실제 생성·임베딩은 아래 후속 원장에 별도로 기록했습니다.

후속 실제 검증 25회 중 21회의 계산 가능한 비용 합은 **$0.01980707**입니다. 초기 추출 3회는 캐시 쓰기 수명 근거가 부족했고, 취소한 생성 1회는 공급자의 최종 usage를 받지 못했습니다. 따라서 전체 비용은 **null**이며 4회를 0으로 계산하지 않습니다. 25회 중 24회에는 실제 토큰 usage가 있습니다. [usage-ledger.json](verification/live/usage-ledger.json)은 이전 임베딩 평가·초기 353토큰 확인을 제외하며 청구서 금액이 아닙니다.

구현은 실제 usage·확인된 단가가 없는 비용을 null로 보존합니다. 일부 비용만 확인됐으면 knownCost와 미확인 여부를 구분합니다. fixture 비용을 0달러 운영 성능으로 보여주지 않습니다.

## 5. 실제 모델과 외부 문헌 검증

사용자가 정확한 모델을 `gpt-6-luna`로 정정한 뒤 서버 기본 모델을 같은 ID로 맞추고 `medium`을 명시했습니다. 실제 Responses에서 반환한 모델·effort·service tier를 요청값과 별도로 보존합니다. 예제 실행 모드는 기본 `disabled`이며, 운영자가 서버 키와 `live`를 설정해야 모델을 호출합니다.

위키·분석 답변, 개인 위키 신규 정리와 v2 병합, 문헌 기반 개념·관계·출처별 설명, 실제 외부 문헌 설명과 대화 첨부를 검증했습니다. 첫 실문헌 추출의 개념 중복, 조건 없는 대안 관계, 관련성 한계 문자열 처리, Extended 조기 종료, 생성 모델의 화면 표시 문제를 찾아 수정하고 결과를 다시 확인했습니다. 초기 실패·미흡 기록은 삭제하거나 성공으로 바꾸지 않았습니다.

이 결과는 대표 사례의 기능 확인과 제한된 AI 대조 검토입니다. 답변의 인과 조건 압축, HBM 성능 소개 발언의 귀속 문맥, 개인 위키의 일부 요약 손실은 [의미 검토](verification/live/semantic-review.md)에 남습니다. 인용 ID가 유효하다는 이유로 의미까지 정확하다고 판정하지 않습니다.

Crossref의 명시적 단일 검색은 서지 메타데이터를 확보했습니다. 이어서 공개 Lam Research URL의 실제 본문을 읽고 적용성과 한계를 생성해 원래 대화로 전송했습니다. 이 실행 환경에서는 시스템 DNS가 실패하여, 설정한 Google DoH A/AAAA 확인과 공개 IP 고정 연결을 사용했습니다. HTTPS 인증서·원래 호스트/SNI·redirect·IP 검사를 유지했으며 실패 시 다른 경로로 몰래 전환하지 않습니다. 제품 기본은 `system`이고 제한 환경의 opt-in 설정만 `google_doh_egress`입니다.

원문 전체 HTML은 공개 검증 보고서에 복사하지 않았습니다. 확보 크기·해시·부분 읽기 범위·실제 응답과 사용량을 기록했습니다. 첫 관련성 설명의 문자열 형식 오류는 별도 초기 기록에 보존했고, 수정 후에는 완전한 한계 문장 목록을 확인했습니다.

## 6. 첫 버전의 명시적인 기능 범위

- **일반 파일 등록:** 2MB 이하 Markdown·텍스트. 브라우저가 `File.text()`로 읽은 본문을 보내므로 수신 본문은 보존하지만 원래 파일 인코딩/BOM까지 같은 바이트 보존은 아닙니다.
- **URL 본문 확보:** HTML·PDF·텍스트. 다운로드 최대 5MB, PDF 최대 30페이지·80,000자, 파서 CPU/시간/메모리 상한. OCR·표/그림 해석 및 Office 업로드는 포함하지 않습니다.
- **원본 파일 보존:** 평가 ZIP·legacy export·실제 URL 다운로드는 확보한 원본 바이트를 보존합니다. 일반 텍스트 등록과 구분합니다.
- **Extended:** 규칙/문자열 신호로 구체 항목과 측면별 검색 후보를 계획합니다. 문자열 일치가 충분성 종료를 만들지는 않습니다. `semanticSufficiency=not_evaluated`이며 초기 3회·15초·24,000자 예산의 품질/시간/비용 최적화는 미검증입니다.
- **온톨로지 추출:** 첫 버전의 자동 추출은 문헌 앞쪽 최대 16구간입니다. 미추출 구간도 원문 RAG에는 사용할 수 있습니다. 모든 자료의 완전한 온톨로지화를 주장하지 않습니다.
- **직접 선택 문헌 문맥:** 문헌별 최대 24개 구간을 후보로 읽고 전체 문맥 예산을 적용합니다. 문헌 전체를 모델이 읽었다고 표시하지 않습니다.
- **검색 규모:** 현재 corpus에서 exact cosine을 확인했습니다. 대규모 트래픽, 다중 API 프로세스, 분산 작업자 성능은 평가하지 않았습니다.
- **저장 복원:** 짧은 delta 배치가 영속화되기 전 프로세스가 강제로 종료되면 마지막 미저장 조각은 복원되지 않을 수 있습니다. 성공 terminal은 최종 commit 후에만 전송됩니다.

## 7. 이전·실행과 다음 확인

스키마 `001_initial.sql`, `002_legacy_imports.sql`을 별도 개발 DB에 적용했습니다. 기존 운영 스키마를 수정하지 않았습니다. 과거 원문·seed JSON·수정/승인 이력은 코드와 별개로 보존하도록 했고, 구형 실행 코드는 제거했습니다. 실제 운영 export가 없으므로 레거시를 새 활성 도메인에 전부 매핑하거나 운영 트래픽을 전환하지 않았습니다.

이 로컬 환경에는 Docker가 없어 설치한 PostgreSQL과 Python/Node 런타임으로 검증했습니다. 동일 브랜치의 GitHub Actions가 별도 project·DB·볼륨을 생성하여 컨테이너 빌드·마이그레이션·문헌 승인/색인·SSE·API 재시작 복원을 확인하도록 구성했습니다. 실제 Actions 실행 결과와 범위는 [COMPOSE_SMOKE.md](COMPOSE_SMOKE.md)에 기록합니다. 최초 실행은 [README](../README.md), 실제 이전 대조/전환 순서는 [MIGRATION.md](MIGRATION.md)를 따릅니다.

생성 모델 결정과 대표 사용자 작업의 실제 호출 검증은 완료했습니다. 다음 운영 전환에는 실제 export와 권한·원문 저장소의 대조가 필요합니다. 더 넓은 질문 세트의 의미 품질과 Extended 예산 최적화도 후속 평가 범위입니다. 이미 확정된 모드·Extended 기본값, 저장소와 모델을 다시 선택할 필요는 없습니다.

API 계약의 고정 스냅샷은 [openapi.json](api/openapi.json), 운영하지 않은 부분까지 포함한 결정 기록은 [DECISIONS.md](DECISIONS.md), runId 중심의 조사 절차는 [DEBUGGING.md](DEBUGGING.md)에 있습니다.
