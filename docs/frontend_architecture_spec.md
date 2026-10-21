# 🏛️ 반도체 온톨로지 프론트엔드 계층형 아키텍처 상세 설계서
## (Frontend Layered Architecture Spec: View ➔ Controller ➔ Service ➔ Repository ➔ DTO)

> **문서 상태**: Active & Mandatory (프론트엔드 단일 진실 원천)  
> **대상 도메인**: [Tab 1 위키 본문], [Tab 2 기술 대안 비교], [Tab 3 검토·승인 센터], [Tab 4 외부 문헌 조사], [F-01 플로팅 챗봇]  
> **핵심 미션**:  
> 1. 기존 318KB 모놀리스 단일 파일(`js/app.js`)의 영구 폐기 및 단일 책임 모듈화.  
> 2. 백엔드 5계층 아키텍처와 1:1 대칭을 이루는 정통 **Outside-In (View ➔ Controller ➔ Service ➔ Repository ➔ DTO)** 단방향 아키텍처 정립.  
> 3. YAGNI(You Aren't Gonna Need It) 원칙 준수: 불필요한 거대 프레임워크 도입 없이 브라우저 네이티브 ES Modules(`import/export`) 기반 경량·고신뢰성 아키텍처 구현.

---

# 1. 프론트엔드 코어 엔지니어링 철학

## 1.1 Outside-In (탑다운 / 사용자 경험 중심 설계)
- 모든 화면과 기능 설계는 반드시 **"사용자가 화면에서 무엇을 보고(View), 어떤 액션(Action)을 취하는가?"**에서 시작한다.
- UI 상태(UI State)와 사용자 액션 ➔ 이를 관리할 컨트롤러(Controller) ➔ UI 비의존적 도메인 계산(Service) ➔ 백엔드 통신(Repository) ➔ 데이터 스키마(DTO)의 하향식 순서로 설계 및 구현을 전개한다.

## 1.2 단방향 데이터 흐름 (Unidirectional Data Flow)
데이터와 제어 흐름은 결코 역류하거나 계층을 건너뛰지 않는다:
```
┌─────────────────────────────────────────────────────────────┐
│ 1. Views / Dumb Components (js/views/)                      │
│    - 책임: 순수 DOM 렌더링 및 UI 이벤트 리스너 바인딩      │
│    - 규칙: 비즈니스 계산 및 fetch 호출 절대 금지            │
└──────────────────────────────┬──────────────────────────────┘
                               │ 사용자 이벤트 (Click, Input, Select...)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Controllers / Stores (js/controllers/)                   │
│    - 책임: 화면별(Tab 1~4, F-01) 반응형 상태(State) 캡슐화    │
│    - 규칙: 비즈니스 계산은 Service에, API 통신은 Repo에 위임│
└──────────────────────────────┬──────────────────────────────┘
                               │ 순수 비즈니스 연산 요청
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Services / Domain Logic (js/services/)                   │
│    - 책임: UI 비의존적 순수 알고리즘 및 도메인 불변 규칙 검증│
│    - 규칙: DOM 조작 및 직접적인 fetch 호출 일절 배제        │
└──────────────────────────────┬──────────────────────────────┘
                               │ DTO 데이터 요청
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Repositories / API Clients (js/repositories/)            │
│    - 책임: 백엔드 REST API / SSE 스트림과 1:1 통신 (순수 I/O)│
│    - 규칙: 헤더(X-User-Role) 주입, HTTP 상태 코드 매핑       │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP JSON / SSE Data
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. DTOs / Schemas (js/types/)                               │
│    - 책임: 백엔드 Pydantic DTO와 1:1 매핑되는 Contract 스키마│
│    - 규칙: camelCase 필드 명세 및 기본값 정의               │
└─────────────────────────────────────────────────────────────┘
```

## 1.3 YAGNI & 브라우저 표준 지향
- 불필요한 번들러(Webpack/Vite) 복잡도와 서드파티 런타임 의존성을 배제하고, 브라우저 표준 **ES Modules (`<script type="module">`)**를 활용한다.
- 각 계층은 순수 ES6 모듈 파일로 격리되며, 파일 단위의 명확한 책임을 갖는다.

---

# 2. 계층별 표준 규약 및 디렉터리 구조

```
js/
├── main.js                  # 단일 진입점: 라우터 초기화, 탭 스위처 바인딩, 전역 이벤트 등록
├── types/                   # 5. DTO 및 계약 스키마 (API Contract)
│   ├── concept.dto.js       # Tab 1: 개념, 서브그래프, 문맥해설 DTO
│   ├── comparison.dto.js    # Tab 2: 질문 구체화, 매트릭스, 가설 DTO
│   ├── review.dto.js        # Tab 3: 검토 티켓, 락, 감사로그 DTO
│   ├── research.dto.js      # Tab 4: 조사 세션, 문헌 피드, 지식 후보 DTO
│   └── chatbot.dto.js       # F-01: 챗봇 컨텍스트, 메시지, 액션카드 DTO
├── repositories/            # 4. 백엔드 통신 API 클라이언트 (순수 I/O)
│   ├── http_client.js       # 공통 Fetch 래퍼 (Base URL, X-User-Role 헤더, 에러 핸들링)
│   ├── concept_repo.js      # Tab 1 백엔드 API 클라이언트
│   ├── comparison_repo.js   # Tab 2 백엔드 API 클라이언트
│   ├── review_repo.js       # Tab 3 백엔드 API 클라이언트
│   ├── research_repo.js     # Tab 4 백엔드 API 클라이언트
│   └── chatbot_repo.js      # F-01 백엔드 REST/SSE API 클라이언트
├── services/                # 3. 순수 도메인 비즈니스 로직
│   ├── citation_service.js  # [E-01] 각주 파싱, 누락 감지 및 자동 복원 엔진
│   ├── diff_service.js      # <mark class="diff-added"> 마크업 합성 엔진
│   ├── validation_service.js# 물리 안전 마진(140N 등) 수치 가드레일 판별 엔진
│   └── format_service.js    # 날짜, 스케일 뱃지, 단위 포맷팅 순수 함수
├── controllers/             # 2. 탭별 반응형 상태 소유 및 지휘자
│   ├── wiki_controller.js       # Tab 1: 위키 브라우저 화면 제어
│   ├── comparison_controller.js # Tab 2: 인과 탐구실 화면 제어
│   ├── review_controller.js     # Tab 3: 검토 승인 센터 화면 제어
│   ├── research_controller.js   # Tab 4: 외부 문헌 조사실 화면 제어
│   └── chatbot_controller.js    # F-01: 플로팅 챗봇 위젯 제어
└── views/                   # 1. 순수 렌더러 (Dumb UI Components)
    ├── wiki_view.js         # Tab 1 본문/서브그래프 DOM 렌더링
    ├── comparison_view.js   # Tab 2 비교 매트릭스 DOM 렌더링
    ├── review_view.js       # Tab 3 티켓 목록/2-Segment/감사로그 DOM 렌더링
    ├── research_view.js     # Tab 4 문헌 피드/종합 리포트 DOM 렌더링
    └── chatbot_view.js      # F-01 챗봇 말풍선/칩/스트리밍 DOM 렌더링
```

---

## 2.3 도메인 공통 서비스 후보군 조사 목록 (JIT 구현 레지스트리: Just-In-Time Registry)

> **🚨 JIT(Just-In-Time) 원칙**:  
> 아래 목록의 공통 서비스들은 사전 과도구현(Premature Implementation)으로 인해 프론트엔드 UI를 오히려 서비스에 억지로 끼워 맞추는 왜곡을 방지하기 위해 **지금 미리 코드를 작성하지 않는다.**  
> 각 탭(Tab 1~4, F-01)의 View와 Controller를 개발하면서 **해당 비즈니스 요구사항에 실제로 부딪히는 순간에 맞추어(Just-In-Time) 구현**한다.

| 번호 | 서비스명 (`js/services/`) | 책임 및 역할 | 주 사용 도메인 | 구현 시점 (Trigger) |
| :---: | :--- | :--- | :--- | :--- |
| **S-01** | `citation_service.js` | 공인 출처 `[E-01]` 각주 파싱, 본문 내 툴팁 배지 렌더링, 편집 중 누락 시 원문 인용구 자동 복원 | Tab 1, 2, 3, 4, F-01 | Tab 1 본문 렌더링 또는 Tab 3 편집기 저장 개발 시 |
| **S-02** | `diff_service.js` | 지식 개정 전/후 문장 diff 비교 및 `<mark class="diff-added">`, `<del>` 마크업 합성 | Tab 1, 2, 3 | Tab 3 지시문 머지 또는 Tab 1 위키 미리보기 개발 시 |
| **S-03** | `safety_service.js` | 인가 본딩 압력(140N 이하 등) 물리 안전 마진 이탈 검사 및 `overrideReason` 가드레일 판별 | Tab 2, Tab 3 | Tab 2 꼬리질문 상담 또는 Tab 3 지시문 입력 개발 시 |
| **S-04** | `formula_service.js` | 본문 내 LaTeX 수식 텍스트(`formula`)를 브라우저 KaTeX 수식 블록으로 안전 변환 | Tab 1, Tab 2 | Tab 1 2번 섹션 '작동 원리 수식' 렌더링 개발 시 |
| **S-05** | `masking_service.js` | 엔지니어 보안 등급(`line_engineer`)에 따라 L3 극비 파라미터를 `*** (권한 제한)`으로 마스킹 | Tab 1, Tab 3 | Tab 1 스펙 테이블 렌더링 및 RBAC 전환 개발 시 |
| **S-06** | `term_linker.js` | 본문 텍스트 내 온톨로지 개념 명칭/동의어를 자동 인식하여 하이라이트 링크 및 팝오버 바인딩 | Tab 1, F-01 | Tab 1 위키 본문 1~4섹션 리치 텍스트 렌더링 개발 시 |
| **S-07** | `toast_service.js` | transitions.dev 패턴 기반 성공/경고/에러 토스트 알림 큐 스케줄링 및 DOM 바인딩 | 전 탭 공통 | Tab 3 승인/반려 의결 알림 개발 시 |
| **S-08** | `modal_service.js` | transitions.dev 패턴 기반 사유 입력 모달, 위키 미리보기 팝업 라이프사이클 제어 | Tab 2, Tab 3 | Tab 3 위키 미리보기 모달 개발 시 |
| **S-09** | `format_service.js` | ISO 타임스탬프 현지화(YYYY.MM.DD HH:mm), 스케일 뱃지 색상, 단위(N, μm, W) 포맷팅 | 전 탭 공통 | Tab 1 헤더 및 Tab 3 티켓 목록 렌더링 개발 시 |
| **S-10** | `stream_service.js` | SSE(Server-Sent Events) 스트림 청크 수신 및 실시간 마크다운 누적 결합 | F-01 챗봇 | F-01 스트리밍 대화창 렌더링 개발 시 |

---

# 3. 도메인별 Outside-In 5단계 상세 설계 명세

---

## 3.1 [Tab 1] 위키 본문 브라우저 (Wiki Knowledge Browser)

### [화면 재설계 핵심 원칙 (Domain Redesign Alignment)]
1. **비인가 지식 열람 권한 4단계 라이프사이클 화면 표출**:
   - 엔지니어의 L3 극비 파라미터 열람 권한 상태를 4단계로 본문에 실시간 피드백:
     - ① **미신청**: `🔒 L3 극비 파라미터 [열람 권한 신청 ➔]` (클릭 시 사유 입력 모달)
     - ② **심사 대기 (`pending`)**: `⏳ 열람 심사 대기 중 (신청일: 10/21) [신청 취소]`
     - ③ **승인 완료 (`approved`)**: 마스킹 즉시 해제 및 `🔓 인가된 지식 (열람 만료: ~2026.11.20)` 녹색 뱃지 노출
     - ④ **반려됨 (`rejected`)**: `❌ 열람 반려됨 [사유 확인]` (클릭 시 관리자 코멘트 팝업 표출 및 `[재신청]` 버튼 지원)
2. **위키 본문 '새 개정안 발의하기' & '새 문서 추가 발의하기' 듀얼 진입로 (전역 모달 팝업)**:
   - **① 기존 문서 개정 발의**: 위키 헤더에 **`[✍️ 이 문서 개정 발의하기]`** 상시 배치 ➔ 간이 수정 모달(`ReviewTicketCreate`) 제출 ➔ Tab 3 대기열 등록.
   - **② 완전 신규 문서/개념 추가 발의**:
     - **화면 진입 위치**: 좌측 탐색기 검색창 하단 **`[+ 새 문서 추가 발의하기 ➔]`** 및 중앙 본문 헤더 우측 **`[+ 새 문서 발의]`**.
     - **클릭 시 동작**: 화면 전환 없이 부드럽게 열리는 **[신규 온톨로지 개념 발의 전역 팝업 모달]** (`transitions.dev: modal-backdrop & modal-box`).
     - **온톨로지 트리 편입 위치 지정 입력 항목**:
       - 신규 기술/개념명 (`title`, `engName`)
       - 핵심 기술 정의 및 도입 목적 (`summary`, `purpose`)
       - **🌟 `[🤖 AI 에이전트 위치 추천 받기]` 원클릭 버튼**:
         - 엔지니어가 개념명과 개요를 입력한 후 클릭 시, 에이전트가 온톨로지 그래프를 스캔하여 최적의 패싯/스케일/상위개념을 추론하고 아래 드롭다운들을 **자동 채우기(Auto-fill)** 지원 (인지 부하 및 분류 실수 방지).
       - 소속 패싯 (`domainFacet`: `device` | `unit_process` | `fab` | `infra`)
       - 공정 스케일 (`scaleLevel`: `1` 원자/물성 ~ `5` 첨단 패키징)
       - 세부 공정군 (`processCategory`: 예: 첨단 패키징, 극저온 식각)
       - 상위 연계 개념 (`parentConceptId` / `relations.is_a`)
       - 발의 근거 및 공인 출처 링크 (DOI, 백서)
     - **제출 시 연동**: 백엔드 `POST /api/v1/review-tickets` (`isNewConcept: true`)로 직행하여 Tab 3 대기열에 신규 편입 티켓으로 등록.

### [1단계: View - 화면 및 사용자 액션]
- **사용자 시각 영역**:
  - 좌측: 4대 패싯(Device, Process, Fab, Infra) 및 Scale 레벨 트리 탐색기, **검색창 하단 `[+ 새 문서 추가 발의하기 ➔]` 버튼**
  - 중앙 상단: 개념 헤더 (명칭, 스케일 뱃지, 세맨틱 버전 v1.2.0, 공인 출처 배지, **`[✍️ 이 문서 개정 발의]`**, **`[+ 새 문서 발의]`** 액션 버튼 듀얼 배치)
  - 중앙 본문: 1번 개요 / 2번 물리 원리(KaTeX 수식) / 3번 물리 한계 / 4번 실무 사례 (L3 파라미터 옆 4단계 열람 권한 뱃지)
  - 우측: 2-Hop 인과 서브그래프 시각화 캔버스, Contextual Explainer 플로팅 카드
- **사용자 액션 (Actions)**:
  1. 좌측 트리에서 개념 클릭 (`selectConcept`)
  2. 본문 텍스트 내 온톨로지 키워드 클릭 시 인라인 문맥 해설 호출 (`openExplainer`)
  3. 우측 서브그래프 노드 클릭 시 해당 개념으로 즉시 이동 (`navigateGraphNode`)
  4. L3 마스킹 옆 열람 권한 신청/취소/사유 확인 클릭 (`requestAccess`, `cancelAccess`, `viewRejectReason`)
  5. 상단 '이 문서 개정 발의하기' 클릭 시 간이 모달 오픈 및 제출 (`openProposalModal`, `submitRevisionTicket`)
  6. 좌측 또는 상단 '새 문서 추가 발의하기' 클릭 시 전역 팝업 모달 오픈 (`openNewConceptModal`)
  7. 모달 내 '에이전트 위치 추천 받기' 클릭 시 온톨로지 위치 자동 채우기 (`requestAgentPlacement`)
  8. 온톨로지 위치 지정 확인 및 티켓 제출 (`submitNewConceptTicket`)

### [2단계: Controller - 상태 및 액션 핸들러]
- **`WikiController` 소유 State**:
  - `activeConceptId`: 현재 선택된 개념 ID
  - `conceptDetail`: 개념 전체 상세 데이터
  - `subgraphData`: 2-Hop 인과 그래프 노드 및 엣지
  - `explainerCard`: 현재 활성화된 인라인 문맥 해설
  - `accessRequestStatus`: 현재 사용자의 L3 열람 권한 상태 (`none` | `pending` | `approved` | `rejected`)
  - `currentUserRole`: `line_engineer` 또는 `chief_reviewer`
- **Controller 메서드**:
  - `init()`: 초기 개념(예: `concept-tcb`) 로드 및 View 초기 바인딩
  - `loadConcept(conceptId)`: Repository 호출 ➔ View 렌더링 지시 ➔ 내 열람 신청 상태 조회 연동
  - `loadSubgraph(conceptId, depth)`: Repository 호출 ➔ 서브그래프 뷰 렌더링 지시
  - `showExplainer(conceptId, term, x, y)`: Explainer 서비스/리포지토리 호출 ➔ 플로팅 뷰 렌더링 지시
  - `handleAccessRequest(conceptId, reason)`: AuthRepository 호출 ➔ 신청 상태 `pending` 전환 ➔ 뱃지 갱신
  - `submitRevisionTicket(formData)`: ReviewRepository `POST /api/v1/review-tickets` 호출 ➔ 성공 토스트 및 Tab 3 티켓 링크 안내

### [3단계: Service - 도메인 비즈니스 로직]
- `FormulaRenderService`: LaTeX 텍스트를 파싱하여 KaTeX 수식 블록으로 안전 변환
- `MaskingService`: `line_engineer` 권한일 때 L3 핵심 파라미터를 `*** (권한 제한)`으로 필터링
- `GraphLayoutService`: 서브그래프 2-Hop 인과 관계 노드 좌표 및 엣지 극성(polarity) 스타일 계산

### [4단계: Repository - 순수 HTTP 클라이언트]
- `ConceptRepository`:
  - `getConceptDetail(id)` ➔ `GET /api/v1/concepts/{id}`
  - `getConceptSubgraph(id, depth)` ➔ `GET /api/v1/concepts/{id}/subgraph`
  - `getContextualExplainer(id, targetTerm)` ➔ `GET /api/v1/concepts/{id}/explainer`
  - `searchConcepts(query)` ➔ `GET /api/v1/search/spotlight`

### [5단계: DTO - 데이터 스키마]
- `ConceptDetailDTO`, `ConceptSubgraphDTO`, `ContextualExplainerDTO`

---

## 3.2 [Tab 2] 기술 대안 인과 탐구실 (Comparison Studio)

### [화면 재설계 핵심 원칙 (Domain Redesign Alignment)]
1. **과감히 제거된 불필요 요소 (복잡도 해소 & 인지 과부하 차단)**:
   - ❌ **`⚡ 빠른 추천 탐색`, `빠른 추천 탐색 키워드 칩` 전면 제거**: 화면 시각적 노이즈를 줄이고 엔지니어 본인의 탐구 고민에 온전히 집중하도록 제거.
   - ❌ **`자주 찾는 현업 엔지니어링 비교 템플릿` 전면 제거**: 타 엔지니어의 작업 이력이 노출되는 보안상/심리적 위화감 방지 및 첫 화면 선택지 강요 차단.
   - ❌ **`🔍 인과 체인 딥다이브 (Causal Deep-Dive)` 분산 칩 제거**: 화면 집중도를 흩뜨리는 분산 UI 제거.
   - ❌ **`현재 분석 적용 맥락 파라미터 (원클릭 조합 변경)` 하단 더미 태그 제거**: 화면 맨 밑 구석에 떨어져 있어 역할이 불분명하던 고립 태그 폐기.
2. **인지 부하 저감 2단 검색 가이드 구조 (Tab 2, Tab 4 공통 원칙)**:
   - **검색창 내부 (Placeholder - 회색 글씨 자연어 문장 예시)**:
     - 질문을 어떻게 해야 할지 감을 잡을 수 있도록 실제 문장 형식 제공 (타이핑 시작 시 즉시 사라짐).
     - 예: `"예: HBM3E 16단 적층에서 MR-MUF와 TC-NCF의 열저항 및 휨(Warpage) 특성 비교해줘"`
   - **검색창 바로 밑 (미니멀 단어 키워드 칩)**:
     - 문장이 아닌 간결한 단어 형태로만 한 줄 안내하여 인지 부하 최소화:
     - `💡 추천 키워드: [MR-MUF vs TC-NCF]  [하이브리드 본딩 방열]  [Cryo 극저온 식각]`
3. **분석 적용 맥락 파라미터의 정상화 재배치 (2단계 흡수 통합)**:
   - **화면 2-A (조건 설정 단계)**: Track 2의 [대안 A 자동완성 입력창], [대안 B 자동완성 입력창], [도메인/판본 선택기]로 완벽 흡수.
   - **화면 2-B (결과 리포트 단계)**: 매트릭스 바로 상단에 **[분석 전제 요약 헤더: 📌 MR-MUF vs TC-NCF | 첨단 패키징 (2026.10)  [조건 수정 ↩]]**로 재배치.
4. **⚠️ 온톨로지 지식 갭 (Knowledge Gap) 온디맨드 팝오버 전환**:
   - 매트릭스 하단에 시끄럽고 거대한 주황색 경고 배너를 상시 고정 노출하지 않음.
   - 매트릭스 셀의 `[⚠️ 공인 데이터 미등록 (Gap)]` 뱃지를 클릭했을 때만 해당 위치에 정밀 **팝오버(Popover)** 또는 하단 **슬라이드 디테일 카드**를 부드럽게 노출 (`transitions.dev: popover-reveal`).
   - 팝오버 내부에서 공인 출처 부재 사유 안내 및 **`[ 📑 외부 문헌 조사(Tab 4)에서 백서 발굴하기 ➔ ]`** 원클릭 연계 액션 제공 (키워드 자동 전달 이동).
5. **2-Track 진입 지원**:
   - **Track 1 (탐색형/초보자)**: 자연어 문장 입력 ➔ 에이전트 질문 구체화(Clarify) ➔ 3대 공학 분기 카드 선택 ➔ 비교 분석 실행.
   - **Track 2 (목적형/숙련자)**: 지능형 검색창으로 대상 A(예: MR-MUF), 대상 B(예: TC-NCF) 직접 지정 ➔ 평가 축 선택 ➔ 즉시 비교 분석 실행.

### [1단계: View - 화면 및 사용자 액션]
- **사용자 시각 영역**:
  - [화면 2-A] 상단 좌측/우측: [Track 1 자연어 탐색창 (회색 문장 placeholder + 하단 단어 칩)] vs [Track 2 대상 A/B 지능형 자동완성 검색창] 2-Track 듀얼 입력창
  - [화면 2-A] 상단 하단: Track 1 실행 시 노출되는 3대 공학 분기 카드 (`BranchCard`)
  - [화면 2-B] 상단 요약 바: 분석 전제 요약 헤더 (`MR-MUF vs TC-NCF | 2026.10 [조건 수정 ↩]`)
  - [화면 2-B] 중앙: 4단계 심층 인과 비교 매트릭스 (열·물성, 결함 신뢰성, 팹 양산성 축 및 미등록 셀 클릭형 Gap 뱃지)
  - [화면 2-B] 클릭 팝오버: `[⚠️ 미등록 데이터]` 셀 클릭 시 열리는 지식 갭 팝오버 (Tab 4 연계 버튼 포함)
  - [화면 2-B] 하단: 인과 꼬리질문(Deep-Dive Tail Questions) 튜닝 상담 창구 (물리 안전 마진 실시간 검증)
- **사용자 액션 (Actions)**:
  1. 질문 입력 및 구체화 분기 카드 선택 (`submitQuery`, `selectBranch`)
  2. 대상 A/B 자동완성 검색 및 선택 (`searchConcept`, `selectTargetConcept`)
  3. 비교 분석 실행 버튼 클릭 (`executeComparison`)
  4. 지식 갭 셀 클릭하여 팝오버 확인 및 Tab 4 연계 이동 (`clickGapCell`, `navigateToResearchWithGap`)
  5. 비교 축 동적 추가 및 필터링 (`toggleAxis`, `addCustomAxis`)
  6. 꼬리질문 파라미터 튜닝 상담 메시지 전송 (`sendTailQuestion`)
  7. 티켓 내보내기 버튼 클릭 (`exportToReviewTicket`)

### [2단계: Controller - 상태 및 액션 핸들러]
- **`ComparisonController` 소유 State**:
  - `currentSessionId`: 비교 분석 세션 ID
  - `selectedTargetA / selectedTargetB`: 비교 대상 개념 쌍
  - `branchCards`: 질문 구체화 결과 도출된 3대 공학 분기 카드 목록
  - `matrixData`: 다차원 축 비교 결과 및 Gap 판정
  - `tailChatHistory`: 꼬리질문 인과 상담 대화 이력
  - `isGenerating`: LLM 추론 로딩 인디케이터
- **Controller 메서드**:
  - `clarifyQuery(rawQuery)`: Clarify API 호출 ➔ 3대 공학 분기 카드 뷰 렌더링
  - `searchConceptAutocomplete(query, targetRole)`: 전역 검색 API 호출 ➔ 대안 후보 팝오버 렌더링
  - `startComparison(targetA, targetB, axes)`: 매트릭스 API 호출 ➔ 비교 테이블 뷰 렌더링
  - `addCustomAxis(axisName, category)`: 단일 축 즉석 추가 API 호출 ➔ 델타 행 추가 렌더링
  - `chatTailQuestion(question, overrideReason)`: 튜닝 상담 API 호출 ➔ 가드레일 판별 ➔ 대화창 갱신
  - `exportTicket(userNote)`: 검토 센터 정규 티켓 생성 연계 ➔ 완료 알림 및 Tab 3 이동

### [3단계: Service - 도메인 비즈니스 로직]
- `PhysicalSafetyGuardService`: 꼬리질문 상담 중 안전 마진(140N 이하) 위반 시 사유(`overrideReason`) 요구 가드레일 경고 생성
- `MatrixHighlightService`: Target A vs Target B의 물리적 물성 우위/열위 셀 색상 인덱싱 및 지식 갭(Knowledge Gap) 경고 배지 파싱

### [4단계: Repository - 순수 HTTP 클라이언트]
- `ComparisonRepository`:
  - `clarifyComparison(rawQuery, customAxes)` ➔ `POST /api/v1/comparison/clarify`
  - `createSession(payload)` ➔ `POST /api/v1/comparison-sessions`
  - `getSession(sessionId)` ➔ `GET /api/v1/comparison-sessions/{id}`
  - `getMatrix(sessionId, payload)` ➔ `POST /api/v1/comparison-sessions/{id}/matrix`
  - `addCustomAxis(sessionId, payload)` ➔ `POST /api/v1/comparison-sessions/{id}/axes`
  - `tuneAdvisor(sessionId, payload)` ➔ `POST /api/v1/comparison-sessions/{id}/tune-advisor`
  - `exportReport(sessionId, format)` ➔ `GET /api/v1/comparison-sessions/{id}/export`

### [5단계: DTO - 데이터 스키마]
- `ComparisonClarifyDTO`, `ComparisonSessionDTO`, `MatrixRowDTO`, `TuningAdvisorDTO`, `ComparisonExportDTO`

---

## 3.3 [Tab 3] 검토·승인 거버넌스 센터 (Review & Governance Center)

### [화면 재설계 핵심 원칙 (Domain Redesign Alignment)]
1. **과감히 제거된 불필요 요소**:
   - ❌ **빠른 요청 칩(Quick Prompt Chips) 4종 전면 제거**: 정형화된 버튼 클릭 몇 번으로 때울 수 없는 고도의 맥락적 검토 작업이므로, 시각적 노이즈를 없애고 자연어 지시문과 직접 편집에만 온전히 집중하도록 정돈.
2. **단일 작업 초안 (working_draft) 일원화**:
   - AI 합성 초안과 검토관 수정을 분리하지 않고 단일 작업 초안으로 관리하여 동시성 충돌 및 누락 방지.
3. **10분 편집 점유 락(Presence Lock) 상한 만료 & [편집 세션 인계받기] 협업 가드레일**:
   - **백엔드 원천 통제**: 백엔드가 10분(600초) 절대 점유 상한선 초과 시 `max_hold_exceeded`로 락을 강제 회수하고 다른 검토관의 세션 인계를 허용함 (`action: "steal"`).
   - **프론트엔드 실시간 UX 보호**:
     1) **상단 카운트다운 타이머**: 락 획득 시 `⏳ 남은 편집 시간: MM:SS` 실시간 노출.
     2) **사전 경고 (9분 경과 / 1분 전)**: `ToastService.warning("1분 후 편집 세션이 자동 만료됩니다. 작업 내용을 저장하세요.")` 1회 알림.
     3) **10분 도달 시 즉시 아웃**: 편집기 입력창들을 즉시 비활성화(`isEditorDisabled = true`, Read-only 잠금)하고 *"10분 독점 방지 정책에 의해 편집 권한이 반환되었습니다"* 모달 표출.
     4) **타인 만료 시 [⚡ 편집 세션 인계받기]**: 앞선 검토관의 10분이 만료되었을 때, 다른 검토관 화면에 **`[⚡ 편집 세션 인계받기]`** (Takeover Editing Session) 버튼이 활성화되어 안전하게 이어서 검토 진행.
