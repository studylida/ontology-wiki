# 개인 위키: 저장·권한·되돌리기 계약

개인 위키는 완료된 위키/분석 답변을 개인 소유 페이지로 정리한다. 문헌의 공용 검토·승인, 공용 주장 승격, 별도 개인 벡터 색인은 포함하지 않는다. 자동 정리 기본 켜짐은 구현 가정이며 설정 API의 `defaultIsAssumption: true`로 드러낸다.

## 책임과 연결점

- Router는 요청 DTO와 인증을 받아 `PersonalWikiService`에 전달한다. SQL은 Repository에 있다.
- 답변 완료 커밋 후 `enqueue_for_message(session_factory, principal, message_id)`가 durable `personal_wiki` job을 만든다. 답변 스트림은 정리를 기다리지 않는다.
- DB worker는 `process_job(session_factory, generation_client, job_id, settings)`를 실행한다. 반환 `status`는 `succeeded`, `superseded`, `cancelled`이며 `action`은 `add`, `merge`, `correct`, `skipped`다. 예외는 worker가 `failed`로 기록한다.
- 대화 제외는 `ConversationService.patch`의 동일 트랜잭션에서 `exclude_conversation(session, principal, conversation_id)`를 호출한다. 전역 설정을 끄면 진행 중인 자동 작업도 취소한다.
- provider의 `generate_json`을 재사용한다. 실제 모델을 부를 수 없거나 결과가 JSON 계약에 맞지 않으면 정리 실패가 남는다. 일반 fixture 답변을 정상 개인 위키로 가장하지 않는다.

DB 트랜잭션은 입력 확인과 최종 저장에만 짧게 사용한다. 모델 호출 동안 연결/행 잠금을 유지하지 않는다. 최종 저장은 현재 계정·권한, 자동 설정 또는 명시적 정리 의도, 원본 답변 완료, job 상태/attempt, 제외 generation, 원문 권한·내용/메타데이터 서명, 대상 페이지 판본을 다시 확인한다. 원문 확인은 공통 `DocumentRepository.ensure_readable(..., lock=True)`를 사용해 철회와 저장을 직렬화한다.

## 무엇을 저장하는가

`personal_wiki_pages`는 현재 제목·주제·요약·본문·조건·한계·실제 원문 citation·원본 대화/메시지 참조를 갖는다. `personal_wiki_revisions`는 모든 변경의 불변 스냅샷과 이전 유효 판본 연결을 보관한다. `personal_wiki_message_states`는 owner/message별 중복 방지와 제외 기록을 보관하며 페이지 삭제 뒤에도 남는다.

페이지는 사용자별로만 조회하며 서비스 계정은 개인 위키 API를 사용할 수 없다. 관리 역할도 다른 사람의 페이지를 조회하는 우회가 없다. 원문 접근이 철회되면 현재 페이지의 제목·요약·본문·조건·citation·원메시지·판본 목록을 가린다. 검색어로 비공개 본문을 추측할 수 없도록 제한된 페이지는 검색 결과에서 제외한다. 검색어 없는 목록에는 안전한 이름의 제한 항목만 표시한다.

생성에 입력된 모든 원문 ID를 접근 검사에 보존한다. 모델이 citation 목록에서 어떤 ID를 빠뜨려도 그 원문에 기반한 내용을 그대로 노출하지 않는다. AI 페이지 자체는 독립 원문 근거로 집계하지 않는다. 원문이 없는 답변도 개인 메모로 정리할 수 있지만 `evidenceStatus: conversation_only`와 경고를 표시한다.

정확한 구간 ID를 찾지 못해도 읽을 수 있는 실제 문헌을 버리지 않는다. 문헌 단위 근거와 `referenceStatus: document_only`로 전환하고 정밀 위치를 만들어내지 않는다. 이 처리는 의미 정확도 보증과 별개다.

## 추가·병합·정정

한 번의 정리는 해당 사용자의 질문 하나, 완료 답변 하나, 원문 근거, 관련 후보 페이지 최대 네 개를 사용한다. 전체 대화 이력이나 다른 사용자의 자료를 전달하지 않는다. 입력이 지정된 한도를 넘으면 부분 답변을 조용히 정리하지 않고 `organization_context_too_large`로 건너뛴다.

병합/정정은 입력에 포함된 페이지 ID와 예상 판본에만 허용한다. 사용자 수정 페이지는 자동 후보에서 제외하고, 생성 중 직접 수정되어도 저장 직전 충돌로 보호한다. 조건이 다르면 병합하지 않는다. 조건과 주제의 정체성 비교는 대소문자를 보존하므로 `mW`와 `MW`를 합치지 않는다. 동일한 활성 주제·조건으로 새 페이지가 겹치면 덮어쓰지 않고 기존 페이지를 알려 준다.

