# 오류와 품질 문제를 찾는 방법

## 1. 먼저 runId와 상태 확인

웹의 답변 실행 정보에서 runId를 확인합니다. `GET /api/v1/answer-runs/{id}`는 현재 사용자 권한으로 저장한 메시지, status/error, retrievalRunId, lastSeq, usage, metrics, 제출 설정을 반환합니다. 다시 읽기나 SSE 재연결은 새 모델 호출이 아닙니다.

`configuration_blocked`는 키/모델/프로필 설정 확인이 필요하다는 뜻입니다. 이를 fixture나 다른 모델로 자동 대체하지 않습니다. `fixture` 배지가 있다면 저장·스트림 흐름을 검사한 것이며 실제 생성 품질 결과가 아닙니다.

## 2. 문제를 네 곳으로 나누기

| 증상 | 확인할 기록 | 수정할 위치 |
| --- | --- | --- |
| 필요한 문헌을 못 찾음 | retrieval_runs의 고정 판본 집합, appliedFilters, queries, hit 수, 그룹별 missing, 검색 프로필 | documents/repository, rag/service·context |
| 문헌은 찾았지만 조건이 빠짐 | hits의 locator/text/contextTruncated, 주변 구간, 문맥 예산, 과거 질문 문맥 | rag/context, documents/parsing |
| 상하위·순서·대안 또는 회사 귀속이 틀림 | relation의 type/방향/conditions/evidence, sourceView metadataVersion/hash·author/attributedTo | ontology/extraction·repository, documents metadata correction |
| 근거와 다른 답변을 만듦 | 실제 입력 문맥, 생성 모델/effort, output delta, 출처 연결, 완료/부분 여부 | answers/prompt, integrations/providers, 생성 평가 질문 |

단순 인용 문자열·줄 번호 불일치로 정상 설명을 전부 버리지 않습니다. 먼저 실제 판본·구간 ID 연결과 접근 범위를 검사한 뒤, 의미가 근거와 맞는지는 별도 평가합니다. 검색 hit 수나 confidence처럼 보이는 숫자를 참/거짓 인증으로 사용하지 않습니다.

## 3. 실제 시간·사용량 측정

- 검색: RetrievalService 진입, 각 실제 query embedding 시작/종료, SQL/문맥 작업을 포함한 `timings.totalMs`와 queries 기록.
- 생성: AnswerExecutor의 공급자 스트림 시작~완료/실패/취소 구간 `generationMs`.
- 첫 공급자 이벤트: 실제 상류 SSE 이벤트 수신 시 `providerEventMs`. response.created 같은 본문 없는 신호일 수 있습니다.
- 첫 본문: 첫 nonempty 실제 텍스트 delta 수신 시 `firstTextMs`. 상태 메시지·카드 준비를 답변 시작으로 세지 않습니다.
- 브라우저 첫 표시: 이번 브라우저의 새 submit부터 첫 nonempty 본문 DOM 반영 뒤 double requestAnimationFrame까지 관측한 `clientFirstVisibleTextMs`. 클라이언트 관측값이며 정확한 하드웨어 paint 측정이나 신뢰된 청구 자료는 아닙니다. 복원/replay는 새 관측값을 전송하지 않습니다.
- 토큰/모델: 공급자가 반환한 실제 usage와 실제 model ID를 어댑터에서 기록합니다. effort는 제출 시의 서버 설정 snapshot입니다.
- 호출 수: 실제 외부 API 시도/관측을 구분하고 fixtureCalls는 실제 API calls와 분리합니다. 검색과 생성, 개인 위키/공용 추출 작업은 별도 component/job usage를 가집니다.
- 비용: 확인한 단가와 실제 usage로 계산한 경우 `estimated`, 단가 기준일·출처를 보관합니다. 최종 청구액으로 단정하지 않습니다. 취소·통신 중단·미설정 단가의 비용은 null입니다. 확인된 일부 비용은 knownCostUsd로 따로 볼 수 있습니다.

