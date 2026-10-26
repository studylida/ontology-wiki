# 실제 백엔드 구조와 실행 경계

이 문서는 `backend/knowledge`의 구현을 설명한다. 구형 `backend/app`과의 호환 래퍼를 전제로 하지 않는다. 실행은 단일 API 프로세스와 단일 DB 작업자로 검증하며, 운영 전환과 다중 서버 배포를 완료했다는 뜻은 아니다.

## 1. 조립 지점과 책임

`knowledge.main.create_app(settings, session_factory, embedding_client, generation_client)`가 서비스를 조립한다. 기본 공급자 모드는 `disabled`이며, fixture는 명시적으로 지정해야 한다. 시작 시 테이블이나 기본 계정을 만들지 않는다. 스키마 적용과 사용자 생성은 CLI의 별도 작업이다. `OW_DATABASE_URL`과 `OW_AUTH_SECRET`은 배포 환경에서 지정하며 설정 객체의 문자열 표현에는 이 값들이 나오지 않는다.

| 영역 | HTTP Controller | Application Service | Repository·저장 책임 |
|---|---|---|---|
| 인증 | `identity/router.py` | `IdentityService` | `UserRepository`, 사용자·비밀번호 해시·토큰 버전 |
| 대화 | `conversations/router.py` | `ConversationService` | `ConversationRepository`, 소유 대화와 메시지 조회 |
| 공통 검색 | `rag/router.py` | `RetrievalService` | `DocumentRepository`의 공용 검색·선택 문헌·권한 확인, `OntologyRepository`의 개념 문맥, `RetrievalRun` 기록 |
| 답변 실행 | `answers/router.py` | `AnswerService`, `AnswerExecutor` | `AnswerRepository`, 요청 중복 방지·실행 상태·부분/최종 메시지·이벤트 배치 |
| 문헌 관리 | `documents/router.py` | `DocumentService` | `DocumentRepository`, 원문 판본·구간·검토·메타데이터 변경 |
| 온톨로지 읽기 | `ontology/router.py` | `OntologyService` | `OntologyRepository`, 공개 근거·필터·발행일 범위·조회 정책 |
| 외부 조사 | `research/router.py` | `ResearchService` | `ResearchRepository`와 문헌 Repository를 조합한 전송 단위 작업 |
| 작업 제어 | `jobs/router.py` | `JobService`, indexing/extraction 작업 함수 | `JobRepository`, DB 작업 상태·중복 키·재시도 이력 |
| 개인 위키 | `personal_wiki/router.py` | `PersonalWikiService`와 작업 함수 | 개인 위키 Repository, 소유권·제외·버전·되돌리기 |

Service가 짧은 트랜잭션을 소유하고 엔티티의 도메인 상태를 변경한다. Repository는 접근 조건과 조회/삽입 규칙을 모은다. 복합 문헌 검토·색인 작업은 같은 트랜잭션 안에서 관련 엔티티를 함께 변경한다. DTO는 요청/응답의 형식과 camelCase 직렬화 규칙이며 호출을 통과시키는 별도 실행 계층이 아니다.

외부 모델·다운로드 I/O는 `integrations`의 작은 포트로 분리한다. 임베딩과 생성 호출을 기다리는 동안 SQL 트랜잭션을 열어 두지 않는다. 스트림을 받는 중간 저장은 별도의 짧은 트랜잭션이다.

## 2. 질문에서 답변 복원까지

