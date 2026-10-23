# AGENTS.md: Semiconductor Causal Ontology Wiki Development Guidelines

> **Status**: Active & Mandatory  
> **Target Audience**: All AI Coding Agents (Antigravity, Codex, Claude Code, Cursor, Copilot) & Human Engineers  
> **Core Mission**: 반도체 공정·소자 인과 온톨로지 지식 위키의 엄격한 계층형 아키텍처(Layered Architecture) 보존, 설계 우선(Architecture-First), YAGNI(You Aren't Gonna Need It) 원칙 준수, 그리고 단일 진실 원천(Single Source of Truth) 유지.

---

## 1. Core Principles (핵심 엔지니어링 철학)

### 1.1 Architecture-First (설계 우선 원칙)
- 코드를 작성하거나 수정하기 전에 **반드시 설계와 계층적 책임을 먼저 정의**한다.
- 임의의 "빠른 패치(Quick-fix)"나 단일 파일에 모든 코드를 때려 박는 모놀리식 누적(`app.js` 비대화)은 엄격히 금지된다.
- 새로운 기능이나 수정 사항은 반드시 정의된 계층(DTO, Repository, Service, Controller, View)의 올바른 위치에 배치한다.

### 1.2 YAGNI & Minimalism (단순성과 목적 부합성)
- **You Aren't Gonna Need It**: 현재 요구사항(Tab 1~4, F-01 챗봇)에 명시되지 않은 미래의 가상 시나리오를 위한 과도한 추상화, 불필요한 서드파티 라이브러리 도입, 무의미한 래퍼 함수 생성을 금지한다.
- 프레임워크나 도구는 가장 단순하고 직관적인 표준(Standard)을 우선한다 (예: 브라우저 네이티브 ES Modules, 표준 Fetch/SSE, FastAPI 표준 의존성 주입).

### 1.3 4-Tier AI Hybrid Gateway 원칙
지식 위키의 모든 AI 추론 및 계산은 다음 4계층 게이트웨이 원칙을 철저히 준수해야 한다:
1. **Tier 1 (Fast Cloud)**: `gpt-4o-mini` / Gemini Flash (초고속 문맥 해설, 단답 챗봇, 출처 폐기 의도 판별)
2. **Tier 2 (Deep Reasoning)**: `gpt-4o` (심층 인과 비교 매트릭스, 전문가 지시문 머지, 종합 리포트)
3. **Tier 3 (Air-Gapped Local)**: 사내 폐쇄망 vLLM/Ollama + DLPTokenizer 가명화 (L3 극비 레시피 사내 처리)
4. **Tier 4 (Deterministic)**: 로컬 SQLite Recursive CTE & 물리 안전 마진 수식 (AI 전면 단절 시 100% 무중단 물리 안전망)

### 1.4 Anti-Pattern: 정적 숫자 한정 및 닫힌 목록화 금지 (Open-Endedness & Principles over Checklists)
AI 에이전트가 흔히 범하는 '가짜 구조화(임의의 숫자 붙이기 및 닫힌 목록화)'를 방지하기 위해 다음 규칙을 엄격히 강제한다:
1. **임의의 정적 숫자 한정 금지 (No Arbitrary Enumeration)**:
   - "10대 패턴", "5대 규칙", "3대 요소" 등 임의로 숫자를 붙여 시스템을 폐쇄형 목록(Closed Set)으로 제한하는 행위를 엄격히 금지한다.
   - 문서나 코드에 제시된 목록은 항상 **'대표적인 예시(Examples)'**일 뿐이며, 요구사항에 따라 얼마든지 유연하게 늘어나거나 줄어들 수 있는 **개방형 세트(Open Set)**로 취급한다.
2. **목록(Checklist) 집착 대신 원칙(Principles) 우선**:
   - "정해진 N개 체크박스를 채웠는가?"에 집착하지 않고, **"이 기술/설계의 본질적 가치(단일 진실 원천, 표준 라이브러리 활용, 책임 분리)를 올바르게 실현했는가?"**를 사고의 기준으로 삼는다.
3. **선제적 배제(Premature Exclusion) 방지**:
   - 예시 목록에 명시되지 않았다는 이유만으로, 실제 구현에 자연스럽게 필요한 기능(예: 추가 UI 인터랙션, 새로운 엣지케이스 가드레일 등)을 "규약 외"로 단정하여 지레 배제하거나 놓치는 행위를 절대 금지한다.
   - 필요한 것이 있다면 라이브러리(transitions.dev 등)나 아키텍처 원칙 안에서 언제든 자유롭게 탐색하고 확장 채택한다.

---

## 2. Backend Architecture Conventions (백엔드 계층 규약)

### 기술 비교와 문헌 조사 왕복의 책임
- 조사실 분석·후보 생성은 `RESEARCH_MODEL=gpt-6.1-sol`, `RESEARCH_REASONING_EFFORT=medium`을 기존 Gateway에 명시하고 실패 시 확보 자료만 표시한다. 관리자 원문 추출과 타 탭 모델은 유지한다. 가짜 문헌을 생성하는 이전 DeepResearchAgent는 사용·보존하지 않는다.
- 조사실 신규 개념은 기존 검토 티켓의 `/concept` 패치와 승인 경로를 사용한다. 미확정 분류는 티켓에서 보존하고 기존 승인 모달에서 검토관이 확정한다. 승인 전에는 위키 개념을 만들지 않는다.
- `comparison` Controller는 기존 API 계약을 유지하고 `comparison_service`가 목적·조건·대화·출처를 조율한다. `comparison_repo`와 기존 `concept_repo`가 저장과 조회를 맡는다. 비교는 공개 위키와 공개 출처만 사용하며 위키 원본을 변경하지 않는다.
- `research_service`는 `research_repo`의 등록 원문·Crossref 검색 결과를 조율한다. 서지정보·초록·발췌를 구분하고 조회 실패나 빈 결과를 자료로 채우지 않는다. 비교 연결 맥락은 기존 조사 세션 `synthesis_report.comparisonContext`에 보관해 복원한다.
- 프론트 `useComparisonController`와 `useResearchController`가 탭 이동 중 상태를 유지한다. `comparisonService`는 세션 표시와 조사 맥락 변환을, Repository는 HTTP를 맡는다. 새 비교를 만들지 않고 선택한 조사 자료를 원래 세션에 보강한다. 기존 계층 설계는 아래 문서를 따른다.
- 탭2의 기존 Controller → ComparisonService → ClarifierAgent가 질문을 A/B·목적·적용 맥락·축의 초안으로 해석한다. Agent는 위키 미등록 표현도 유지하고 부족한 내용만 확인하며 고정 분기·축을 만들지 않는다. Service는 기존 Repository의 등록 연결과 공개 사양 검증을 맡고, Controller가 초안·원래 질문·사용자 수정·지연 응답을 관리한다. 기존 비교 View의 초안을 직접 지정과 문헌 조사에 사용하며 등록 ID와 초안 대상명을 구분한다. 상세 계약과 격리 검증은 `docs/tab2_purpose_comparison.md`를 따른다.

### 비교 출처 승인 통합의 책임
- 비교 Service는 확보 출처를 기존 티켓의 `/evidenceSources` 목록 패치로 보관한다. `/concept`·`/wikiDraft` 패치와 검토 지시문을 유지한다. 새 출처 서비스나 Repository는 추가하지 않는다.
- 기존 `DirectiveAgent.materialize()`가 최종 본문에 남은 출처를 미리보기·승인에 함께 전달하고 `review_repo.save_content()`가 출처 충돌 검사·중복 없는 연결을 승인 트랜잭션에서 저장한다. 인용 삭제한 후보는 연결하지 않는다.
- Controller는 화면을 바꾼 뒤 도착한 응답·오류를 버린다. 공인 학술 신뢰 등급과 비공개 처리 등급을 구분하며 수치의 부호를 원문과 대조한다.

### 신규 개념 편입 위치 추천의 책임
- 두 추천 API는 `placement_service`에 위임한다. Service가 기존 `concept_repo`·`llm_gateway`를 사용해 현재 위키의 패싯·물리적 규모·세부 공정군을 추천하고 DTO로 검증한다. 키워드 대체 추천은 임시임을 표시하며 분류할 수 없는 입력에 기본 분류나 임의 상위 개념을 넣지 않는다.
- `useWikiController`가 추천 요청·실패·종료를 관리한다. `NewConceptModal`은 응답의 `domainFacet`, `scaleLevel`, `processCategory`를 입력란에 반영하고 기존 패싯·규모 표시 함수를 사용한다. 발의는 기존 검토 티켓 경로를 유지한다.

### 등록 지식 검색의 책임
- 기존 `useTopBarController`가 검색어·추천·검색 결과·지연 응답·실패를 관리하고 `conceptRepo.search()`로 기존 Spotlight API를 사용한다. `SpotlightModal`은 등록 응답만 표시하며 고정 샘플 ID를 만들지 않는다.

### 위키 텍스트 선택의 책임
- 상세 DTO의 `selectionTerms`는 기존 Repository 조회의 공개 등록명·별칭만 담는다. View가 클릭·더블클릭의 실제 선택 범위를 보정하고 드래그는 보존한다. 순수 `textSelectionService`는 문자 범위만 계산하며 Controller가 선택 문자열을 그대로 기존 설명 API에 전달하고 중복·지연 응답을 관리한다. 설명 대상 해석과 L3 마스킹은 변경하지 않는다.

### 선택 표현 해설의 책임
- 공개 사례·L3 마스킹 투영은 Concept Service의 공통 메서드를 재사용하며 팝오버가 상세 화면의 관계·규모·선택 목록 조립을 실행하지 않는다. 승인 시 문맥 없는 팝오버 사전 생성은 하지 않는다. Service의 해설 실패 원인은 API에서 HTTP 상태로 변환하고 Controller가 상태별 안내를 표시한다.
- View는 실제 Selection과 주변 문맥만 전달하고 Controller가 문맥별 요청 재사용·지연 응답을 관리한다. Concept Service는 기존 공개·L3 마스킹 결과로 문맥을 확인하고 실제 등록 정의·공개 관계·출처만 전달하며 공개 입력 서명으로 캐시한다. ExplainerAgent는 뜻·문맥 해설 두 필드를 한 번에 생성·검증하며 실패를 성공 답변으로 대체하지 않는다. 임의 표현은 허용하고 선택 문자열을 정규화하거나 개념 ID로 치환하지 않는다.

### 통합 실행과 첫 위키 진입
- App은 URL에 명시된 개념을 Controller에 전달한다. 지정이 없으면 `useWikiController`가 기존 트리 응답의 첫 등록 개념을 열며, 데모 개념 ID를 기본값으로 사용하지 않는다. 명시적 선택이 시작된 뒤 트리 응답으로 이를 대체하지 않는다.
- 문헌 조사 재개·공개 HTML/PDF 확보는 `docs/research_discovery_design.md`의 기존 Agent·Service·Repository·DTO 계약을 따른다. 로컬 메인 DB 전환·백업·격리 HTTP 및 비용 측정의 범위는 `docs/local_service_verification_20261023.md`에 기록한다.

### 온톨로지 챗의 현재 책임
- Global 출력 지시는 스키마 대신 실제 답변 객체 형식을 전달하며 `GlobalChatAnswer` 검증을 유지한다. 형식 오류·무응답은 본문 없이 유형만 로그에 남기고 기존 오류 응답을 반환한다.
- Controller의 Local/Global 선택은 요청 DTO `knowledgeScope`로 전달한다. Local은 등록 위키 근거만, Global은 반도체 분야 모델 일반 지식만 답하며 웹 검색·위키 출처로 가장하지 않는다. 명시한 다른 질문 대상을 현재 열람 개념으로 대신하지 않고 모드별 실패를 그대로 표시한다.
- 기존 `chatbot` API → `ClarifierAgent.route_chatbot_intent`가 등록 개념을 해석하고, `concept_service.get_enriched_concept_detail`의 공개·L3 마스킹 결과와 기존 Repository의 연결 출처를 사용한다. 기술명·고정 수치·인과 노드를 대체 데이터로 만들지 않는다.
- 화면 이동은 명시적인 화면 열기 요청에만 카드로 제공한다. 일반 설명·비교·표준 질문은 챗에서 답하고, 비교 대상이 불명확하면 확인한다. Controller는 서버 출처·후속 질문 계약을 표시하며 오류를 정상 답변으로 꾸미지 않는다.

### 검토 지시문과 승인 초안의 책임
- `review_service`가 기존 티켓 JSON의 `/workingDraft`로 전체 구조화 작업본의 저장·판본·되돌리기·미리보기·승인을 조율한다. 기존 `materialize()`는 이 Service의 한 구현만 사용하며 Agent의 호환 메서드도 위임한다. `review_repo`는 조건부 판본 갱신과 승인 트랜잭션의 본문·사례·관계·출처 저장을 담당한다. 승인 전 공용 위키를 바꾸지 않는다.
- `DirectiveAgent`는 현재 작업본의 공개 내용과 등록 발췌로 자료별 기여·대상 항목 교체를 생성하고 같은 DTO로 검증한다. 본문과 관계·사례의 의미 검토 및 `source_service`를 재사용한다. 인용 문자열·줄 번호·동일 줄 명칭으로 후보를 배제하지 않으며 실패 시 작업본을 보존한다. 삭제 이력 기반 AI 차단은 사용하지 않는다.
- Controller는 저장본/편집본을 분리하고 모든 목차의 직접 추가·수정·삭제·순서를 하나의 판본으로 저장한다. 목차별 왼쪽 기준본과 오른쪽 입력 폼을 표시하며 미리보기는 기존 위키 렌더러를 사용한다. 구조화 승인은 확인한 미리보기 판본·서명·분류가 일치해야 한다. 상세·이력 응답에 원본 작업본/undo 스냅샷을 노출하지 않고 L3 필드와 비공개 출처를 보호한다.
- 기존 분류와 비교 출처 패치를 보존한다. 새 수동 공개 사례의 공개 의도는 승인 티켓 스냅샷으로 보존하며 출처 불명 legacy 사례의 마스킹을 낮추지 않는다. 상세 계약과 격리 검증은 `docs/review_full_editor.md`를 따른다. 새 화면·테이블·마이그레이션은 추가하지 않는다.

### 사례 맥락 해설의 책임
- 수치 없는 사례도 승인된 공개 의도 또는 내용이 보존된 원문 적용 이력과 공개 근거로 해설할 수 있다. `source_repo.public_case_ids()`의 같은 판정을 상세·해설 Service에서 사용하며 비공개 사양·출처 불명 legacy·후속 비공개 승인은 계속 보호한다.
- `case_explanation_service`가 공개 입력·서명·최신성·생성을 조율하고 기존 `concept_repo`가 사례 JSON의 조건부 저장을 맡는다. 기존 `ExplainerAgent`의 사례 메서드는 공개 입력만 해설하며 원문·근거 필드를 덮지 않는다. 적용·승인 커밋 후 독립 세션의 BackgroundTasks에서 생성하고 GET은 저장된 최신 결과만 읽는다. 실패·누락은 원문 저장·표시를 막지 않는다.
- `useWikiController`가 생성·재시도와 제한적인 GET 재확인을 맡고 `SectionPerspectives`가 원문 표 아래 `CaseContextExplanation`을 기본 표시한다. 미리보기는 응답 복사본만 장식하며 원문 이력·비교 서명에는 해설을 넣지 않는다. 설계와 명시적 마이그레이션·운영 미적용 범위는 `docs/perspective_context_explanation_design.md`, 용어는 `GLOSSARY.md`를 따른다.

### 관계와 규모별 연결의 책임
- 두 관계 View는 블록 설명을 그대로 표시하고 등록 대상 블록·제목의 클릭을 기존 Controller의 문서 선택에 전달한다. 미등록 대상은 명시적 발의 버튼만 사용하며, 콜백이 없는 승인 미리보기는 설명만 표시한다. 중복 설명 팝오버·DB·추출·관계 데이터 변경은 없다.
- 대상 규모는 개념 자체의 정의를 기준으로 검토한다. 회로·칩·패키지 구조와 제조 공정·장비를 구분하고 문헌별 기존 제안은 보존하며 명시적 시드 확정값만 수정한다. 규모 안내는 실제 길이 범위를 보장하지 않는다. 용어는 `GLOSSARY.md`를 따른다.
- 원리 View는 독립된 원리 제목·본문·수식을 표시한다. 여러 문헌의 로컬 step 값을 공통 공정 순서로 표시하거나 원문 번호를 새로 꾸미지 않는다.
- 문헌별 관계 보강은 기존 시드 JSON과 관계 재검토 기록에 근거·유형·방향·보류 판단을 남긴다. 지식 관계 View는 실제 관계를 먼저 표시하고 존재하지 않는 공정 순서 패널을 생략한다.
- Repository는 등록 관계의 상·하위 종류와 소속·구성 요소를 양방향으로 조회한다. Concept Service는 실제 관계의 두 단계 이웃을 규모별로 구성하고 기존 SubgraphEdge DTO에 종류·방향·사유를 보존한다. View는 모든 관계와 연결 단계를 표시하며 분류·공정·대안을 물리 포함 계층으로 바꾸지 않는다.

### 문헌 오프라인 시드의 책임
- `backend/seeds/offline_sources_20261023/README.md`와 문헌별 JSON은 전체 읽기·원문 해시·검토 판단을 보관한다. API 응답 이력으로 가장하지 않는다. `scripts/import_offline_seed.py`는 외부 모델 호출을 막은 별도 CLI에서 기존 DTO → 원문 Service 미리보기·적용 → Repository 저장과 사례 해설 Service를 사용한다. 기존 DB 파일은 거부하며 원문·운영 설정을 바꾸지 않는다.
- `scripts/verify_offline_seed.py`는 읽기 전용 격리 DB에서 전체 개념·문헌 GET과 지식 서명·원문 해시·무결성을 확인한다. 시드 내용과 저장된 해설을 구분하고 기존 공개 판정·적용 트랜잭션을 유지한다. 부분 빌드는 완료 결과로 취급하지 않는다.

### 관리자 원문 추출 기능의 현재 책임
- 원문 줄 번호·인용문 문자열 일치·같은 줄의 명칭 유무로 추출 내용을 배제하지 않는다. 인용과 위치는 가능한 경우 메타데이터로 보관하며 Service의 기존 의미 검토로 관계의 주체·유형과 사례·수치의 귀속·조건을 판단한다. 형식·ID·분류 충돌·전체 후보 판정·적용 트랜잭션 검사는 유지한다.
- 원문 추출·분류·파라미터 보강·관계 및 사례 귀속 검토는 추출 전용 `SOURCE_EXTRACTION_PROVIDER=gemini`, `SOURCE_EXTRACTION_MODEL=gemini-3.8-flash`, `SOURCE_EXTRACTION_REASONING_EFFORT=medium`을 기존 Gateway에 전달한다. 다른 기능의 Tier 1/2 설정은 유지하며, 추출은 실패 시 경량 모델로 조용히 대체하지 않는다.
- 추출 프롬프트는 발행사별 사실·수치를 강제하지 않고 공통 위키 계약을 따른다. Service의 같은 정제 원문을 추출·미리보기·적용 근거 검증에 사용한다. 신규 관계는 종류·소속까지, 신규 사례는 회사·제품·상황과 수치 귀속을 검토한 뒤 저장한다. 예시는 기본 비활성이며 격리 비교에서 효과를 확인한 뒤에만 확대한다. 플레이북은 `docs/data_extraction_playbook.md`를 따른다.
- 긴 문서는 Service가 모든 원문 구간을 처리한 뒤 미리보기를 저장한다. 처리 범위·항목별 인용·적용 불가 사유를 DTO로 전달하며 일부 구간 실패를 문서 성공으로 기록하지 않는다.
- 미리보기와 적용은 같은 보존·보강 규칙을 사용한다. 추출된 내용으로 빈칸을 채우며 기존 본문은 보존한다. 사례 재추출은 마지막 적용 내용을 원문 이력 JSON에 보관해 전문가 수정과 구분하고, 순번 변경으로 사례를 덮어쓰지 않는다.
- 추출 DTO의 분야·분류·규모는 프롬프트→미리보기→적용으로 전달하며 단위 공정·Scale 3으로 강제하지 않는다. 분류 미확정은 검토 화면에서 드러내고 적용 시 검증한다. 개념별 설명·관계 사유·사다리를 합성하지 않는다.
- `concept_repo`는 등록 ID·고유한 이름/별칭으로 참조를 해석하고, 적용 트랜잭션에서 기존 미등록 참조까지 `causal_edges`에 반영한다. 관계 유형과 원문 근거를 보존하고 전후 관계는 양방향 조회한다. 프론트는 서버의 `isRegistered`를 따른다.
- 프론트엔드는 `App`의 `useAdminController`가 SSE 실행과 진행·결과를 소유하며, View의 닫기는 표시만 숨긴다. 전체 선택은 현재 목록의 기추출 문서도 포함하며 실행 중 문서는 제외한다. Controller가 실행 전 재추출 포함 여부를 확인하고 기존 `forceReextract`로 전달한다. Service가 기존 순차 추출을 전용 DB 세션의 독립 Task로 실행하고, SSE는 최신 작업의 이벤트를 구독·재생한다. Controller가 관리자 로그인 후 상태를 조회해 새로고침 뒤에도 진행·결과를 복원한다. 서버 재시작은 자동 실행하지 않으며, 목록 순서가 확인되는 기존 중단은 전체 목록과 보존 범위를 표시한 뒤 명시적으로 이어한다. 새 큐나 DB 테이블은 추가하지 않는다.
- `adminRepo`는 기존 `tokenService`로 인증하고 SSE를 전달한다. `source_service`는 기존 위키 DTO 변환·보존 병합과 적용 트랜잭션을, `source_repo`는 원문 메타데이터·추출 이력을 담당한다. 원문은 수정하지 않는다.
- 사례 파라미터는 기존 `PerspectiveCaseModel.specifications` JSON 계약을 사용한다(설계서의 별도 사양 테이블은 현재 미구현). Service가 각 값·단위·마진과 설명의 원문 근거를 검증하고, 관리자 미리보기와 위키는 같은 `SectionPerspectives`로 표시한다. 없는 값·마진·설명을 합성하지 않으며 공개 파라미터와 기존 L3 마스킹을 구분한다.
- 분류는 명시적 관리자 확정 → 현재 DB → 신규 추출안 순서로 적용하며 원문별 제안·충돌은 별도로 보존한다. 원문별 관계 기여 이력은 기존 추출 이력 JSON에 보관하며, 재추출 누락만으로 정상 관계를 지우지 않는다. 정정은 변경되지 않은 해당 원문의 기여만 대상으로 하고 다른 원문·전문가 수정과 별도 그래프 지식은 보존한다.
- 추출 성공 시 미리보기를 저장하고 관리자 적용 시에만 위키를 변경한다. 묶음 적용 중 Repository는 중간 커밋하지 않으며 Service가 한 번에 확정한다. 자세한 계층 설계는 `docs/layered_architecture_spec.md`, `docs/frontend_architecture_spec.md`를 따른다.

백엔드는 `docs/layered_architecture_spec.md`를 헌법으로 삼으며, 아래 정통 5계층 분리 기준을 엄격히 준수한다.

```
[Client / Frontend]
       │ HTTP / SSE
       ▼
[Router / Controller]  ── FastAPI 엔드포인트, 입력 유효성 검증(Pydantic), HTTP 상태 코드 매핑
       │ DTO
       ▼
[Service Layer]        ── 순수 비즈니스 로직, 4-Tier LLM 추론 조율, 도메인 불변 규칙 검증
       │ Entity
       ▼
[Repository Layer]     ── SQLAlchemy ORM 비동기 쿼리, SQLite Recursive CTE, 순수 DB 입출력
       │ SQL
       ▼
[Database / Entities]  ── 정규화된 RDBMS 물리 테이블 (JSON 컬럼 남용 배제, 3정규형)
```

### 계층별 금지 사항 (Backend Anti-Patterns)
1. **Router에서 DB 직접 조회 금지**: Controller/Router에서 `db.execute(select(...))` 등 ORM 쿼리를 직접 수행하지 않고 Service/Repository를 통해 처리한다.
2. **Entity를 클라이언트에 직접 노출 금지**: ORM Entity(`ConceptModel` 등)를 그대로 반환하지 않고 반드시 직렬화 DTO(`ConceptDetailDTO` 등)로 변환하여 응답한다.
3. **L3 극비 데이터 무단 누출 금지**: 요청자의 권한 레벨이 Level 2 이하이거나 L3 열람 인가를 받지 않은 경우 핵심 파라미터는 Service 계층에서 반드시 마스킹(`***`) 처리되어야 한다.

---

## 3. Frontend Architecture Conventions (프론트엔드 계층 규약)

프론트엔드는 백엔드의 계층 구조와 **1:1 대칭을 이루는 단방향 계층 구조(Layered Architecture)**를 채택한다.  
거대한 단일 파일(`app.js`)을 영구 폐기하고, 브라우저 표준 ES Modules(`import/export`) 기반의 5계층으로 분리한다.

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Views / Components (js/views/)                           │
│    - 순수 DOM 렌더링 및 이벤트 리스너 바인딩만 담당          │
│    - 비즈니스 로직 및 직접적인 fetch 호출 일절 금지         │
└──────────────────────────────┬──────────────────────────────┘
                               │ User Events
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Controllers / Stores (js/controllers/)                   │
│    - 화면별(Tab 1~4, F-01) 반응형 상태(State) 소유          │
│    - 사용자 액션 수신 ➔ Service/Repository 호출 ➔ View 갱신  │
└──────────────────────────────┬──────────────────────────────┘
                               │ State / Actions
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Services / Domain Logic (js/services/)                   │
│    - UI 비의존적 순수 비즈니스 로직                         │
│    - 공인 출처 각주([E-01]) 파싱/복원, diff 하이라이트 생성,  │
│      안전 마진 및 보상 파라미터 유효성 검사                  │
└──────────────────────────────┬──────────────────────────────┘
                               │ DTO Requests
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Repositories / API Clients (js/repositories/)            │
│    - 백엔드 REST API / SSE 스트림과 1:1 통신하는 순수 I/O   │
│    - fetch/EventSource 래핑, JWT Bearer 토큰 주입, 에러 처리 │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP JSON / SSE
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. DTOs / Schemas (js/types/ or js/api/dto/)                │
│    - 백엔드 API 계약(Contract) 스키마 정의                   │
│    - camelCase 표준 필드 명세 및 기본값 정의                 │
└─────────────────────────────────────────────────────────────┘
```

### 3.1 디렉터리 배치 표준
```
js/
├── main.js                  # 단일 진입점 (Router 및 Tab 스위처 초기화)
├── types/                   # 5. DTO 및 상수 정의
│   ├── concept.dto.js
│   ├── comparison.dto.js
│   ├── review.dto.js
│   └── research.dto.js
├── repositories/            # 4. 백엔드 통신 API 클라이언트 (순수 I/O)
│   ├── http_client.js       # 공통 Fetch 래퍼 (Base URL, Auth, Error Handling)
│   ├── concept_repo.js
│   ├── comparison_repo.js
│   ├── review_repo.js
│   ├── research_repo.js
│   └── chatbot_repo.js
├── services/                # 3. 순수 도메인 비즈니스 로직
│   ├── citation_service.js  # 출처 각주 보존 및 자동 복원 로직
│   ├── diff_service.js      # <mark class="diff-added"> 렌더링 로직
│   └── validation_service.js# 물리 안전 마진 수치 가드레일 로직
├── controllers/             # 2. 탭별 화면 상태 관리 및 제어
│   ├── wiki_controller.js       # Tab 1: 지식 브라우저
│   ├── comparison_controller.js # Tab 2: 인과 탐구실
│   ├── review_controller.js     # Tab 3: 검토 승인 센터
│   ├── research_controller.js   # Tab 4: 외부 문헌 조사실
│   └── chatbot_controller.js    # F-01: 실시간 챗봇
└── views/                   # 1. 순수 렌더러 (Dumb UI Components)
    ├── wiki_view.js
    ├── comparison_view.js
    ├── review_view.js
    ├── research_view.js
    └── chatbot_view.js
```

### 3.2 계층별 금지 사항 (Frontend Anti-Patterns)
1. **View에서 API 직접 호출 금지**: UI 렌더러 함수나 이벤트 핸들러 안에서 직접 `fetch()`를 부르는 스파게티 패턴을 절대 금지한다. 반드시 Controller ➔ Repository를 경유한다.
2. **글로벌 전역 변수 남용 금지**: `window.someState = ...` 형태의 전역 오염을 금지하고, 각 탭의 Controller 인스턴스가 상태를 캡슐화하여 관리한다.
3. **단일 거대 파일 복구 금지**: 분할된 모듈을 다시 한 파일로 뭉치는 행위를 엄격히 금지한다.

### 3.3 UI 인터랙션 및 애니메이션 규약 (transitions.dev 라이브러리 표준 준수)
- 모든 화면 전환, 탭 슬라이딩, 모달, 토스트, 드롭다운, 스켈레톤, 스트리밍 텍스트 등 인터랙션/애니메이션은 임의의 파편화된 CSS `@keyframes`를 자체 제작하지 않고, **[transitions.dev 라이브러리](https://transitions.dev/library.html)의 정식 인터랙션 패턴을 자유롭게 가져와 `css/transitions.css`에 표준화하여 확장 사용**한다.
- **초기 대표 도입 패턴 예시 (기본 탑재)**:
  1. `tabs-sliding`: `sliding-tabs-container`, `sliding-tab-indicator` (Tab 1~4 슬라이딩 전환)
  2. `panel-reveal`: `panel-reveal-drawer` (우측 서브그래프/편집 패널)
  3. `accordion`: `accordion-item`, `accordion-trigger` (인과 트리/공정 단계 접기)
  4. `toast-open-close`: `toast-notification` (거버넌스 승인/반려/에러 알림)
  5. `tooltip-open-close`: `tooltip-bubble` (L3 보안 마스킹 및 공인 출처 배지 호버)
  6. `streaming-text`: `streaming-text-char` (AI 추론 및 챗봇 토큰 실시간 타이핑)
  7. `success-check`: `success-check-icon` (WORM 감사로그 승인 완료 체크)
  8. `skeleton-loader-and-reveal`: `skeleton-shimmer` (API 데이터 로딩 인디케이터)
  9. `reasoning-stream & matrix-dot-loader`: (비교 매트릭스 추론 인디케이터)
  10. `modal-open-close`: `modal-backdrop`, `modal-box` (사유 입력 및 위키 미리보기 팝업)
- **자유로운 라이브러리 확장 원칙**: 위 대표 패턴 예시 외에도 개발 중 새로운 UI 인터랙션(드롭다운, 카운터 플립, 펄스 인디케이터, 뱃지 트랜지션 등)이 필요한 경우, 특정 패턴에 얽매이지 않고 **[transitions.dev 전체 라이브러리](https://transitions.dev/library.html)에서 적합한 패턴을 언제든 자유롭게 채택하여 `css/transitions.css`에 누적 등록**한다.

---

## 4. Verification Protocol (3단계 라이브 검증 원칙)

모든 엔드포인트 및 기능 구현/수정 후에는 반드시 다음 3단계를 거쳐 검증해야 한다:

1. **① 존재 이유 설명**:
   - 해당 기능/라우터가 해결하고자 하는 도메인 공학적 문제와 가드레일 역할을 설명.
2. **② 정상 시나리오 (Happy Path)**:
   - 실제 정상 입력에 대한 실시간 응답(200/201 OK) 및 상태 변경을 확인.
3. **③ 엣지 케이스 및 위험 상황 방어 (Edge Case)**:
   - 권한 위반(`403 Forbidden`), 데이터 누락/형식 위반(`400/422`), 동시성 충돌(`409 Conflict`), 미존재 자원(`404 Not Found`)의 철저한 방어를 입증.

> **테스트 파일 생성 금지 규칙**: 별도의 `test_*.py` 임시 파일을 만들지 않고, 가상환경 일회성 인라인 파이썬(`python -c "import httpx; ..."`) 명령으로 실서버(`http://localhost:8000`)를 호출하여 검증한다.

---

## 5. Definition of Done (작업 완료 기준)

1. **아키텍처 부합성**: 신규 작성/수정된 코드가 Backend 및 Frontend의 계층 분리 원칙을 100% 준수하는가?
2. **단방향 데이터 흐름**: View ➔ Controller ➔ Service ➔ Repository 흐름이 깨지지 않았는가?
3. **가드레일 보존**: L3 권한 마스킹, 공인 출처 불변성([E-01] 보존), 물리 안전 마진 수식 가드레일이 손상되지 않았는가?
4. **실시간 라이브 검증 완료**: 실제 동작 서버를 대상으로 3단계 검증이 오차 없이 확인되었는가?

### 문헌 조사 후보 선정

- `ResearchService.gather()`는 기존 점수로 경로별 후보를 정렬하고 출처 ID로 동점을 고정한 뒤 등록 발췌·Crossref·로컬 원문을 한 건씩 교대해 검색당30건을 선정한다. 빈 경로의 자리는 나머지가 사용한다. 선정 후에는 기존 DOI 통합이 등록 ID를 먼저 보도록 등록 발췌를 앞에 배치한다. 조회·원문·판정·세션 누적 계약은 유지한다.