4. **최종 승인 시 [세맨틱 버전(vMAJOR.MINOR.PATCH) 승계 모달]**:
   - 승인 클릭 시 바로 처리하지 않고, 변경 영향도에 따라 자동 계산된 세맨틱 버전을 안내하는 확인 모달 표출:
     - 📌 **PATCH 승계 (예: v1.2.0 ➔ v1.2.1)**: 일상적인 수치/파라미터 및 문맥 보완 시.
     - 📌 **MINOR 승계 (예: v1.2.0 ➔ v1.3.0)**: 신규 개념 등록(`new_concept`) 또는 공인 출처 공식 폐기(`deprecatedCitations`) 시.
     - 최종 승인 사유 입력 ➔ WORM 불변 머클 해시 감사 로그(`audit_logs`)에 영구 기록.
5. **다중 진입로: [+ 새 문서 추가 발의] 전역 팝업 모달 연계**:
   - 검토 센터(Tab 3) 상단 헤더 우측에도 **`[+ 새 문서 추가 발의]`** 상시 버튼을 배치하여, 검토관이 티켓 큐를 보다가도 즉시 전역 팝업 모달을 띄워 온톨로지 신규 개념 편입을 발의 가능.

### [1단계: View - 화면 및 사용자 액션]
- **사용자 시각 영역**:
  - 좌측: 거버넌스 티켓 목록 (상태별: 대기 중 / 승인 완료 / 반려됨)
  - 중앙 상단: 동시 편집 락(Presence Lock) 상태 배너, **실시간 10분 카운트다운 타이머 (`⏳ 09:59`)**, **`[⚡ 편집 세션 인계받기]`** 버튼 (타인 만료 시), **우측 상단 `[+ 새 문서 추가 발의]` 버튼**
  - 중앙 본문: 2-Segment 개정 초안 뷰 (좌: AI 합성 백서 초안 vs 우: 전문가 직접 편집기 / 10분 만료 시 Read-only 전환)
  - 중앙 하단: 전문가 자연어 보완 지시문 입력 바 및 3대 무결성 지표 대시보드
  - 우측/헤더: '위키 미리보기' 모달 버튼, '최종 승인', '반려' 의결 버튼
