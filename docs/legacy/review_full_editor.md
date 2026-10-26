# 검토 승인 센터 전체 목차 편집

## 책임과 저장 경로

- Controller는 요청·응답을 전달한다. `review_service`가 작업본·검증·판본·미리보기·승인을 조율하며 `review_repo`와 기존 Source/Concept Repository가 DB를 처리한다.
- 기존 `DirectiveAgent.materialize()`·`process_directive()`·`preview()`는 호환 진입점이며 Service의 단일 구현에 위임한다. Agent는 공개 초안 입력과 등록 자료로 검증된 기여/교체 제안을 만든다.
- `ReviewTicketModel.structured_patches`의 `/workingDraft`에 `schemaVersion=1`, 기준 서명, 최종 canonical state, 연결 출처와 메타데이터를 저장한다. 테이블·컬럼·마이그레이션은 추가하지 않는다.
- `/workingDraft`가 있으면 과거 `/wikiDraft` 기여를 다시 재생하지 않는다. `/wikiDraft`, `/concept`, `/evidenceSources`는 기존 근거·분류·호환 책임을 유지한다.
- 삭제는 현재 작업본의 변경이다. 삭제 이력을 다음 AI 보강의 금지·보류 조건으로 사용하지 않는다. 현재 초안과 등록 자료에 따라 삭제했던 내용도 다시 추가할 수 있다.

## API 계약

`GET /review-tickets/{id}`는 인증된 Level 2 이상에게 작성용 `workingDraft`, `editingMode`, `canUndo`를 제공한다. `workingDraft.content`는 표시용 위키 DTO와 구분하며 narrative·편집 키·필드 권한을 유지한다. 원본 `/workingDraft` 및 undo 스냅샷은 raw patch/history 응답에서 제외한다.

`PUT /review-tickets/{id}/human-edits`는 다음 중 하나를 받는다.

- 구형 `editedContent`: 아직 legacy 모드인 티켓의 개요만 저장한다.
- 새 `changes`와 필수 `ticketVersion`: summary/purpose 및 목차별 upsert/remove/order를 원자적으로 저장한다. 항목 키는 editorId이며 사례의 specifications에도 같은 변경 집합을 사용한다. 미전달 필드는 유지하고, 빈 문자열은 비우며, 삭제는 remove로만 요청한다.

구조화 저장을 시작하면 `editingMode=structured`가 된다. 이후 구형 문자열 저장·구형 directive·미리보기 서명 없는 승인은 409로 차단한다. 구형 요청이 다른 목차를 모른 채 전체 작업본을 승인하지 못하게 한다. 새 저장 응답은 전체 권한 적용 작업본과 최신 티켓 판본을 돌려준다.

`POST /directive`는 새 UI에서 `structuredDraft=true`, 최신 `ticketVersion`을 보낸다. `targetSections` 생략은 전체 목차이며 빈 목록은 오류다. 현재 항목의 교체는 자료 ID·현재 editorId·영역과 동일한 DirectiveContent 계약으로 생성하고 기존 본문·관계·사례 의미 검토를 통과해야 한다. 식별할 수 없는 항목이나 기밀 사례의 모델 교체는 보류한다. 외부 모델에는 기밀 파라미터·설명·출처를 전달하지 않는다. 생성·형식·의미 검토 실패는 원래 작업본을 변경하지 않는다.

`POST /wiki-preview`는 저장된 판본, 선택한 targetVersion/conceptPlacement로 단일 materialize 결과를 표시한다. 응답의 `previewSignature`는 승인 시 같은 조건으로 재검증한다. 새 구조화 승인은 편집 본문을 받지 않는다. 먼저 저장하고 같은 판본·분류·출처·원문 상태의 미리보기를 확인한다.

## 데이터 보존

