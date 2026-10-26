# API와 스트림 계약

실행 중인 서버의 `/docs`, `/openapi.json`이 DTO 필드·제약의 기계 판독 명세입니다. 아래는 구현 의도를 포함한 사용 지침입니다. API prefix는 `/api/v1`, JSON 키는 camelCase, 날짜는 UTC ISO 8601, ID는 opaque string입니다.

2026-10-26 최종 실행에서 추출한 [OpenAPI 스냅샷](api/openapi.json)을 함께 제공합니다. 계약을 변경하면 서버 스키마와 이 스냅샷을 함께 갱신하세요.

## 인증과 외부 프로젝트

`POST /auth/login {username,password}`는 `{accessToken,user}`를 반환합니다. `GET /auth/me`로 현재 계정을 확인합니다. 이후 `Authorization: Bearer ...`를 사용합니다. 토큰에 쓰인 권한만 믿지 않고 현재 DB 계정의 활성 상태·tokenVersion·권한을 확인합니다.

다른 프로젝트는 CLI로 만든 `kind=service` 계정을 사용합니다. 명시적인 `ontology:read`, `rag:retrieve`, `rag:answer`만 부여할 수 있으며, 필요한 것만 선택합니다. 서비스 계정은 개인 위키 권한을 얻지 않습니다. 개념 API만 사용하는 프로젝트는 검색/생성을 호출할 필요가 없고, 원문 문맥이나 답변까지 필요하면 같은 RAG/Answer Service를 사용하는 API를 호출합니다. 온톨로지 API가 RAG를 대체하거나 RAG 데이터를 버리는 구조가 아닙니다.

```bash
.venv/bin/python scripts/v2/dev.py create-user \
  --username project-reader --service \
  --permission ontology:read --permission rag:retrieve
```

위 명령은 비밀번호를 대화형으로 받고 기존 계정을 덮어쓰지 않습니다. 연결용 비밀값은 다른 프로젝트의 서버에만 보관합니다.

## 대화와 답변

| 메서드·경로 | 동작 |
| --- | --- |
| GET /conversations | 소유한 대화 목록 |
| POST /conversations | 새 대화. 새 설정은 wiki/false |
| GET /conversations/{id} | 메시지·판본에 연결된 출처·마지막 제출 설정 복원 |
| PATCH /conversations/{id} | 제목/autoWiki 설정, 대화 제외 기록 연결 |
| POST /conversations/{id}/turns | 대화에 새 질문/실행 생성 |
| POST /answer-runs | 같은 실행 생성 Service. conversationId 없으면 대화 생성 |
| GET /answer-runs/{id} | 저장된 부분/최종 메시지, lastSeq, status, usage, metrics |
| GET /answer-runs/{id}/events?after=N | N 이후 이벤트 재생과 live SSE. 모델 재호출 없음 |
| POST /answer-runs/{id}/cancel | 명시적 취소. 부분 본문 보존 |
| POST /answer-runs/{id}/client-metrics | 새 실행의 브라우저 최초 표시 관측값 1회 기록 |

다음 JSON은 요청 형식 예입니다. ID는 실제 검색/첨부 응답에서 얻은 값으로 넣습니다.

```json
{
  "clientRequestId": "client-generated-uuid",
  "conversationId": null,
  "message": "보유 자료에서 HBM 접합 방식의 조건과 한계를 비교해 주세요.",
  "responseMode": "wiki",
  "extended": false,
  "conceptIds": [],
  "sourceRevisionIds": [],
  "sourceGroups": [],
  "aspect": null,
  "attachmentIds": [],
  "documentContextIds": []
}
```

`clientRequestId`는 소유자 범위에서 멱등성을 보장합니다. 같은 ID/같은 요청은 기존 실행을 반환하며 내용이 바뀌면 충돌입니다. 명시적인 재시도는 새 clientRequestId와 `retryOfRunId`를 사용하고 실패/부분 답변을 덮어쓰지 않습니다. 동시에 같은 대화의 새 실행을 겹치게 하지 않습니다.

`responseMode`는 wiki/analysis 형식만 선택합니다. Extended와 자료 범위, 서버 모델/effort, 권한을 바꾸지 않습니다. 실제 제출 설정은 run에 고정합니다.