원문 텍스트·질문·개인 조건은 DB 진단 기록의 소유 범위를 따릅니다. 운영 로그에는 runId/jobId/오류 코드 등 식별값을 남기고 provider credential·원문 전체를 출력하지 않습니다.

## 4. 스트림과 재시도

1. 수신 seq와 run의 lastSeq를 비교합니다. 중복 seq는 버리고 이후 이벤트를 요청합니다.
2. 연결이 끊겼다고 POST /answer-runs를 다시 호출하지 않습니다. GET run + events?after=N으로 복원합니다.
3. 공급자가 중간에 끝났으면 실패/부분 상태입니다. 본문이 있다는 이유로 completed로 바꾸지 않습니다.
4. 사용자의 명시적 재시도만 새 clientRequestId/retryOfRunId로 실행합니다.
5. 취소는 상류 요청을 닫고 늦은 텍스트를 성공 결과에 덧붙이지 않습니다. 이미 확인한 usage는 보존합니다.
6. 최종 DB 저장 실패는 성공 terminal을 보내지 않습니다. 프로세스 재시작은 실행 중이던 요청을 interrupted로 기록합니다.

짧은 배치 저장 사이에 프로세스가 강제로 죽으면 마지막 미저장 조각은 복원되지 않을 수 있습니다. 이 범위를 없다고 주장하지 않습니다. 운영에서 필요한 손실 허용 범위를 정한 뒤 flush 예산을 조정하세요.

## 5. 문헌이 승인됐는데 검색되지 않을 때

문헌의 reviewStatus와 indexStatus를 각각 확인합니다. 승인 후 일일 작업을 기다리거나 검토자가 즉시 색인을 요청할 수 있습니다. Job의 실제 processed/total과 error를 봅니다. query profile과 passage profile이 다르면 벡터가 검색되지 않습니다. 이 경우 기록에 문자열 검색이라는 경고가 남습니다.

같은 원문에 여러 프로필을 보관할 수 있으나 한 요청에서는 한 프로필만 사용합니다. 모델을 바꾼 뒤 예전 벡터에 새 모델의 질문 벡터를 섞지 않습니다. 원문 body/title prefix가 바뀌면 입력 해시도 달라집니다. 본문 정제 후 예전 벡터를 그대로 연결하지 않습니다.

일일 작업은 timezone과 hour 설정을 따릅니다. 예약 단위와 무관하게 withdrawal/current ACL은 즉시 반영됩니다. 늦게 끝난 색인·추출이 활성 상태를 되살리는지 의심되면 job payload의 판본·metadataVersion과 현재 문헌 포인터를 비교합니다.

## 6. 개인 위키가 저장되지 않을 때

원래 답변이 completed인지, 사용자와 대화의 autoWiki 설정이 현재 켜져 있는지, 메시지가 제외되지 않았는지 확인합니다. 삭제/되돌리기/대화 제외는 정책 버전이 바뀌어도 존중합니다. 사용자가 편집한 페이지의 예상 판본과 다르면 자동 덮어쓰지 않습니다.

개인 위키 Job의 failed/superseded/cancelled와 reason을 확인합니다. 실제 JSON/참조 검증 실패는 실패로 남으며 화면에 가짜 페이지를 만들지 않습니다. fixture 기본 답변이 JSON 정리 형식이 아니면 정리 실패가 정상입니다. 테스트에서는 별도 구조화 fake로 저장 동작을 검증했습니다.

## 7. 회귀 검증

백엔드 테스트는 별도 PostgreSQL schema에서 실행합니다. `schema_translate_map` 없는 search_path 설정만으로는 public의 동명 테이블을 잘못 사용할 수 있어 금지합니다. 테스트 실행에 `--tb=short`를 쓰고 Settings 비밀값은 repr에서 제외합니다.

`test_documents_indexing.py`, `test_personal_wiki.py`, `test_answers.py`, `test_rag_contract.py`, `test_providers.py`, `test_public_fetch.py`와 후속 계약 테스트가 핵심 회귀 위치입니다. 실패 지점과 관련된 검증부터 실행하고, 통합 계약 변경 후 전체 suite와 FE build를 확인합니다.