1. `POST /answer-runs`는 `(owner_id, client_request_id)`의 유일성과 요청 해시를 확인한다. 같은 키·같은 요청은 기존 실행을 반환하며, 다른 내용은 409이다. 대화·사용자 메시지·빈 assistant 메시지·queued 실행을 한 트랜잭션에서 저장한다. 같은 대화의 진행 중인 서로 다른 요청은 409로 알려 대화 순서를 보존한다.
2. `AnswerExecutor`는 현재 계정 권한을 다시 읽고, 저장된 과거 대화와 공통 `RetrievalService`를 사용한다. 응답 모드는 프롬프트 구성만 바꾼다. 모드나 Extended 토글 자체가 요청을 만들지 않는다.
3. 검색은 승인된 활성 공용 판본을 먼저 고정한다. `sourceRevisionIds`는 그 집합을 좁히며 `sourceGroups` 조건, 현재 승인·철회 상태와 교차한다. `documentContextIds`와 대화의 `attachmentIds`는 별도의 요청 전용 문맥이다. 이 문맥은 공용 색인이나 온톨로지 추출 입력으로 승격되지 않는다.
4. 실제 공급자 `output_text.delta`의 경계를 그대로 전달한다. 첫 공급자 이벤트는 본문 없는 관측값일 수 있으며, 실제 본문과 혼동하지 않는다. 완료 후 문자열을 잘라 타이핑처럼 보내지 않는다.
5. 이벤트는 순번을 붙여 메모리에서 즉시 전달하고 `answer_event_batches`에 배치 저장한다. 기본 flush 조건은 512자 또는 0.4초이며, 다음 공급자 이벤트가 없더라도 타이머가 이미 받은 부분을 저장한다. 최종 답변·사용량·terminal 이벤트를 commit한 뒤 `run.completed`를 공개한다.
6. 취소는 실행 상태와 in-memory 취소 신호를 함께 변경한다. 이미 도착한 부분 본문은 보존하고 늦게 도착한 토큰은 버린다. 재시도는 별도 실행/메시지와 `retryOfRunId`를 만든다. SSE 재접속은 재생성하지 않는다.
7. 프로세스 중단 후 queued/running 실행은 `interrupted`로 복구한다. 저장되지 않은 마지막 이벤트 구간은 재현했다고 주장하지 않는다. 앞선 재생 커서는 409로 알려 실행 상세를 다시 읽게 한다.

GET 대화·실행 및 SSE 재생은 현재 출처 접근 권한을 재확인한다. 철회된 출처가 포함되면 파생 본문 전체를 제한한다. 메타데이터만 정정된 경우 본문을 자동 수정하지 않고 과거 답변 경고를 추가한다. 당시 source-view 스냅샷은 DB에 남기되 현재 조회/재생의 일반 카드에서 제외한다. 후속 답변은 앞선 답변의 출처 의존성도 보존한다.

## 3. Extended와 문맥 예산

기본 검색은 여러 문헌을 대상으로 한다. Extended는 원리·목적·조건·한계·대안·순서·비교·사례 등 요청에 나타난 측면을 규칙으로 분리한다. 모호한 질문에는 정의와 적용 조건을 확인하는 제한된 계획을 만든다. 새로운 특정 개체나 외부 검색어를 임의로 만들지 않는다.

추가 탐색은 초기 검색 이후 별도 시간 예산을 시작한다. 주변 구간, 부족한 측면의 내부 추가 query, 등록된 개념의 한 단계 관계 근거를 사용한다. 기본 설정은 추가 query 최대 3회, 추가 탐색 15초이다. 남은 시간은 `asyncio.timeout`으로 실제 호출에 적용한다. 시간이 끝나도 먼저 확보한 기본 근거는 보존한다. 새 구간이 없거나, 계획/호출/문맥 예산이 끝나거나, 요청 측면의 관측 가능한 coverage 목표에 도달하면 종료한다.

coverage는 문자열 측면 신호와 실제 확보 구간의 기록이다. 일치한 구간은 `candidate_found`, 일치하지 않으면 `unknown`이며 의미가 충분함이나 정답성을 인증하지 않는다. v2는 온도·압력·휨·수율·치수·시간 등 질문의 구체 항목을 일반 측면보다 먼저 계획한다. 문자열 일치만으로 추가 검색을 생략하거나 `coverage_target_reached`로 종료하지 않는다. `semanticSufficiency=not_evaluated`를 반환하고 query 내용·상태·시간·결과 수, 종료 사유와 사용 예산을 `RetrievalRun.result`에 기록한다.