모델의 구조와 참조 ID는 검증한다. 근거의 의미 적합성이나 조건 해석의 정확도는 별도 평가 과제이며 이 기계적 검증만으로 인증하지 않는다.

## API와 되돌리기

| API | 계약 |
|---|---|
| `GET /api/v1/personal-wiki?q=` | 본인 페이지의 제목·주제·요약·본문·조건 문자열 검색; 모델 호출 없음 |
| `GET /api/v1/personal-wiki/{id}` | 현재 내용, 안전한 판본 메타데이터, `{messageId, conversationId}` 원메시지 참조, 실제 원문 citation |
| `PATCH /api/v1/personal-wiki/{id}` | `{expectedVersion, title?, content?}`; 낡은 판본은 409, 저장 후 사용자 수정 보호 |
| `DELETE /api/v1/personal-wiki/{id}` | 소프트 삭제와 제외 기록; `{id, deleted:true, version:<삭제 후 판본>}` 반환 |
| `POST /api/v1/personal-wiki/{id}/undo` | `{expectedVersion}`; 직전 유효 내용 복원. 삭제 복구에는 DELETE가 반환한 판본 번호 사용 |
| `GET/PATCH /api/v1/personal-wiki/settings` | `{autoOrganize}`; 응답에 `defaultIsAssumption:true` |
| `POST /api/v1/personal-wiki/organize` | `{messageId, explicit:false}`; durable 작업 요청 결과. 저장 성공 알림과 구분 |

첫 AI 생성 자체를 되돌리면 페이지가 사라지므로 undo도 `{id, deleted:true, version}`를 반환할 수 있다. 삭제 복구는 같은 주제·조건의 다른 활성 페이지를 덮어쓰지 않는다. 이전 판본의 원문 권한이 없으면 복구를 거절한다. 과거 본문 전체를 `versions` 목록으로 돌려주는 우회도 없다.

삭제·정리 되돌리기·대화 제외는 해당 메시지의 exclusion generation을 증가시키고 진행 중 작업을 취소한다. 제외된 대화에서 이후 완료된 메시지도 제외 기록을 갖는다. 설정을 다시 켜거나 정책 버전이 달라져도 이 기록을 무시하지 않는다. 사용자 본인이 `explicit:true`로 정리를 다시 요청할 때만 새로운 generation을 허용하며, 과거 제외 사유/시각은 보존한다. 명시적 정리는 자동 설정이 꺼져 있어도 가능하지만 권한·원본 완료·취소·판본 검사를 우회하지 않는다.

## 비용·실패와 디버깅

모델 호출 전에 `Job.usage`에 호출 시도와 미확인 사용량/null 비용을 남긴다. 관측된 usage는 성공, 취소 후 늦은 응답, JSON/DTO 검증 실패에도 보존한다. 정리 job 실패는 원래 완료된 답변의 상태를 바꾸지 않는다. job 결과에는 원문에서 파생한 자유 서술을 넣지 않아 이력 API가 원문 권한을 우회하는 통로가 되지 않게 한다.

일반적인 확인 순서는 원본 Message의 owner/status → User/Conversation 자동 설정 → message-state의 suppression/generation → Job 상태/attempt/usage → 원문 현재 권한/metadata signature → 페이지 expectedVersion이다. `superseded`는 실패를 성공으로 꾸민 것이 아니라 새 상태를 보호하기 위해 결과를 저장하지 않았다는 뜻이며 `action: skipped`와 reason으로 구분한다.

## 검증 범위

`backend/tests/test_personal_wiki.py`는 공유 fixtures가 만든 테스트별 PostgreSQL 임시 schema를 사용한다. JSON generation fake는 명시적으로 주입하며 실제 모델 API를 호출하지 않는다. 원문/개인위키 접근, durable 중복 방지, 삭제·복구·판본 충돌, 대화 제외 후 재활성화, 현재 설정/계정/원문/메타데이터/답변/작업 취소 race, 사용자 편집 보호, 조건 구분, JSON 실패와 usage 보존, HTTP 인증/설정 계약을 확인한다.

이 테스트는 개인 위키 생성의 의미 정확도나 실제 모델 품질을 평가하지 않는다. 제품 UI 흐름과 실제 공급자를 이용한 별도 검증 결과는 전체 프로젝트 실행 기록에 분리한다.