- **사용자 액션 (Actions)**:
  1. 티켓 목록에서 항목 클릭 (`selectTicket`)
  2. 동시 편집 락 획득/연장/인계받기 클릭 (`acquireLock`, `renewLock`, `takeoverLock`, `releaseLock`)
  3. 상단 '+ 새 문서 추가 발의' 클릭 시 전역 팝업 모달 오픈 (`openNewConceptModal`)
  4. 보완 지시문 입력 및 엔터 (`submitDirective`)
  5. 우측 직접 편집기 텍스트 수정 및 저장 (`saveHumanEdits`)
  6. '위키 미리보기' 모달 열기 (`openWikiPreview`)
  7. '승인' 버튼 클릭 시 [세맨틱 버전 승계 및 승인 사유 확인 모달] 확인 (`approveTicket`)
  8. '반려' 버튼 클릭 및 반려 사유 입력 (`rejectTicket`)

### [2단계: Controller - 상태 및 액션 핸들러]
- **`ReviewController` 소유 State**:
  - `ticketList`: 현재 상태 필터링된 티켓 배열
  - `currentTicket`: 현재 선택된 티켓 상세 객체
  - `presenceLock`:
    - `isLocked`: boolean
    - `holder`: string | null
    - `acquired`: boolean
    - `maxHoldSeconds`: 600 (10분 절대 상한선)
    - `remainingSeconds`: number (남은 편집 초)
  - `presenceHeartbeatTimerId`: 15초 주기 백엔드 Heartbeat 갱신 타이머 ID
  - `countdownTimerId`: 1초 주기 클라이언트 카운트다운 타이머 ID
  - `isEditorDisabled`: boolean (10분 만료 시 true)
  - `ticketVersion`: 낙관적 락 검증용 판본 번호