`GET /answer-runs/{id}`의 `retrievalSummary`는 저장된 검색 snapshot, 그룹별 확보 범위, 탐색 계획·실행 기록·종료 사유를 복원합니다. 이 GET은 검색을 다시 수행하지 않습니다. 브라우저 계측 요청은 `{firstVisibleTextMs}`이며 소유자만 최초 한 번 기록할 수 있습니다. 서버는 `clientFirstVisibleTextMs`와 `browser_untrusted`를 저장하여 서버 관측 시간과 구분합니다.

### 자료 범위의 세 가지 입력

- `sourceRevisionIds`: 승인·활성 공용 검색 집합을 좁히는 필터입니다. 미승인 문헌을 공용 검색에 포함시키지 않습니다.
- `documentContextIds`: 사용자가 명시적으로 읽고 질문하는 원문입니다. 소유자 또는 검토자 권한을 검사합니다. 검토 화면의 미승인 문헌 질문도 여기를 사용합니다.
- `attachmentIds`: 원래 대화에 소유자가 가져온 외부 문헌/첨부입니다. 소유자와 대화 ID를 함께 검사합니다.

`sourceGroups`의 각 항목은 `{groupId,publisherId?,sourceType?}`입니다. 그룹 안은 AND, 그룹 간은 각각 후보를 확보한 뒤 결합합니다. 이 필터는 직접 선택 문헌에도 적용됩니다. `groupCoverage`의 missing은 해당 범위에서 근거를 확보하지 못했다는 뜻이며 관계/사실이 존재하지 않는다는 판정이 아닙니다.

### SSE는 무엇을 전달하는가

본문 텍스트와 카드 데이터를 서로 다른 종류의 이벤트로 보냅니다. 클라이언트는 `type`을 읽고 본문에 붙일지, 출처 목록에 추가할지 결정합니다. 예를 들어 다음은 **형식 예**이며 실제로 확인한 반도체 지식을 뜻하지 않습니다.

```text
id: 7
event: text.delta
data: {"type":"text.delta","runId":"run_example","seq":7,"at":"2026-10-26T00:00:00Z","data":{"text":"## 핵심 설명\n"}}

id: 8
event: citation.add
data: {"type":"citation.add","runId":"run_example","seq":8,"at":"2026-10-26T00:00:00Z","data":{"id":"passage_example","sourceRevisionId":"revision_example","passageId":"passage_example","title":"테스트 문헌","locator":"원리","excerpt":"실제 전달할 구간 텍스트"}}
```

실제로 서버는 OpenAI Responses의 `response.output_text.delta`를 받는 즉시 같은 텍스트 경계로 전달합니다. 출처/관계/관점은 검색한 실제 객체와 검증 가능한 참조로 구성합니다. 완성된 본문을 나눠 보이는 지연 애니메이션은 없습니다.

| 이벤트 | data의 의미 |
| --- | --- |
| run.started | messageId, conversationId, responseMode, extended, generationConfig |
| retrieval.status | 실제 stage, retrievalRunId, snapshot, coverage, warnings, 종료 사유 |
| text.delta | `{text}` 실제 공급자 본문 조각 |
| citation.add | 원문 판본·구간·위치·excerpt·메타데이터 |
| relation.add | 개념 쌍·관계 타입/방향·조건·evidence |
| source_view.add | 개념/원문·publisher/author/attributedTo·aspect·conditions·evidence |
| run.completed | 저장 commit 이후에만 공개하는 성공 terminal, usage·metrics 포함 |
| run.failed | 실제 실패 사유와 저장한 부분 본문/usage |
| run.cancelled | 취소 terminal. 미확인 사용량/비용은 null |

모든 이벤트는 runId, 단조 증가 seq, 시각을 가집니다. 클라이언트는 seq 중복을 버립니다. 서버는 실제 delta 경계를 JSONB 배치로 보존하므로 토큰별 row/commit은 없습니다. 브라우저를 새로 열어도 기존 본문을 다시 생성하지 않습니다.

## 검색과 온톨로지

`POST /retrieval/search`는 생성 없이 공통 검색을 사용합니다. 질문과 위의 자료 필드를 받으며 다음을 반환합니다.

```text
retrievalRunId, indexSnapshotId, hits[], relatedConcepts[], relations[], sourceViews[],
appliedFilters, groupCoverage[], warnings[], usage, timings, stopReason, queries[]
```

hit에는 실제 passageId/sourceRevisionId/locator/text/score와 확보 범위가 있습니다. 점수는 검색 순위 신호이며 사실 정확도 확률이 아닙니다.