원문 구간과 한 단계 관계/관점의 원문 근거는 `rag/grounding.py`에서 passage ID로 중복 제거한다. 생성 문맥에 검토할 관계는 최대 8개, 관점은 최대 12개이며, 카드에는 원문을 다시 붙이지 않고 선택된 `evidenceRefs`를 넣는다. 근거가 문맥 예산에 들어오지 않는 카드는 생성 프롬프트에서 제외하고 부족을 알린다. 저장된 원래 카드와 근거는 삭제하지 않는다.

직렬화된 evidence JSON의 기본 상한은 24,000자이다. 전체 프롬프트 본문은 기본 64,000자 이내이며, 최근 대화 최대 8개·각 최대 6,000자 중 실제 남은 공간에 들어가는 부분만 사용한다. 이 수치는 첫 버전의 조정 가능한 가정이다. 토큰 한도나 의미 정확성 검증을 대신하지 않는다. 실제 모델 토큰은 공급자의 응답 usage에서만 측정한다.

선택 문헌·첨부는 첫 버전에서 문헌별 최대 24개 보존 구간을 요청 문맥 후보로 읽는다. 전체 문헌을 모델이 읽었다는 뜻이 아니다. 공용 온톨로지의 초기 추출은 최대 16개 구간으로 제한되며, 추출되지 않은 원문 구간도 공용 RAG에서 검색할 수 있다.

## 4. 문헌 승인·색인·관점 변경

원문 파일은 내용 해시로 식별하는 파일 저장소에 보존하고, 임시 파일을 완성한 후 원자적으로 연결한다. PostgreSQL에는 문헌/불변 판본, 구간·locator·입력 해시, 벡터, 현재 활성 판본 포인터, 검토 이력을 저장한다. pgvector 저장 차원은 현재 1536이며 모델·API 차원·저장 차원·변환을 포함하는 profile ID가 다른 벡터는 혼합하지 않는다.

승인은 검색 활성화와 별도이다. 일일 일정과 관리자/검토자의 즉시 요청은 같은 색인 경로를 사용한다. 변경되지 않은 임베딩 입력과 같은 프로필/범위는 재사용한다. 새 판본의 모든 구간 처리가 끝나고 승인·소유 범위·메타데이터를 다시 확인한 후 활성 포인터를 전환한다. 기존 활성 판본의 재색인 중에는 해당 판본의 검색을 중단시키지 않는다.

철회·보류·반려는 공용 검색 조건에서 즉시 제외한다. 철회 후 재승인도 다시 색인 활성화를 기다린다. 같은 내용이면 기존 벡터를 재사용할 수 있다. 실패/취소 작업의 명시적 재시도에는 이전 상태·오류·usage를 `attemptHistory`로 남긴다. 작업자 중단 복구는 job 상태와 진행 중 판본의 index 상태를 같은 트랜잭션에서 실패로 바꾸며, 이미 ready인 활성 판본은 유지한다.

source-view는 개념·측면·판본·근거와 메타데이터 버전/해시에 연결된 AI 파생 설명이다. 문헌 승인은 관계나 source-view의 사실 인증이 아니다. 출처 메타데이터 변경은 이전 view를 superseded로 표시하고 새 정리 작업을 등록한다. 동일한 본문 임베딩을 다시 계산하는 이유로 사용하지 않는다. 공용 추출 작업에는 사적인 질문이나 대화 조건을 전달하지 않는다.

온톨로지·관점 추출과 개인 위키 정리 프롬프트에는 실제 Pydantic 응답 모델의 JSON Schema를 함께 전달한다. 온톨로지의 조건은 문자열 또는 null, 개인 위키의 조건·한계는 문자열 배열이라는 차이와 길이 제한을 생성 전에 명시한다. 반환값은 같은 모델로 검증하며, 프롬프트 지침을 공급자 측의 강제 structured output 보장으로 표현하지 않는다.