- **Controller 메서드**:
  - `loadTicketList(statusFilter)`: 티켓 목록 조회 ➔ 좌측 리스트 렌더링
  - `selectTicket(ticketId)`: 티켓 상세 로드 ➔ 락 획득 시도 ➔ 타이머 초기화 ➔ 2-Segment 뷰 렌더링
  - `startPresenceTimers()`: 1초 카운트다운 및 15초 하트비트 가동 ➔ 1분 전 토스트 경고 ➔ 0초 도달 시 `lockoutEditor()` 실행
  - `lockoutEditor()`: 편집기 `disabled` 처리 ➔ 락 해제 안내 모달 표출 ➔ 티켓 읽기 전용 모드 전환
  - `handlePresenceAction(action)`: `acquire`, `renew`, `steal`, `release` I/O 처리 ➔ 락 배너 갱신
  - `applyDirective(text, overrideReason)`: 지시문 I/O ➔ diff 하이라이트 반영 및 무결성 지표 갱신
  - `saveHumanEdits(content, allowDeletion, reason)`: 인용 복원 서비스 ➔ 서버 저장 ➔ 버전 동기화
  - `showWikiPreview(highlightChanges)`: 미리보기 I/O ➔ 공용 위키 사전 렌더링 모달 팝업
  - `executeApprove(reason, targetVer, allowDeletion)`: 승인 집행 ➔ 락 해제 ➔ 완료 토스트 ➔ 목록 갱신
  - `executeReject(reason)`: 반려 집행 ➔ 락 해제 ➔ 목록 갱신

