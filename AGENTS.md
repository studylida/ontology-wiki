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