초기 실제 3문헌 추출에서 자유로운 유형명 때문에 같은 HBM이 두 ID로 나뉘고, Wire Bonding의 공통 별칭도 재사용되지 않는 결함이 확인됐다. 이후 `source-extract-v2-canonical-identity`는 `process/device/structure/material/equipment/property/technology/concept`의 작은 유형 집합을 사용한다. 확인한 소수의 기존 유형명만 명시적으로 대응시키며, 알 수 없는 유형을 문구 유사도로 추정하지 않는다. `ontology/identity.py`는 NFKC·대소문자·연속 공백을 정규화한 이름과 명시적 별칭의 유일 후보를 찾는다. 현재 공개 근거가 있는 후보가 하나이며 유형도 일치할 때만 재사용한다. 여러 후보·유형 충돌·미확인 유형은 `identityIssues`에 보류 사유를 남기고 새 중복 개념을 만들지 않는다. 기존 ID·유형·설명·출처를 자동 병합하거나 덮어쓰지 않는다.

`OntologyRepository`의 schema별 트랜잭션 advisory lock은 개념 조회·생성의 짧은 저장 구간만 직렬화한다. 공급자 호출 중에는 잠금을 보유하지 않는다. 새 출처에서 확인한 명칭은 해당 source-view의 `extractor.sourceLabels`에 남겨 다음 추출의 식별에 사용할 수 있으며, 그 문헌의 철회·판본 변경·메타데이터 변경으로 유효한 공개 근거가 사라지면 식별 후보에서도 제외한다. 출처별 설명·조건·귀속은 같은 canonical ID 아래 각각 보존한다.

단순 비교가 `alternative_to`로 승격된 초기 결과도 확인하여, 명시적인 공통 목적·적용 범위·조건이 근거에 있을 때만 추출하도록 보완했다. `alternative_to`의 conditions가 null 또는 공백이면 관계 저장을 보류하고 `relationIssues`에 기록한다. `is_a`와 `part_of`도 각각 실제 하위범주와 구성 관계를 요구한다. 이 계약·출처 검증은 관계의 의미 정확성을 인증하는 절차가 아니며, 나머지 정상 개념·관점까지 폐기하지 않는다.

## 5. 외부 조사 전송의 원자성

외부 검색은 사용자가 입력한 단일 query와 제한된 결과 수로 수행한다. 공개 HTTPS 가져오기는 DNS 결과와 모든 redirect를 검사하고 공개 IP에 고정한다. DNS 확인 실패는 재시도 가능한 502이며, 비공개 IP·자격 증명 URL·허용되지 않은 스킴은 422이다. 환경의 DNS 제약을 우회하는 경로는 없다.

외부 조사의 확인 범위는 metadata/abstract/partial/full로 저장한다. 읽지 못한 본문에 관련성 판단을 만들지 않는다. 전송은 소유 대화와 조사 항목을 잠근 하나의 트랜잭션에서 문헌/판본/첨부/전송 포인터를 함께 저장한다. 동시 전송도 같은 항목의 문헌과 첨부를 중복 생성하지 않는다. 원래 내려받은 파일 참조와 발행처·저자·귀속 근거를 보존한다. 개인 질문과 조건은 공용 문헌 본문/메타데이터에 복사하지 않는다.

## 6. 계측과 검증 범위

| 관측값 | 실제 측정 지점 |
|---|---|
| retrievalMs | RetrievalService 시작부터 결과 저장까지 |
| generationMs | 생성 stream 시작부터 완료/실패/취소까지 |
| providerEventMs | durable 실행 생성 뒤 orchestration 시계 기준 첫 실제 공급자 event |
| firstTextMs | 같은 시계 기준 첫 nonempty 실제 본문 delta |
| clientFirstVisibleTextMs | 소유 브라우저가 첫 표시를 신고한 최초 1회 값, `browser_untrusted` 표기 |
| promptCharacters / groundingCharacters | 실제 구성한 프롬프트 본문과 직렬화 evidence JSON 길이 |
| 모델·effort·토큰·비용 | 실제 공급자 stream/embedding usage와 명시된 가격 근거 |