### [3단계: Service - 도메인 비즈니스 로직]
- `CitationIntegrityService`:
  - `validateAndRestore(original, edited, allowDeletion, reason)`:
    - 엔지니어가 `[E-01]` 각주나 해당 문장을 실수로 지웠을 때 `[공인 출처 인용 근거 보존]: ... [E-01]`으로 안전 자동 복원.
    - 반대로 `allowDeletion: true`이거나 사유에 폐기 의도가 명시된 경우 공식 폐기 인가.
- `PresenceHeartbeatService`:
  - 15초 주기 하트비트 전송, 10분 상한 카운트다운 계산, 9분 경과 시 1분 전 사전 경고 발생 조율.
- `DiffMarkupService`:
  - 신규 반영된 문장을 `<mark class="diff-added">`로 감싸 시각적 변경 추적 제공.
- `SemanticVersionService`:
  - 신규 등록 및 공인 출처 공식 폐기는 `MINOR` 승계, 일반 파라미터 보완은 `PATCH` 승계 계산.

### [4단계: Repository - 순수 HTTP 클라이언트]
- `ReviewRepository`:
  - `getTickets(status, conceptId)` ➔ `GET /api/v1/review-tickets`
  - `getTicketDetail(id)` ➔ `GET /api/v1/review-tickets/{id}`
  - `managePresence(id, action, userId, ttl)` ➔ `POST /api/v1/review-tickets/{id}/presence`
  - `applyDirective(id, payload)` ➔ `POST /api/v1/review-tickets/{id}/directive`
  - `saveHumanEdits(id, payload)` ➔ `PUT /api/v1/review-tickets/{id}/human-edits`
  - `getWikiPreview(id, highlight)` ➔ `GET /api/v1/review-tickets/{id}/wiki-preview`
  - `approveTicket(id, payload, role)` ➔ `POST /api/v1/review-tickets/{id}/approve`
  - `rejectTicket(id, payload, role)` ➔ `POST /api/v1/review-tickets/{id}/reject`
  - `getAuditLogs(id)` ➔ `GET /api/v1/review-tickets/{id}/audit-logs`

### [5단계: DTO - 데이터 스키마]
- `ReviewTicketDTO`, `PresenceLockRequestDTO`, `PresenceLockResponseDTO`, `HumanEditsRequestDTO`, `WikiPreviewResponseDTO`, `AuditLogDTO`

---

## 3.4 [Tab 4] 외부 문헌·백서 조사실 (Deep Research Lab)

### [화면 재설계 핵심 원칙 (Domain Redesign Alignment)]
1. **과감히 제거된 불필요 요소 (화면 세로 공간 확보 & 시각적 노이즈 차단)**:
   - ❌ **신뢰출처풀(Publisher Trust Pool) 거대 배너 전면 제거**: Intel, TSMC, IEEE 등이 나열된 상단 거대 배너를 걷어내어 첫 화면 세로 공간을 대폭 확보.
   - ❌ **발굴 추천 예시 칩 전면 제거**: 고정된 클릭 유도용 칩들을 모두 없애 엔지니어가 본인의 탐구 목적에만 온전히 집중하도록 정돈.
2. **인지 부하 저감 2단 검색 가이드 구조 (Tab 2와 통일)**:
   - **검색창 내부 (Placeholder - 회색 글씨 자연어 문장 예시)**:
     - 예: `"예: 차세대 유리기판 TGV 공정 크랙 억제 메커니즘 및 SEMI 국제 표준 규격 조사"` (타이핑 시 자동 소멸)
   - **검색창 바로 밑 (미니멀 단어 키워드 칩)**:
     - 간결한 단어 형태의 추천 칩 한 줄 제공:
     - `💡 추천 검색어: [유리기판 TGV]  [High-NA EUV]  [GAA 나노시트]`
3. **좌측 사이드바: [날짜별 그룹화 (Date-based Grouping)] 이력 관리**:
   - 외부 조사는 "최신성"과 "언제 조사했는가"가 핵심이므로, 복잡한 트리 대신 📅 **오늘 (Today)**, 📅 **이번 주 (This Week)**, 📅 **이전 조사 (Older)** 순으로 날짜별 그룹 정돈.

### [1단계: View - 화면 및 사용자 액션]
- **사용자 시각 영역**:
  - 좌측: 과거 문헌 조사 세션 이력 사이드바
  - 중앙 상단: 기술 주제 검색창 및 5대 공인 기관(IEEE, SEMI, Intel 등) 타깃 필터 칩
  - 중앙 피드: 발굴된 공인 문헌 실측 피드 카드 목록 (체크박스 선택 UI)
  - 중앙 하단 / 결과 뷰: 교차 분석 종합 브리핑 리포트 및 온톨로지 신규 지식 후보 카드
  - 후보 카드 액션: '검토 센터로 거버넌스 티켓 등록' 버튼