| GET | 용도 |
| --- | --- |
| /ontology/concepts?q=&cursor=&limit= | 근거가 현재 공개 가능한 개념 찾기 |
| /ontology/concepts/{id} | 안정적 ID, 이름/별칭/타입/판본/근거 |
| /ontology/concepts/{id}/relations | is_a, part_of, precedes, alternative_to와 조건·근거 |
| /ontology/concepts/{id}/source-views | publisherId/sourceType/aspect/dateFrom/dateTo/cursor/limit 조회 |

GET·카드 펼침은 모델을 호출하지 않습니다. 출처가 철회됐거나 귀속 정보가 달라진 파생 설명은 현행 결과에서 제외합니다. 기존 ID/원문/추출 이력은 DB에 남습니다. 원문 근거가 사라진 개념을 이름만으로 공개하지 않습니다.

## 문헌·검토·작업

| 메서드·경로 | 동작 |
| --- | --- |
| GET /documents?reviewStatus= | 현재 권한의 자료 목록. 승인/색인 상태 분리 |
| POST /documents | text/markdown 원문과 서지·귀속 등록. 기본 private |
| POST /documents/{id}/revisions | 정정 본문을 불변 새 판본으로 생성 |
| GET /documents/revisions/{id} | 실제 판본, 추출 구간, 확보 범위, 검토 이력 |
| PATCH /documents/revisions/{id}/metadata | 귀속 정정, 기존 source view 무효화, 후속 재추출 |
| POST /documents/revisions/{id}/review | approve/reject/hold/withdraw와 사유 |
| POST /documents/revisions/{id}/attach | 소유한 대화에 명시적으로 첨부 |
| POST /index-jobs | 선택한 최신 승인 판본의 즉시 색인 |
| GET /jobs?kind= | 소유한 작업과 권한 있는 공용 작업만 조회 |
| POST /jobs/{id}/cancel | 진행/대기 작업의 명시적 취소 |
| POST /jobs/{id}/retry | 실패/취소 작업의 명시적 재시도 |

원문과 벡터 자체를 편집하는 위키 목차 UI는 없습니다. 리뷰어 역할과 시스템 관리자 역할을 구분합니다. `documents:review`가 문헌 검토를, `jobs:manage`가 공용 색인 작업을 허용합니다.

## 외부 조사와 개인 위키

외부 조사 API는 `POST /research/search`, `/fetch`, `/transfer`입니다. 첫 버전의 명시적 검색 공급자는 Crossref입니다. 메타데이터/초록/확보한 본문을 구분하며, 자료를 읽지 못했으면 relevance=null입니다. URL은 매 redirect에서 공개 HTTPS 주소인지 검사하고 제한된 파서로 읽습니다. 검색 결과 전체를 자동 수집하지 않습니다.

개인 위키는 다음 API로 다룹니다.

```text
GET   /personal-wiki?q=
GET   /personal-wiki/settings
PATCH /personal-wiki/settings
POST  /personal-wiki/organize
GET   /personal-wiki/{id}
PATCH /personal-wiki/{id}
DELETE /personal-wiki/{id}
POST  /personal-wiki/{id}/undo
```

정리 요청은 `{messageId,explicit}`입니다. 사용자 수정/되돌리기에는 `expectedVersion`이 필요합니다. 삭제 응답의 새 version을 이용해 삭제를 되돌릴 수 있습니다. 상세 규칙은 [personal-wiki.md](personal-wiki.md)에 있습니다. 정리 실패와 원래 답변의 완료 상태는 독립적입니다.

## 오류와 과거 답변

오류 본문은 `{error:{code,message,details?,retryable}}`입니다. 401은 인증, 403/404는 권한·가시성, 409는 상태/판본 충돌, 422는 입력 계약, 502는 공급자/본문 확보 오류, 503은 미설정 공급자 등을 나타냅니다. 요청 본문·비밀번호·공급자 키를 validation 오류에 그대로 돌려주지 않습니다.

과거 답변은 자동 재작성하지 않습니다. 현재 원문 권한이 철회되면 파생 본문·카드와 재생을 차단합니다. 귀속 메타데이터만 정정되면 과거 답변임을 경고하고 오래된 source view 카드는 현행 카드로 내보내지 않습니다. DB의 원래 답변·추출 기록은 보존합니다.