- 저장·directive·undo는 pending 티켓의 판본을 조건부 UPDATE하고 영향 행 수를 확인한다. 모델 호출 중 DB 쓰기 잠금을 유지하지 않는다.
- 승인은 티켓 판본을 확보한 뒤 ORM 캐시를 만료하고 원본·출처·최종 내용을 다시 읽어 검사한다. 본문·사례·파라미터·관계·출처·감사·티켓 상태는 한 번에 커밋한다.
- 직접 고친 기존 관계의 사유/근거는 해당 JSON 관계가 소유한 엣지와 일치할 때만 갱신한다. 다른 개념의 연결이나 독립 편집이 지지하면 409로 보존한다.
- 사례 ID의 소유 개념을 검사한다. 관리자 재추출의 누락을 삭제로 해석하지 않으며, 검토 초안에서 명시한 삭제만 승인 계획에 반영한다.
- 변경하지 않은 summary/purpose의 bodyFields 근거를 보존한다. 본문이 바뀌었으면 이전 문장의 검증을 승계하지 않는다. 공용 인용문·URL을 덮어쓰지 않으며 새 발췌는 티켓의 새 출처로 추가한다.
- 공인 E-* 인용/연결 폐기는 기존 allowCitationDeletion, deprecatedCitations, overrideReason을 명시해야 한다. UI의 출처 목차에서 요청한다. 원문과 다른 개념의 참조는 삭제하지 않는다.
- 비공개 출처는 내부에서 보존하되 작성·미리보기 응답과 외부 모델에는 노출하지 않는다. L3 미인가 사용자의 숨김 값·사례·출처 수정/삭제/재정렬을 차단한다.
- 새 수동 사례는 '공개 사례 추가'로 작성 의도를 표시한다. 공개 의도는 승인된 기존 티켓 스냅샷에 남기며 실제 사례 내용이 그 스냅샷과 같은 경우에만 재사용한다. 출처 불명 legacy 사례의 마스킹을 낮추지 않는다. 개별 기밀 파라미터는 이 표시와 별개로 계속 보호한다.
- Level 2의 기존 편집 자격과 해당 개념 L3 열람 인가를 함께 검사한다. 기존 기밀 지정/해제는 Level 3 이상만 가능하다. 권한 전환 시 이전 사용자의 폼과 미리보기는 즉시 숨긴다.

## UI

공통 목차 탐색으로 현재 위키와 오른쪽 편집기의 같은 목차를 비교한다. 모든 목차의 변경은 함께 저장한다. 입력마다 서버 미리보기를 호출하지 않으며, 저장본과 입력 중 초안을 분리한다. 실패/충돌은 입력을 보존한다. 같은 티켓 재클릭은 입력을 초기화하지 않는다. 다른 티켓 이동은 native dialog에서 저장/버리기/계속 편집을 선택한다. 탭 전환 중에도 App의 Controller가 작업본을 유지하며 브라우저 이탈에는 미저장 경고를 사용한다.

사례·파라미터는 펼쳐 편집한다. 관계는 등록 개념 선택과 관계 사유/근거 목록으로 작성하고 파생 그래프는 미리보기에서 확인한다. 출처는 등록 자료 연결과 신규 발췌 추가를 지원한다. 원문 파일 편집은 제공하지 않는다. 판본 충돌의 자동 병합은 하지 않는다.

## 격리 검증

제품 서버를 재시작하거나 운영 DB를 연결하지 않고 다음을 실행한다. `.venv`의 설치 의존성을 사용한다.

```powershell
.venv/Scripts/python.exe scripts/verify_review_directive.py
.venv/Scripts/python.exe scripts/verify_review_full_editor.py --artifacts-dir <격리 결과 폴더>
```

전체 편집 검사는 자체 FastAPI 앱·별도 파일 SQLite·독립 캐시를 사용하고 설정된 운영 엔진에 connect 금지 이벤트를 등록한다. 실제 삼성 원문을 읽되 생성/의미 검토 모델 응답은 제어한다. 원문은 쓰지 않는다. 저장·실패 보존·삭제와 후속 보강·현재 항목 교체·전체 undo·권한·비공개 출처·공인 폐기·미리보기/승인 일치·관계·두 세션의 저장/승인을 확인한다.

작업 기록의 브라우저 harness는 실제 View/Controller/Repository와 같은 격리 HTTP 앱을 연결한다. 결과와 화면은 작업 기록에 저장한다. 실제 모델 응답의 품질, 운영 티켓 승인, 기존 실행 서버 반영, 대규모 성능은 이 검사만으로 확인되지 않는다.