- **사용자 액션 (Actions)**:
  1. 기술 검색어 입력 및 구체화 (`searchTopic`)
  2. 공인 문헌 발굴 실행 (`discoverEvidences`)
  3. 발굴된 문헌 체크박스 선택/해제 (`toggleEvidenceSelect`)
  4. '종합 분석 리포트 생성' 버튼 클릭 (`synthesizeReport`)
  5. 지식 후보 카드에서 '검토 센터 거버넌스 큐로 내보내기' 클릭 (`exportCandidateTicket`)

### [2단계: Controller - 상태 및 액션 핸들러]
- **`ResearchController` 소유 State**:
  - `currentSessionId`: 조사 세션 ID
  - `evidenceFeed`: 발굴된 공인 문헌 목록 및 선택 상태(`selectedEvidenceIds`)
  - `synthesisReport`: 교차 분석 리포트 (합의 사실, 한계 갭)
  - `candidates`: 온톨로지 지식 후보 3종
- **Controller 메서드**:
  - `loadSessionList()`: 과거 세션 목록 조회 ➔ 좌측 사이드바 렌더링
  - `clarifyTopic(topic)`: 주제 구체화 I/O ➔ 타깃 필터 칩 렌더링
  - `discover(topic, institutions)`: 문헌 발굴 I/O ➔ 실측 문헌 피드 카드 렌더링
  - `synthesize(selectedIds)`: 교차 분석 I/O ➔ 종합 브리핑 및 지식 후보 뷰 렌더링
  - `exportCandidate(candId, userNote)`: 티켓 발행 I/O ➔ Tab 3 등록 완료 안내

### [3단계: Service - 도메인 비즈니스 로직]
- `EvidenceRankingService`: 인용 신뢰도 티어(Tier 1 공식 제조사, Tier 2 국제 표준)별 시각 뱃지 부여
- `CandidatePayloadMapper`: 지식 후보 규격 데이터를 Tab 3 ReviewTicket 스키마로 표준 매핑

### [4단계: Repository - 순수 HTTP 클라이언트]
- `ResearchRepository`:
  - `listSessions()` ➔ `GET /api/v1/research/sessions`
  - `clarify(searchTopic)` ➔ `POST /api/v1/research/clarify`
  - `discover(searchTopic, targetInstitutions)` ➔ `POST /api/v1/research/discover`
  - `synthesize(sessionId, selectedEvidenceIds)` ➔ `POST /api/v1/research/sessions/{id}/synthesize`
  - `getSession(sessionId)` ➔ `GET /api/v1/research/sessions/{id}`
  - `exportCandidateTicket(candId, payload)` ➔ `POST /api/v1/research/candidates/{id}/export-ticket`

### [5단계: DTO - 데이터 스키마]
- `ResearchSessionDTO`, `ResearchEvidenceItemDTO`, `SynthesisReportDTO`, `KnowledgeCandidateDTO`

---

## 3.5 [F-01] 플로팅 실시간 챗봇 (Floating Engineering Chatbot)

### [1단계: View - 화면 및 사용자 액션]
- **사용자 시각 영역**:
  - 우측 하단 플로팅 토글 버튼 및 대화 위젯 팝업창
  - 챗봇 헤더: 현재 위키 개념 컨텍스트 뱃지 (예: `📌 열압착 본딩 (Scale 3)`)
  - 메시지 영역: 어시스턴트/엔지니어 말풍선, 3종 퀵 질문 칩, 액션 카드 (바로가기 버튼)
  - 하단 입력부: 자연어 질문 입력창, 전송 버튼, 대화 초기화(리셋) 버튼
- **사용자 액션 (Actions)**:
  1. 챗봇 열기/닫기 토글 (`toggleWidget`)
  2. 퀵 질문 칩 클릭 (`clickQuickChip`)
  3. 자연어 질문 입력 및 전송 (`sendMessage`)
  4. 답변 내 액션 카드 클릭 시 해당 탭/문서로 이동 (`clickActionCard`)
  5. 대화 초기화 클릭 (`resetMessages`)

### [2단계: Controller - 상태 및 액션 핸들러]
- **`ChatbotController` 소유 State**:
  - `isOpen`: 위젯 열림/닫힘 상태
  - `contextConcept`: 현재 위키 브라우저에서 열람 중인 활성 개념
  - `messageHistory`: 대화 메시지 목록
  - `isStreaming`: SSE 스트리밍 수신 중 여부
- **Controller 메서드**:
  - `syncContext(conceptId)`: 열람 중인 위키 개념 변경 시 헤더 및 퀵 질문 칩 실시간 동기화
  - `sendUserMessage(text)`: 사용자 말풍선 추가 ➔ SSE 스트리밍 수신 ➔ 토큰 실시간 렌더링 ➔ 완료 처리
  - `clearChat()`: 대화 초기화 I/O ➔ 환영 메시지 복원

### [3단계: Service - 도메인 비즈니스 로직]
- `MarkdownStreamService`: SSE 실시간 델타(`event: delta`) 텍스트 청크를 안전하게 결합하여 인라인 마크다운 렌더링

### [4단계: Repository - 순수 HTTP/SSE 클라이언트]
- `ChatbotRepository`:
  - `getContext(conceptId)` ➔ `GET /api/v1/chatbot/context`
  - `postMessage(message, conceptId)` ➔ `POST /api/v1/chatbot/messages`
  - `streamMessage(message, conceptId, onChunk, onDone)` ➔ `POST /api/v1/chatbot/messages/stream` (SSE EventSource/Fetch Stream)
  - `resetMessages(conceptId)` ➔ `DELETE /api/v1/chatbot/messages`

### [5단계: DTO - 데이터 스키마]
- `ChatbotContextDTO`, `ChatbotMessageRequestDTO`, `ChatbotMessageResponseDTO`

---

## 3.6 [Home] 서비스 소개 및 온톨로지 안내 대시보드 (Home Landing Dashboard)

### [화면 재설계 핵심 원칙 (Domain Redesign Alignment)]
1. **네비게이션 및 홈 복귀 규칙**:
   - 상단 네비게이션 바에는 별도의 '홈 탭'을 추가하지 않고 기존 4대 탭(`Tab 1~4`)을 단정하게 유지.
   - **좌측 상단 로고(`Semiconductor Causal Wiki`) 클릭 시 홈(`#home`)으로 즉시 복귀**하는 표준 웹 UX 적용.
   - 브라우저 히스토리(뒤로가기/앞으로가기)를 자연스럽게 지원하는 **URL 해시 라우팅** 지원:
     - `#home` (홈 대시보드), `#wiki` (위키 브라우저), `#comparison` (인과 탐구실), `#review` (검토 센터), `#research` (문헌 조사실), `#admin` (관리자 콘솔).

### [1단계: View - 화면 및 사용자 액션]
- **사용자 시각 영역**:
  - 상단 히어로: 반도체 인과 온톨로지 지식 위키의 핵심 미션 및 4-Tier AI 하이브리드 아키텍처 개요
  - 중앙: 4대 핵심 작업 공간(Tab 1 위키, Tab 2 비교분석, Tab 3 거버넌스, Tab 4 문헌조사) 원클릭 퀵스타트 카드
  - 하단: 온톨로지 5대 스케일 계층(L1~L5) 시각 안내 및 실시간 지식 통계 (등록 개념 수, 공인 백서 수, 승인 완료 버전)
- **사용자 액션 (Actions)**:
  1. 각 탭 바로가기 카드 클릭 시 해당 작업 공간으로 즉시 전환 (`navigateToTab`)
  2. 인기 공정 개념(TCB, MR-MUF, Cryo Etch 등) 퀵 링크 클릭 시 Tab 1 상세로 직행 (`openQuickConcept`)
  3. 온톨로지 온보딩 가이드 팝업 열기 (`openOnboardingGuide`)

### [2단계: Controller - 상태 및 액션 핸들러]
- **`HomeController` 소유 State**:
  - `systemMetrics`: 총 개념 수, 공인 출처 수, 승인 대기 티켓 수
  - `featuredConcepts`: 추천 탐색 개념 목록
- **Controller 메서드**:
  - `loadDashboardStats()`: 시스템 헬스 및 통계 로드 ➔ 뷰 렌더링
  - `handleQuickNavigation(target)`: 글로벌 탭 스위처와 연동하여 뷰 전환