미확인 비용·토큰은 null이다. 알려진 부분 비용과 비용 미확인 호출 수를 구분한다. fixture는 실제 외부 API calls=0, fixtureCalls를 별도로 기록하고 비용/토큰을 실제 모델 값으로 꾸미지 않는다. 답변 실패·구조화 JSON 실패·취소된 작업의 늦은 usage도 보존한다.

생성 요청은 `service_tier=default`를 명시한다. 실제 반환 모델이 `gpt-6-luna`이고 반환 서비스 등급이 `default`일 때, 공급자의 `input_tokens`에서 `cached_tokens`와 `cache_write_tokens`를 뺀 일반 입력, 캐시 읽기, 30분·12시간 쓰기, 전체 출력 토큰을 각각 계산한다. 반환된 `cache_write_tokens_details`의 두 수명을 우선 사용한다. 해당 세부값을 공급자가 생략한 경우, `gpt-6-luna` 요청에 명시한 `prompt_cache_options.ttl=30m`와 별도 breakpoint가 없다는 사실을 근거로 쓰기 총량을 계산하고 `cacheWriteLifetimeSource=request`로 구분한다. 응답 설정의 TTL이 있으면 요청값보다 우선한다. 다른 수명 설정이 섞일 가능성, 사용량 누락·불일치가 있으면 비용은 null이며 기존 호출에 설정을 소급 적용하지 않는다. 272,000 입력 토큰 초과 시 요청 전체의 입력·캐시 가격은 2배, 출력 가격은 1.5배다. 이는 [모델 가격표](https://developers.openai.com/api/docs/models/gpt-6-luna)와 [캐시 사용량 정의](https://developers.openai.com/api/docs/guides/prompt-caching)를 2026-10-26에 확인한 공개 Standard 텍스트 가격의 추정값이며, 계정 청구서·세금·개별 계약·지역 할증을 확인한 금액은 아니다. 원시 사용량과 항목별 `costBreakdown`을 함께 저장한다.

`requestedEffort`와 `requestedServiceTier`는 요청 설정, `effectiveEffort`와 `serviceTier`는 실제 응답에 포함된 값이다. 응답이 값을 주지 않으면 요청값이나 모델 기본값으로 채우지 않는다. 기존 `effort`는 요청값이라는 의미를 유지한다. 각 호출과 답변 사용량 집계에 이 구분을 보존한다.

자동 테스트는 실제 PostgreSQL의 매번 다른 임시 schema와 `schema_translate_map`을 사용하며, 테스트의 모델 호출은 명시적 fixture 또는 HTTP mock이다. 성공한 mock/fixture 스트림은 실제 생성 모델 품질·가용성·운영 요금 검증을 뜻하지 않는다. 실제 공급자 실행 결과는 별도 실행 기록으로 확인하며, 운영 DB 전환·배포는 이 테스트 범위 밖이다.

`scripts/v2/verify_live_ontology.py`는 명시적인 `--allow-live`와 판본 목록을 받은 경우에만 local `_dev` DB의 새 UUID schema에서 실제 추출을 검증한다. public의 승인·활성 판본은 읽기 전용으로 가져오고, 소유자는 기존 인증정보 없이 비활성 대체행으로 복제한다. schema 매핑과 테이블 수를 확인한 뒤 문헌별 생성 호출을 순차적으로 한 번씩 수행하고 첫 실패에서 중단한다. 보고서는 호출별 usage와 개념·관점·관계·조건·근거 ID를 담으며 전체 원문이나 비밀값은 제외한다. `--keep-schema`가 없으면 자신이 만든 schema만 정리한다. 이 스크립트의 guard 테스트는 실제 모델 호출을 수행하지 않는다.