---

## 3.7 [Auth & Admin] 자체 인증, 권한 관리 및 관리자 콘솔

### [화면 재설계 핵심 원칙 (Domain Redesign Alignment)]
1. **관리자 콘솔 버튼 양방향 자동 토글 UX**:
   - 일반 사용자 작업 공간(Tab 1~4, 홈) 열람 시: TopBar 우측에 **`[관리자 콘솔 ⚙️]`** 노출 (`level >= 3` 사용자 한정).
   - 관리자 콘솔 화면(`#view-admin`) 진입 시: 해당 버튼이 자동으로 **`[사용자 화면 ➔]`** (또는 `[위키 작업 공간으로 돌아가기 ➔]`)으로 토글되어, 심사 완료 후 언제든 원클릭으로 이전 작업 화면에 복귀.

### [1단계: View - 화면 및 사용자 액션]
- **사용자 시각 영역**:
  - TopBar 우측: [로그인/회원가입] 버튼 또는 로그인된 [엔지니어 프로필(이름/부서/레벨)] + `level >= 3`일 때 [관리자 콘솔 ⚙️ ↔ 사용자 화면 ➔] 양방향 토글 버튼 (현장 엔지니어는 미노출)
  - 인증 모달: 자체 회원가입 폼 (사번, 비밀번호, 이름, 부서) / 로그인 폼
  - [Tab 1 본문]: L3 마스킹(`***`) 옆 [열람 권한 신청] 버튼 클릭 시 나타나는 사유 입력 모달
  - [관리자 콘솔 화면 (`#view-admin`)]:
    - 탭 A: 비인가 지식 열람 신청 심사 큐 (대기/승인/반려/회수 액션 버튼)
    - 탭 B: 사내 엔지니어 계정 및 권한 레벨(`level`) 관리 테이블 (승격/강등, 계정 차단)
- **사용자 액션 (Actions)**:
  1. 회원가입 및 로그인 양식 제출 (`submitRegister`, `submitLogin`)
  2. 비밀번호 변경 모달에서 구/신 비밀번호 제출 (`changePassword`)
  3. L3 비인가 파라미터 열람 신청서 작성 및 제출 (`submitAccessRequest`)
  4. 내 열람 신청 대기 취소 (`cancelMyRequest`)
  5. 관리자의 신청 건 승인/반려/회수 버튼 클릭 (`approveRequest`, `rejectRequest`, `revokeRequest`)
  6. 관리자의 엔지니어 level 변경 및 퇴사자 계정 비활성화 (`updateUserLevel`, `deactivateUser`)

### [2단계: Controller - 상태 및 액션 핸들러]
- **`AuthController` 소유 State**:
  - `currentUser`: 현재 로그인된 사용자 정보 (`UserDTO`)
  - `isAuthenticated`: 로그인 여부 (토큰 유효성)
  - `myAccessRequests`: 내가 신청한 열람 권한 목록
  - `pendingReviewRequests`: 관리자 전용 미결 신청 큐 (`level >= 3`)
  - `allUsers`: 관리자 전용 전체 사용자 목록 (`level >= 4`)
- **Controller 메서드**:
  - `login(username, password)` / `register(data)` / `logout()`
  - `changePassword(oldPw, newPw)`
  - `requestAccess(conceptId, reason)`: 본문에서 신청 제출 ➔ 알림 토스트
  - `approveAccess(requestId, comment)` / `rejectAccess(requestId, comment)` / `revokeAccess(requestId, comment)`
  - `changeUserLevel(userId, level)` / `blockUser(userId)`

### [3단계: Service - 도메인 비즈니스 로직]
- `TokenStorageService`:
  - localStorage에 JWT 토큰 안전 보관 및 만료(`exp`) 사전 체크
- `PermissionGateService`:
  - `canAccessL3(conceptId)`: 현재 사용자가 Level 3 이상이거나 승인된 신청이 있는지 판정하여 본문 마스킹 해제 제어

### [4단계: Repository - 순수 HTTP 클라이언트]
- `AuthRepository`:
  - `register(data)` ➔ `POST /api/v1/auth/register`
  - `login(data)` ➔ `POST /api/v1/auth/login`
  - `refresh()` ➔ `POST /api/v1/auth/refresh`
  - `getMe()` ➔ `GET /api/v1/auth/me`
  - `changePassword(data)` ➔ `POST /api/v1/auth/change-password`
  - `deleteMe()` ➔ `DELETE /api/v1/auth/me`
  - `createAccessRequest(data)` ➔ `POST /api/v1/auth/access-requests`
  - `getMyAccessRequests()` ➔ `GET /api/v1/auth/access-requests/my`
  - `cancelAccessRequest(id)` ➔ `DELETE /api/v1/auth/access-requests/{id}`
  - `getAdminAccessRequests(status)` ➔ `GET /api/v1/auth/access-requests`
  - `approveAccessRequest(id, comment)` ➔ `POST /api/v1/auth/access-requests/{id}/approve`
  - `rejectAccessRequest(id, comment)` ➔ `POST /api/v1/auth/access-requests/{id}/reject`
  - `revokeAccessRequest(id, comment)` ➔ `POST /api/v1/auth/access-requests/{id}/revoke`
  - `listUsers(params)` ➔ `GET /api/v1/auth/users`
  - `updateUserLevel(userId, level)` ➔ `PATCH /api/v1/auth/users/{id}/level`
  - `deactivateUser(userId)` ➔ `DELETE /api/v1/auth/users/{id}`

### [5단계: DTO - 데이터 스키마]
- `UserRegisterDTO`, `UserLoginDTO`, `TokenResponseDTO`, `UserDTO`, `AccessRequestDTO`, `AccessReviewDTO`

---

# 4. 인터랙션 및 애니메이션 디자인 시스템 규약 (transitions.dev 필수 준수)

> **공식 표준**: [transitions.dev](https://transitions.dev/) & [transitions.dev Library](https://transitions.dev/library.html)  
> **스타일시트 단일 진실 원천**: `css/transitions.css`

본 시스템의 모든 UI 인터랙션, 상태 전이, 팝업, 스트리밍 타이핑 애니메이션은 임의의 인라인 CSS나 파편화된 `@keyframes` 작성을 금지하며, **반드시 `transitions.dev` 기반의 10대 공인 인터랙션 패턴을 엄격히 준수**한다.

| 번호 | 패턴명 (Pattern) | transitions.dev 레퍼런스 | 적용 대상 UI 컴포넌트 | CSS 클래스 규약 |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Tabs Sliding** | `tabs-sliding` | 최상단 4대 작업 공간(Tab 1~4) 및 상태 탭 전환 | `.sliding-tabs-container`, `.sliding-tab-item`, `.sliding-tab-indicator` |
| **2** | **Panel Reveal** | `panel-reveal` | 우측 서브그래프 패널 및 전문가 직접 편집기 드로어 | `.panel-reveal-drawer`, `.drawer-backdrop` |
| **3** | **Accordion** | `accordion` | 좌측 온톨로지 패싯 트리 및 공정 단계(Step) 접기 | `.accordion-item`, `.accordion-trigger`, `.accordion-content` |
| **4** | **Toast Open/Close**| `toast-open-close` | 거버넌스 승인/반려 의결 완료, 복원 안내 토스트 | `.toast-notification`, `.toast-progress` |
| **5** | **Tooltip** | `tooltip-open-close` | L3 마스킹 안내, 공인 출처 배지 메타데이터 호버 | `.tooltip-trigger`, `.tooltip-bubble` |
| **6** | **Streaming Text** | `streaming-text` | AI 추론 백서 문장 및 F-01 챗봇 토큰 실시간 렌더링 | `.streaming-text-char`, `.streaming-cursor` |
| **7** | **Success Check** | `success-check` | WORM 감사로그 머클 체인 생성 완료 원형 체크 아이콘 | `.success-check-icon`, `.success-check-circle`, `.success-check-tick` |
| **8** | **Skeleton Loader** | `skeleton-loader-and-reveal`| 백엔드 API 호출 대기 중 카드 및 본문 스켈레톤 | `.skeleton-shimmer`, `.skeleton-card`, `.skeleton-text` |
| **9** | **Matrix Dot Loader**| `matrix-dot-loader` | Tab 2 다차원 비교 매트릭스 계산 대기 인디케이터 | `.reasoning-stream`, `.matrix-dot-loader` |
| **10**| **Modal Open/Close** | `modal-open-close` | 위키 본문 사전 미리보기 팝업, 사유 입력 모달 | `.modal-backdrop`, `.modal-box`, `.modal-enter`, `.modal-exit` |

### 애니메이션 타이밍 및 가속도 표준:
- **물리적 가속도 (Natural Easing)**: 기본 가속도는 `cubic-bezier(0.16, 1, 0.3, 1)` (Spring-like Smooth Deceleration)을 채택하여 전문 산업용 엔지니어링 툴다운 절제된 반응성을 유지한다.
- **지연 시간 제한 (Latency Budget)**: 모든 UI 피드백 애니메이션은 320ms 이내에 완료되어야 하며, 데이터 로딩이 150ms 이상 지속될 때만 `skeleton-shimmer`를 노출한다.
- **신규 패턴 확장 원칙 (Extensibility)**: 기존 10대 패턴 외에 화면별로 새로운 UI 인터랙션(예: 드롭다운 메뉴, 탭 카운터 플립, 펄스 인디케이터, 태그 필터 배지 전이 등)이 필요할 경우, 임의로 CSS keyframe을 작성하지 않고 **[transitions.dev 공식 라이브러리](https://transitions.dev/library.html)에서 적합한 패턴을 검색·채택하여 `css/transitions.css`에 표준 규격으로 누적 등록**한다.

---

# 5. 프론트엔드 리팩토링 및 마이그레이션 실행 로드맵

```
[Phase 1] 계층 기반 구축 (Foundation)
  ├─ 1.1 HTTP 공통 클라이언트 구현 (js/repositories/http_client.js)
  ├─ 1.2 DTO 계약 스키마 모듈 정의 (js/types/*.dto.js)
  ├─ 1.3 도메인 공통 서비스 구축 (js/services/citation_service.js, diff_service.js)
  └─ 1.4 transitions.dev 애니메이션 헬퍼 바인딩 (js/services/animation_service.js)

[Phase 2] 도메인 탭별 순차적 계층 분리 (Domain-by-Domain Migration)
  ├─ 2.1 [Tab 1 위키 브라우저] Controller & View 모듈화 (패싯트리, 서브그래프, transitions.dev 아코디언/드로어)
  ├─ 2.2 [Tab 3 검토 승인 센터] Controller & View 모듈화 (2-Segment, 락, 위키미리보기 모달, 토스트)
  ├─ 2.3 [Tab 2 인과 탐구실] Controller & View 모듈화 (비교 매트릭스, 꼬리질문, 닷로더)
  ├─ 2.4 [Tab 4 외부 문헌 조사실] Controller & View 모듈화 (문헌피드, 종합 리포트, 스켈레톤)
  └─ 2.5 [F-01 플로팅 챗봇] Controller & View 모듈화 (SSE 스트리밍 타이핑 애니메이션)

[Phase 3] 단일 진입점 전환 및 최종 검증 (Final Integration)
  ├─ 3.1 단일 진입점 index.html -> <script type="module" src="js/main.js"> 교체
  ├─ 3.2 기존 레거시 app.js 영구 폐기
  └─ 3.3 브라우저 실시간 라이브 연동 및 3단계 검증 완료
```

---

## 2.3 도메인 공통 서비스 후보군 조사 목록 (JIT 구현 레지스트리: Just-In-Time Registry)

> **🚨 JIT(Just-In-Time) 원칙**:  
> 아래 목록의 공통 서비스들은 사전 과도구현(Premature Implementation)으로 인해 프론트엔드 UI를 오히려 서비스에 억지로 끼워 맞추는 왜곡을 방지하기 위해 **지금 미리 코드를 작성하지 않는다.**  
> 각 탭(Tab 1~4, F-01)의 View와 Controller를 개발하면서 **해당 비즈니스 요구사항에 실제로 부딪히는 순간에 맞추어(Just-In-Time) 구현**한다.

| 번호 | 서비스명 (`js/services/`) | 책임 및 역할 | 주 사용 도메인 | 구현 시점 (Trigger) |
| :---: | :--- | :--- | :--- | :--- |
| **S-01** | `citation_service.js` | 공인 출처 `[E-01]` 각주 파싱, 본문 내 툴팁 배지 렌더링, 편집 중 누락 시 원문 인용구 자동 복원 | Tab 1, 2, 3, 4, F-01 | Tab 1 본문 렌더링 또는 Tab 3 편집기 저장 개발 시 |
| **S-02** | `diff_service.js` | 지식 개정 전/후 문장 diff 비교 및 `<mark class="diff-added">`, `<del>` 마크업 합성 | Tab 1, 2, 3 | Tab 3 지시문 머지 또는 Tab 1 위키 미리보기 개발 시 |
| **S-03** | `safety_service.js` | 인가 본딩 압력(140N 이하 등) 물리 안전 마진 이탈 검사 및 `overrideReason` 가드레일 판별 | Tab 2, Tab 3 | Tab 2 꼬리질문 상담 또는 Tab 3 지시문 입력 개발 시 |
| **S-04** | `formula_service.js` | 본문 내 LaTeX 수식 텍스트(`formula`)를 브라우저 KaTeX 수식 블록으로 안전 변환 | Tab 1, Tab 2 | Tab 1 2번 섹션 '작동 원리 수식' 렌더링 개발 시 |
| **S-05** | `masking_service.js` | 엔지니어 보안 등급(`line_engineer`)에 따라 L3 극비 파라미터를 `*** (권한 제한)`으로 마스킹 | Tab 1, Tab 3 | Tab 1 스펙 테이블 렌더링 및 RBAC 전환 개발 시 |
| **S-06** | `term_linker.js` | 본문 텍스트 내 온톨로지 개념 명칭/동의어를 자동 인식하여 하이라이트 링크 및 팝오버 바인딩 | Tab 1, F-01 | Tab 1 위키 본문 1~4섹션 리치 텍스트 렌더링 개발 시 |
| **S-07** | `toast_service.js` | transitions.dev 패턴 기반 성공/경고/에러 토스트 알림 큐 스케줄링 및 DOM 바인딩 | 전 탭 공통 | Tab 3 승인/반려 의결 알림 개발 시 |
| **S-08** | `modal_service.js` | transitions.dev 패턴 기반 사유 입력 모달, 위키 미리보기 팝업 라이프사이클 제어 | Tab 2, Tab 3 | Tab 3 위키 미리보기 모달 개발 시 |
| **S-09** | `format_service.js` | ISO 타임스탬프 현지화(YYYY.MM.DD HH:mm), 스케일 뱃지 색상, 단위(N, μm, W) 포맷팅 | 전 탭 공통 | Tab 1 헤더 및 Tab 3 티켓 목록 렌더링 개발 시 |
| **S-10** | `stream_service.js` | SSE(Server-Sent Events) 스트림 청크 수신 및 실시간 마크다운 누적 결합 | F-01 챗봇 | F-01 스트리밍 대화창 렌더링 개발 시 |

---

# 6. 작업 완료 기준 (Definition of Done)

1. **단일 파일 배제**: 318KB `app.js`가 완전히 제거되고, 모든 코드가 `views`, `controllers`, `services`, `repositories`, `types` 5개 계층으로 100% 분리되었는가?
2. **단방향 데이터 흐름 보존**: View에서 직접 `fetch()`를 부르거나, Service가 DOM을 직접 건드리는 계층 위반이 단 1건도 없는가?
3. **가드레일 연속성**: 공인 출처 불변성(`[E-01]` 복원), L3 극비 마스킹, 물리 안전 마진 수치 가드레일이 프론트엔드에서도 무결하게 작동하는가?
4. **실시간 라이브 동작 확인**: 실제 백엔드 서버(`http://localhost:8000`)와 연결된 브라우저에서 Tab 1~4 및 F-01 기능이 오차 없이 매끄럽게 동작하는가?
