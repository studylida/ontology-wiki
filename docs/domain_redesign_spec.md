# 🏛️ 반도체 인과 온톨로지 위키 도메인 재설계 통합 마스터 명세서

> **문서 목적**:  
> 위키(Tab 1), 기술 대안 비교분석(Tab 2), 검토·승인 센터(Tab 3), 외부 문헌 조사(Tab 4), 플로팅 챗봇 등  
> 시스템 전체의 화면별 사용자 인터랙션과 User Flow를 바탕으로,  
> **Controller ➔ Service ➔ Repository ➔ Entity** 계층별 책임과 API 인터페이스를  
> 파편화 없이 **단일 문서에서 통합 관리**하기 위한 마스터 기준 문서입니다.

---

# 1. 📖 [Tab 1] 위키 본문 뷰 (Public Wiki) 도메인 설계

## 1.1 위키 페이지 컴포넌트별 5대 핵심 도메인 컨트롤러 & 서비스 정의

### [도메인 1] 카테고리 계층 네비게이션 (`Navigation / Classification`)
- **담당 역할**:
  - 좌측 업무 분야(소자 제품군, 제조 단위 공정, 팹 지능화 & 운영, 소재 화학 & 팹 인프라) 선택 시 하위 카테고리 계층 및 개념 목록 트리 서빙.
  - 프론트엔드가 알 수 없는 온톨로지 지식 계층(스케일 레벨, 단위 공정 분류, 관점 보유 여부)을 구조화하여 제공.
- **컨트롤러**: `CategoryHierarchyController`
  - `GET /api/v1/navigation/tree?facet={domain_facet}`
- **서비스**: `NavigationService.get_hierarchy_tree(facet)`
- **레포지토리**: `NavigationRepository.get_concepts_by_facet(facet)`
- **엔티티**: `ConceptModel` (`domain_facet`, `process_category`, `scale_level`, `title`)

---

### [도메인 2] 위키 엔트리 본문 & 비식별화 (`Wiki Entry & Deidentification`)
- **담당 역할**:
  - 카테고리 내 특정 개념(플라즈마 건식 식각, TCB 등) 선택 시 본문 개요, 물리적 메커니즘, 공정 한계, 다도메인 실무 사례(Perspectives) 제공.
  - **비식별화/마스킹 서비스 연동**: 요청한 사용자의 보안 인가 등급(`X-User-Role`, Clearance Level: L1/L2 vs L3)에 따라 Tier 3 양산 절대 수치(온도, 가압력, 수율 등)를 동적으로 가림 처리.
- **컨트롤러**: `WikiEntryController`
  - `GET /api/v1/wiki-entries/{entry_id}` (헤더: `X-User-Role`)
- **서비스**: 
  - `WikiEntryService.get_entry_detail(entry_id, user_role)`
  - `DeidentificationService.mask_confidential_recipe(perspective_cases, user_level)` (비식별화 전담 엔진)
- **레포지토리**: 
  - `WikiEntryRepository.get_entry_by_id(entry_id)`
  - `PerspectiveRepository.get_perspectives_by_concept(entry_id)`
- **엔티티**: `ConceptModel`, `PerspectiveCaseModel`

---

### [도메인 3] 출처 근거 원문 & 공식 검증 증빙 (`Evidence & Reference Source`)
- **담당 역할**:
  - 본문 내 각주 `[E-01]` 클릭 시 슬라이딩 드로어 표출 또는 하단 "공식 검증 출처 원문" 목록 서빙.
  - 공인 출처 메타데이터(출처명, 학회/제조사, 원문 인용구, 관련 섹션, 원문 URL, 신뢰도 등급 Tier 1/2) 단건 및 목록 조회.
- **컨트롤러**: `EvidenceController`
  - `GET /api/v1/evidences/{evidence_id}` (단건 상세 드로어 조회)
  - `GET /api/v1/evidences?conceptId={concept_id}` (해당 개념과 연관된 전체 공식 출처 목록 조회)
- **서비스**: `EvidenceService.get_evidence_detail(id)` / `get_evidences_by_concept(concept_id)`
- **레포지토리**: `EvidenceRepository.get_by_id(id)` / `get_by_concept_id(concept_id)`
- **엔티티**: `EvidenceSourceModel` (테이블: `evidence_sources`)

---

### [도메인 4] 인라인 용어 팝업 요약 해설 (`Contextual Term Explainer`)
- **담당 역할**:
  - 본문 텍스트 중 형광펜 키워드 호버/클릭 시 0ms로 띄워줄 인라인 요약 정의 및 두 개념 간의 인과 문맥 설명 제공.
- **구현 아키텍처 (최적화)**:
  - **기본 방식 (0ms 사전 적재)**: 도메인 2의 위키 엔트리 상세 응답(`GET /wiki-entries/{id}`) 내에 본문 연관 키워드들의 팝업 요약(`preloadedExplainers`)을 미리 묶어서 내려주어 네트워크 딜레이 없이 즉시 팝업 표출.
  - **폴백 방식 (온디맨드 팝오버 API)**: 챗봇, 비교 스튜디오, 검토 에디터 등 타 화면에서 단독으로 용어 요약만 원하거나, 본문 사전 적재 목록에 없는 낯선 용어 클릭 시 단독 호출.
- **컨트롤러**: `ContextualExplainerController`
  - `GET /api/v1/explainers/contextual?childId={child_id}&parentId={parent_id}`
- **서비스**: `ExplainerService.generate_context_summary(child_id, parent_id)`
- **레포지토리**: `ConceptRepository.get_by_id()`, `CausalGraphRepository.get_edge()`
- **DTO**: `ContextualExplanationDTO`

---

### [도메인 5] 온톨로지 2-Hop 인과 서브그래프 네트워크 (`Causal Subgraph & Compensation`)
- **담당 역할**:
  - 해당 개념을 기점으로 1~2단계 연쇄 원인·결함 노드 및 이를 상쇄하는 **보상 파라미터(Compensating Parameters)** 네트워크 탐색.
  - 단순 텍스트 조회가 아닌, **그래프 토폴로지 탐색 알고리즘(SQLite 재귀 CTE 쿼리)** 전담.
- **컨트롤러**: `CausalGraphController`
  - `GET /api/v1/causal-graphs/{concept_id}/2hop`
- **서비스**: `CausalGraphService.get_2hop_network(concept_id, max_depth=2)`
- **레포지토리**: `CausalGraphRepository.find_recursive_edges(concept_id, max_depth)` (CTE 쿼리 격리)
- **엔티티**: `CausalEdgeModel` (테이블: `causal_edges`, 컬럼: `compensating_params`, `mechanism_label`)
- **DTO**: `CausalSubgraphResponse`, `SubgraphNode`, `SubgraphEdge`, `CompensatingParamSchema`

---

## 1.2 컨트롤러 vs 서비스 역할 분리 기준

| 계층 | 역할 (Role) | 허용되는 작업 | 절대 금지 작업 |
| :--- | :--- | :--- | :--- |
| **Controller** | HTTP 진입점 (Gatekeeper) | URL 파라미터 검증, 권한 헤더(`X-User-Role`) 추출, 서비스 호출, HTTP 상태 코드(200, 404) 반환 | DB 쿼리 실행, SQL 작성, 비즈니스 가공, 마스킹 정규식 실행 |
| **Service** | 비즈니스 로직 (Brain) | 레포지토리 호출, 엔티티 결합, 비식별화/마스킹 정책 적용, 그래프 DTO 가공, 캐시 처리 | HTTP 세션/헤더 직접 접근, Request 객체 파싱 |
| **Repository** | 순수 데이터 접근 (Data Access) | SQLAlchemy `AsyncSession` 기반 쿼리 수행, 엔티티 객체 또는 원시 Row 리스트 반환 | 비즈니스 조건문 분기, 가짜 하드코딩 폴백 반환 |
| **Entity** | 물리 스키마 매핑 (Data Model) | SQLite 물리 테이블 컬럼 및 외래키/관계 정의 | 로직이나 변환 코드 포함 |

---

## 1.3 타 도메인 연계 컴포넌트 명세 (위키 내 중복 신설 방지 및 향후 개편 연동 규격)

위키 화면 내에서 일어나는 인터랙션이지만, **위키 도메인에서 별도로 중복 신설하지 않고, 추후 해당 전문 도메인이 새로 정의·개편되었을 때 그쪽에서 제공하는 정규 인터페이스를 연계하여 사용하기로 확정한 연동 지점**입니다.

### 1.3.1 🔒 L3 절대 수치 열람 권한 신청 (보안·거버넌스 도메인 개편 시 연동)
- **화면 트리거**: 본문 3번 섹션 (L3 실무 사례 카드 내 `[이 관점 상세 절대 수치 열람 권한 신청 ➔]` 버튼)
- **연계 예정 도메인**: 보안 및 인가 거버넌스 도메인 (`Security & Access Governance`)
- **처리 원칙**:
  - 위키 도메인에서 임의로 권한 신청 컨트롤러를 만들지 않습니다.
  - 기존 레거시 코드를 단순 재사용하는 것이 아니며, **향후 보안·거버넌스 도메인을 정식 계층화하여 새로 개편할 때 정의될 권한 신청 API(예: `POST /api/v1/security/access-requests`)를 가져다 쓰는 것**으로 규정합니다.

### 1.3.2 ✍️ 본문 최하단 수정·보완 간이 제안 (검토·승인 센터 도메인 개편 시 연동)
- **화면 트리거**: 본문 최하단 Quiet Feedback 영역 (`내용에 오류나 누락이 있나요? 수정·보완 제안` 버튼 ➔ 모달 `[M-05]`)
- **연계 예정 도메인**: 검토·승인 센터 거버넌스 도메인 (`Review & Governance`)
- **처리 원칙**:
  - 사용자 액션은 위키 화면에서 일어나지만 최종 데이터의 처리 주체는 '검토 센터'입니다.
  - 따라서 위키 도메인에 제안용 엔드포인트를 중복 생성하지 않으며, 기존 레거시를 쓰는 것도 아닙니다.
  - **향후 검토·승인 센터 도메인을 정식으로 새로 개편할 때 정의될 티켓 신규 발행 API(예: `POST /api/v1/review-tickets`)를 프론트엔드가 모달 제출 시 직결 호출하여 연계**하도록 규정합니다.

### 1.3.3 🔗 온톨로지 관계 링크 칩 (`is_a`, `part_of`, `next_step`) (2번 위키 엔트리 DTO 내장)
- **화면 트리거**: 본문 4번 섹션 (스케일 네비게이터 하단 인라인 링크 칩)
- **처리 원칙**:
  - 관계 링크만을 위한 별도 컨트롤러를 신설하지 않습니다.
  - [도메인 2] `WikiEntryController`의 응답 DTO(`WikiEntryDetailResponse`) 내에 `relations: { is_a: [...], part_of: [...], next_step: [...] }` 필드를 온전히 보장하여 단일 번들로 서빙합니다.

---

# 2. ⚖️ [Tab 2] 기술 대안 비교분석 (Perspective Studio) 도메인 설계

## 2.1 [화면 2-A: 조사·분석 요청실] UI/UX 개편 및 듀얼 트랙(Dual Track) 설계

기존 화면의 번잡함을 걷어내고, **엔지니어의 전문성 수준과 질문 명확도에 따라 최적화된 2가지 진입 경로**로 화면을 재설계합니다.

```
                  [사용자 진입: 조사·분석 요청실]
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
[Track 1: 탐색형 (초보자)]                      [Track 2: 목적형 (숙련자)]
"HBM 열 문제 어떻게 하지?"                      "대상 A: MR-MUF, 대상 B: TC-NCF"
        ↓                                               ↓
에이전트 질문 구체화 (Clarify)                  지능형 개념 검색창으로 직접 타깃팅
        ↓                                               ↓
★ 3대 공학 분기 카드 선택                       ★ 평가 축 & 공정 조건 직접 조합
        └───────────────────────┬───────────────────────┘
                                ▼
                [⚡ 비교 분석 실행 (화면 2-B 이동)]
```

### ① 과감히 제거된 불필요 요소 (복잡도 해소 & 보안 강화)
1. **빠른 추천 탐색 키워드 칩 제거**: 화면 시각적 노이즈를 줄이고 본인의 고민에 집중하도록 제거.
2. **자주 찾는 현업 엔지니어링 비교 템플릿 전면 제거**:
   - 타 엔지니어의 작업 이력이 노출되는 보안상/심리적 위화감 방지.
   - 검색 첫 화면에서 불필요하게 많은 선택지를 강요하는 인지 과부하(Cognitive Overload) 차단.

### ② 정적 드롭다운 ➔ 지능형 자동완성 검색창 전환
- 기존의 단순 드롭다운 대신, 대안 A와 대안 B를 사내 온톨로지 DB에서 바로 찾아주는 **지능형 개념 검색창(Auto-complete Input)**을 배치.
- 숙련된 엔지니어는 3대 분기 카드를 거치지 않고도 원하는 대안 두 가지와 평가 조건을 즉시 설정하여 바로 실행 가능.

---

## 2.2 도메인 컨트롤러 & 서비스 계층 정의

에이전트를 호출하더라도 **기대하는 입력과 출력(DTO), 그리고 화면 맥락이 완전히 다르므로 컨트롤러 단에서 목적별로 명확히 분리**합니다.

### [도메인 1] 세션 및 연구 자산 관리 (`ComparisonSessionController`)
- **담당 역할**:
  - 엔지니어링 비교 세션의 영속화(DB 저장), 북마크(⭐ Pinned), 프로젝트 폴더화(`+ 새 폴더`), 이력 삭제 관리.
- **컨트롤러 엔드포인트**:
  - `GET    /api/v1/comparison-sessions` (세션 목록 조회: Pinned 상단 고정, 폴더별 그룹 필터 지원)
  - `POST   /api/v1/comparison-sessions` (새 비교 세션 생성)
  - `GET    /api/v1/comparison-sessions/{session_id}` (세션 단건 상세 및 결과 복원)
  - `PATCH  /api/v1/comparison-sessions/{session_id}` (세션 메타 수정: 즐겨찾기 토글, 폴더 이동, 제목 변경)
  - `DELETE /api/v1/comparison-sessions/{session_id}` (세션 삭제)
- **서비스**: `ComparisonSessionService`
- **레포지토리**: `ComparisonSessionRepository`
- **엔티티**: `ComparisonSessionModel`, `ComparisonFolderModel`

---

### [도메인 2] 대화형 질문 구체화 & 3대 공학 분기 (`ComparisonClarifierController`)
- **담당 역할**:
  - 모호한 자연어 질문(예: "HBM 열 문제") 입력 시, 온톨로지 지식 그래프를 조회하여 엔지니어가 선택할 수 있는 **3대 공학 분기 카드**와 추천 평가 축을 도출.
- **컨트롤러 엔드포인트**:
  - `POST /api/v1/comparison/clarify`
- **서비스**: `ComparisonClarifierService` (내부적으로 `clarifier_agent` 호출)
- **요청 DTO**: `{ "query": "HBM 방열 문제", "baseConceptId": "concept-mrmuf" }`
- **응답 DTO**:
  - `ComparisonClarifyResponse`
    - `branchCards`: 3대 공학 분기 카드 리스트 (분기별 제목, 핵심 상충 메커니즘, 추천 파라미터 세트)
    - `targetA`, `targetB`: 자동 추론된 비교 대상 개념 후보
    - `dynamicAxes`: 추천 비교 평가 축

---

### [도메인 3] 다차원 비교 매트릭스 도출 (`ComparisonMatrixController`)
- **담당 역할**:
  - 확정된 대상 A와 대상 B, 그리고 평가 축을 기반으로 열·물성, 결함 리스크, 팹 양산성을 대조하는 **동적 매트릭스 테이블** 생성.
  - 사내 DB에 공인 실측 데이터가 없을 경우 억지 추정(환각)을 배제하고 **지식 갭(Knowledge Gap)** 태그 생성.
  - **🌟 온톨로지 보완 제안 자동 도출 파이프라인 내장 (`OntologyGapDetectorService`)**:
    - 매트릭스 계산 과정에서 실측치 부재(Gap)나 공인 출처 간 수치 모순(Conflict)이 감지되면, 에이전트가 "이 항목은 16단 적층 시 실측치 보완 필요"라는 `governanceProposal` 객체를 자동 생성하여 매트릭스 응답 DTO에 실어줌.
    - 프론트엔드는 이 데이터가 있을 때만 화면 하단에 검토 센터 전송 배너를 표출함.
- **컨트롤러 엔드포인트**:
  - `POST /api/v1/comparison-sessions/{session_id}/matrix`
- **서비스**: 
  - `ComparisonMatrixService` (매트릭스 생성 메인 오케스트레이션)
  - `OntologyGapDetectorService` (지식 갭 및 온톨로지 보완 제안 자동 도출 전담 서비스)
- **응답 DTO**: `ComparisonMatrixResponse` (동적 축 행 데이터, 지식 갭 경고, AI 종합 인과 코멘트, `governanceProposal` 객체)

---

### [도메인 4] + 비교 평가 축 즉석 추가 (`ComparisonAxisController`)
- **담당 역할**:
  - 엔지니어가 기본 축 외에 "CAPEX 설비 투자비 및 감가상각" 같은 **신규 축을 즉석에서 추가했을 때, 기존 테이블을 덮어쓰거나 전체 재계산하지 않고 오직 추가된 1개 행(Delta Single Row)만 즉석 계산하여 반환**.
  - 속도 1초 미만 보장 및 기존 매트릭스 데이터 100% 무결성 유지.
- **컨트롤러 엔드포인트**:
  - `POST /api/v1/comparison-sessions/{session_id}/axes`
- **서비스**: `ComparisonAxisService`
- **요청 DTO**: `{ "axisName": "CAPEX 설비 투자비", "category": "팹 양산성 & TAT" }`
- **응답 DTO**: `ComparisonAxisRowResponse` (추가된 단일 평가 행 및 두 대안별 지표 데이터)

---

### [도메인 5] AI 파라미터 튜닝 상담 (스냅샷 2 시점) (`ParameterAdvisorController`)
- **담당 역할**:
  - 엔지니어가 설비 한계(예: "우리 라인은 가압력을 150N 이상 못 줌")를 자연어로 제시할 때, 온톨로지 물리 인과 모델을 기반으로 **보상 수치 조합(추천안 A, B)과 트레이드오프(TAT 증가 등)를 역제안**.
- **컨트롤러 엔드포인트**:
  - `POST /api/v1/comparison-sessions/{session_id}/tune-advisor`
- **서비스**: `ParameterAdvisorService` (내부적으로 `advisor_agent` 호출)
- **응답 DTO**: `TuningAdvisorResponse` (안전 마진 분석, 추천 파라미터 세트 2종, 예상 결함 변화율)

---

### [도메인 6] 비교 분석 리포트 내보내기/다운로드 (`ComparisonExportController`)
- **담당 역할**:
  - 완성된 비교 매트릭스, 튜닝 조건, AI 종합 인과 코멘트를 사내 엔지니어링 표준 마크다운(Markdown) 문서 파일로 조합하여 다운로드 서빙.
- **컨트롤러 엔드포인트**:
  - `GET /api/v1/comparison-sessions/{session_id}/export?format={md|json}`
- **서비스**: `ComparisonExportService` (세션 데이터를 리포트 템플릿으로 렌더링)

---

## 2.3 타 도메인 연계 컴포넌트 명세 (비교분석 내 중복 신설 방지 규격)

### 2.3.1 🔍 대안 A / 대안 B 자동완성 검색 (전역 검색 재사용)
- **화면 트리거**: 화면 2-A 대안 A, 대안 B 입력란
- **처리 원칙**:
  - 별도의 비교 전용 검색 알고리즘이나 컨트롤러를 중복 신설하지 않습니다.
  - 전역 검색 도메인의 **`GET /api/v1/search/spotlight?type=concept&q={keyword}`**를 그대로 재사용하여, 온톨로지 개념 DB에서 서로 비교 가능한 대안 개념 목록(후보 5~10개)만 0ms로 필터링하여 바인딩합니다.

### 2.3.2 ✍️ 비교 분석 결과 ➔ 검토 센터 티켓 내보내기 (검토 센터 도메인 개편 시 연동)
- **화면 트리거**: 화면 2-B 최하단 거버넌스 배너 (`✍️ 이 분석 결과를 검토 센터로 전송하여 온톨로지에 반영하기` 버튼)
- **처리 원칙**:
  - 비교 도메인에서 티켓을 직접 생성하는 컨트롤러를 파지 않습니다.
  - **검토 센터가 스스로의 입력 DTO와 유효성 검증을 완벽히 통제해야 하므로, 향후 검토·승인 센터 도메인이 새로 개편될 때 정의될 정규 티켓 생성 API를 프론트엔드가 연계 호출**하도록 규정합니다.

---

## 2.4 에이전트 호출을 컨트롤러 단에서 분리해야 하는 3대 공학적 근거

1. **DTO 타입 계약(Type Safety)의 엄격성**:
   - `질문 구체화(분기 카드 반환)`와 `매트릭스(대조표 반환)`, `축 추가(단일 행 반환)`, `파라미터 튜닝(보상안 수치 반환)`은 Request와 Response의 형태가 완전히 다릅니다.
   - 하나의 컨트롤러로 뭉뚱그리면 DTO가 온갖 Optional 필드로 뒤범벅된 거대 잡탕 스키마가 되어 프론트엔드 연동 시 타입 에러를 양산합니다.
2. **RESTful 리소스 지향성**:
   - 세션 내부의 하위 리소스(`/matrix`, `/axes`, `/tune-advisor`, `/export`)로 분리되어 URL만 보아도 어떤 결과물을 기대하는지 명확합니다.
3. **독립적 장애 격리**:
   - 파라미터 튜닝 상담에 일시적인 LLM 타임아웃이 발생해도, 기본 비교 매트릭스 조회나 세션 목록 조회 등 다른 기능은 100% 정상 작동합니다.

---

# 3. ✍️ [Tab 3] 검토·승인 센터 (Review & Governance) 도메인 설계

## 3.1 화면 UI/UX 구성 및 핵심 거버넌스 원칙

검토·승인 센터는 라인 엔지니어의 수정 제안이나 AI 에이전트의 온톨로지 보완 제안을 **지식 검토관(Chief Reviewer)이 검증하고, AI 지시문 및 직접 편집을 거쳐 공용 위키에 안전하게 공식 반영(Publish)**하는 거버넌스 핵심 허브입니다.

```
[상단 상태 탭 필터: 검토 대기 (12) | 승인 완료 (38) | 반려됨 (5)]
                       │
[좌측 Pane: 검토 대기 티켓 큐 (기본값: status=pending)]
  │
  ├─ 티켓 선택 (MR-MUF 열저항 수치 보완 건 등)
  ▼
[2-Pane 비교·편집 워크스페이스]
  ├─ 좌측 Pane : [변경 전 원본 본문] vs [제안 발의 배경 및 사유]
  ├─ 우측 Pane : ★ [단일 작업 초안 (working_draft)] 통합 버퍼
  │                ├─ AI 지시문 바: "불변 제약 유지하고 가압력 범위만 재조정해줘" (지시 시 초안 자동 갱신)
  │                └─ 직접 편집 모드: 에디터에서 문장/수치 직접 타이핑 수정 (저장 시 초안 갱신)
  ▼
[실시간 가상 위키 미리보기 모달]  ◀── 원본 DB 오염 없이 working_draft를 메모리 상 가상 병합 (Virtual Merge)
  │
  ├─ [승인 및 공용 위키에 즉시 게시]  ◀── 단일 원자적 트랜잭션 (위키 버전 승계 v1.2➔v1.3 + 캐시 무효화)
  └─ [반려 (탈락 처리)]              ◀── 반려 사유 기록 ➔ status="rejected" ➔ 기본 대기열에서 즉시 탈락
```

### ① 과감히 제거된 불필요 요소
- **빠른 요청 칩(Quick Prompt Chips) 4종 전면 제거**:
  - 엔지니어링 실무에서 반도체 공정 지식 검토는 정형화된 버튼 클릭 몇 번으로 때울 수 없는 고도의 맥락적 작업입니다.
  - 불필요한 시각적 노이즈를 없애고 검토관이 정확한 의도를 자연어 지시문이나 직접 편집으로 전달하도록 집중도를 극대화합니다.

### ② 초안 충돌 및 누락 방지: [단일 작업 초안 (working_draft)] 일원화
- AI 초안과 전문가 직접 편집본을 별개 필드로 나누어 두면, 사람이 고친 내용을 AI 지시문이 날려버리거나 미리보기 시 기준이 꼬이는 치명적 결함이 발생합니다.
- 따라서 **`working_draft` (현재 작업 중인 단일 초안)** 버퍼 하나로 완전히 일원화합니다:
  1. 티켓 진입 시: 발의된 초안이 `working_draft`에 로드됨.
  2. **AI 수정 지시 시**: 에이전트가 현재 `working_draft`를 읽어 보완한 뒤 다시 `working_draft`를 갱신.
  3. **직접 편집 시**: 현재 `working_draft`를 에디터에 띄워 타이핑 수정 후 저장 (`working_draft` 갱신).
  4. **미리보기 시**: 항상 최신의 `working_draft` 하나만 원본과 대조하므로 충돌·누락 원천 차단.

### ③ 반려(Reject) 기본 원칙: [즉시 탈락 & 아카이브 분리]
- 검토관이 부적절한 제안을 반려할 경우, 반려 사유를 입력받고 상태를 `status="rejected"`로 변경합니다.
- 기본 검토 대기열(`status=pending`)에서는 **즉시 제외(탈락)**되어 검토관의 대기열이 항상 깨끗하게 유지됩니다.
- 탈락된 반려 건은 상단 탭에서 **[반려됨]**을 클릭했을 때만 사유와 함께 조회할 수 있습니다.

### ④ 임시 초안의 엄격한 프로덕션 DB 격리 원칙
- 검토관이 AI 지시문을 수행하거나 직접 편집기를 통해 글을 고쳐도, **승인 전까지는 `review_tickets` 테이블의 임시 필드(`working_draft`)에만 보관**됩니다.
- 공식 위키 본문 DB(`concepts` 테이블)는 **단 1바이트도 수정되지 않으며**, 승인(`POST /approve`)이 최종 집행되는 순간에만 원자적(Atomic)으로 공용 위키에 복사·반영됩니다.

---

## 3.2 도메인 컨트롤러 & 서비스 계층 정의

### [도메인 1] 검토 대기 큐 및 티켓 목록 서빙 (`ReviewTicketListController`)
- **담당 역할**:
  - 검토 티켓 목록을 서빙하며, **기본 대기열에서는 반려/승인 건을 자동 제외(탈락)**하여 표출.
  - 상단 탭 숫자 뱃지(`[대기중 (12)] | [승인완료 (38)] | [반려됨 (5)]`)를 위한 **상태별 집계 카운트(`tabCounts`)** 번들 제공.
  - 무한 스크롤 및 "더 불러오기"를 위한 페이징 메타데이터(`PageResponse`) 완비.
- **컨트롤러 엔드포인트**:
  - `GET /api/v1/review-tickets?status={pending|approved|rejected}&limit=20&offset=0`
  - *(쿼리 생략 시 기본값: `status=pending`)*
- **서비스**: `ReviewTicketService.get_ticket_list(status, limit, offset)`
- **레포지토리**: `ReviewTicketRepository.find_tickets(status, limit, offset)`, `ReviewTicketRepository.count_by_status()`
- **엔티티**: `ReviewTicketModel`
- **응답 DTO (`ReviewTicketPageResponse`)**:
  ```json
  {
    "items": [ ...티켓 DTO 리스트... ],
    "totalCount": 12,
    "hasMore": false,
    "offset": 0,
    "limit": 20,
    "tabCounts": {
      "pending": 12,
      "approved": 38,
      "rejected": 5
    }
  }
  ```

---

### [도메인 2] 2-Pane 검토 상세 워크스페이스 & 동시 편집 락 (`ReviewTicketDetailController`)
- **담당 역할**:
  - 목록에서 특정 티켓 클릭 시 2-Pane 검토에 필요한 전체 데이터 패키지 서빙:
    - 원본 지식 본문(`current_content`), 현재 단일 작업 초안(`working_draft`)
    - 온톨로지 정합성 점검 보고서(`integrity_report`: 인과 모순 여부, 공인 출처 불변 제약 준수율)
    - 과거 지시문 대화 이력(`directive_history`)
  - **분산 프레즌스 락(Presence Lock)**: 동일 티켓을 다른 검토관이 열람/수정 중인지 실시간 감지하여 편집 충돌 사전 차단.
- **컨트롤러 엔드포인트**:
  - `GET  /api/v1/review-tickets/{ticket_id}` (티켓 상세 및 편집자 락 상태 조회)
  - `POST /api/v1/review-tickets/{ticket_id}/presence` (동시 편집 락 획득/갱신/해제)
- **서비스**: 
  - `ReviewTicketService.get_ticket_detail(ticket_id)`
  - `PresenceLockService.manage_presence(ticket_id, action, editor_info)`
- **응답 DTO**: `ReviewTicketDetailDTO`, `PresenceLockResponse`

---

### [도메인 3] 전문가 AI 보완 지시문 실행 (`ReviewDirectiveController`)
- **담당 역할**:
  - 하단 지시문 입력창에서 전문가가 자연어로 보완 명령(예: "가압력 150N 상한선에 따른 보상 파라미터 언급을 추가하고 공인 출처 [E-01] 인용구는 유지해줘")을 내렸을 때 에이전트를 가동.
  - 현재의 `working_draft`를 기반으로 공인 출처 불변 제약을 보존하면서 초안을 재작성하고 `working_draft`를 자동 갱신.
- **컨트롤러 엔드포인트**:
  - `POST /api/v1/review-tickets/{ticket_id}/directive`
- **서비스**: `ReviewDirectiveService` (내부적으로 `directive_agent` 호출)
- **요청 DTO**: 
  - `DirectiveRequest`: `{ "directiveText": "...", "overrideReason": "..." }`
- **응답 DTO**: `ReviewTicketDTO` (갱신된 `working_draft`, 누적된 `directive_history`, 최신 정합성 보고서)

---

### [도메인 4] 전문가 직접 편집 모드 실시간 임시 저장 (`ReviewDraftSaveController`)
- **담당 역할**:
  - 우측 Pane의 인플레이스 직접 편집기(In-Place Editor)에서 전문가가 수치나 문장을 타이핑하여 수정한 내용을 `working_draft` 단일 버퍼에 임시 저장.
  - **낙관적 동시성 락(Optimistic Concurrency Lock)**: `ticket_version` 검사를 수행하여 다른 세션의 덮어쓰기 유실을 원천 차단.
  - **임시성 보장**: 오직 `ReviewTicketModel.working_draft` 컬럼에만 저장되며 공식 위키 DB에는 일절 영향을 주지 않음.
- **컨트롤러 엔드포인트**:
  - `PUT /api/v1/review-tickets/{ticket_id}/draft`
- **서비스**: `ReviewTicketService.save_draft(ticket_id, edited_content, ticket_version)`
- **요청 DTO**: `DraftSaveRequest`: `{ "editedContent": "...", "ticketVersion": 2 }`
- **응답 DTO**: `DraftSaveResponse` (갱신된 `ticketVersion`, `updatedAt`)

---

### [도메인 5] 승인 전 공용 위키 페이지 가상 미리보기 (`ReviewWikiPreviewController`)
- **담당 역할**:
  - 최종 승인 전, 본 개정안이 공용 위키에 게시되었을 때의 완성된 위키 상세 화면을 **메모리 상에서 가상 병합(Virtual Merge)**하여 미리 렌더링.
  - DB 원본 개념의 연관 데이터(출처 목록, 2-Hop 인과 서브그래프 등) 위에 최신 `working_draft`를 메모리 상에서 오버레이하고 변경 diff(`<mark class="diff-added">`)를 입혀서 서빙.
- **아키텍처 결정 (별도 컨트롤러 분리)**:
  - 기존 위키 본문 컨트롤러(`GET /api/v1/wiki-entries/{id}`)는 **공식 승인된 DB 데이터만 읽는 공개 게이트웨이**이므로 절대 오염시키지 않습니다.
  - 검토 센터 전용 미리보기 컨트롤러를 분리하여, 서비스 계층에서 기존 `WikiEntry` 조립 로직을 재사용하되 DB 원본 위에 현재 티켓의 `working_draft`를 메모리 상에서 오버레이 병합하여 안전하게 서빙합니다.
- **컨트롤러 엔드포인트**:
  - `GET /api/v1/review-tickets/{ticket_id}/wiki-preview?highlightChanges=true`
- **서비스**: `ReviewWikiPreviewService.generate_virtual_preview(ticket_id, highlight_changes)`
- **응답 DTO**: `WikiPreviewResponse` (가상 완성된 `preview_concept` 객체, 변경 단락 diff 요약)

---

### [도메인 6] 거버넌스 결정 집행 (승인 및 즉시 게시 / 반려 및 대기열 탈락) (`ReviewDecisionController`)
- **담당 역할**:
  - 지식 검토관이 승인 또는 반려 버튼을 클릭했을 때의 최종 거버넌스 액션 집행.
  - **① 승인 집행 (`POST /approve`)**:
    1. **권한 검증**: 요청 헤더 `X-User-Role`이 Chief Reviewer(승인권자)인지 엄격 판별 (일반 `line_engineer`는 403 차단).
    2. **단일 원자적 DB 트랜잭션**:
       - `concepts` 테이블의 공식 지식 본문을 최신 `working_draft`로 갱신.
       - 버전 번호를 기존 하드코딩 `v1.3`이 아닌 직전 버전(`v1.2`) 기준 동적 마이너 판본 승계(`v1.3`) 자동 반영.
       - 티켓 상태를 `status="approved"`, `approved_at`, `approved_by`로 확정.
    3. **위키 캐시 즉시 무효화**: 공개 위키 엔트리 캐시를 즉시 제거하여 모든 사용자가 0ms로 새 버전을 열람 가능하도록 보장.
  - **② 반려 집행 (`POST /reject`)**:
    1. **권한 검증**: Chief Reviewer 권한 확인.
    2. **반려 사유 기록 및 상태 변경**: `rejectReason` 기록 및 `status="rejected"`로 전환.
    3. **기본 대기열 즉시 탈락**: 상태가 변경되어 기본 대기열(`status=pending`)에서 즉시 사라지고 상단 [반려됨] 탭으로 아카이브.
- **컨트롤러 엔드포인트**:
  - `POST /api/v1/review-tickets/{ticket_id}/approve` (헤더: `X-User-Role`)
  - `POST /api/v1/review-tickets/{ticket_id}/reject` (헤더: `X-User-Role`)
- **서비스**: `ReviewDecisionService.approve(ticket_id, user_role, override_reason)` / `reject(ticket_id, user_role, reject_reason)`
- **응답 DTO**: `ReviewDecisionResponse` (처리 결과 상태, 승계된 버전 번호, 안내 메시지)

---

## 3.3 타 도메인 연계 컴포넌트 명세 (타 화면에서 검토 센터 호출 규격)

### 3.3.1 ✍️ 위키 본문 뷰 (Tab 1) ➔ 검토 티켓 신규 발행 연동
- **화면 트리거**: 위키 본문 최하단 `수정·보완 제안` 클릭 시 뜨는 모달 `[M-05]`
- **호출 규격**:
  - 위키 화면 프론트엔드가 검토 센터의 **`POST /api/v1/review-tickets`**를 호출.
  - 요청 페이로드: `{ "conceptId": "concept-mrmuf", "reviewType": "parameter_update", "title": "...", "humanEdits": "...", "reason": "..." }`
  - 검토 센터는 이를 접수하여 티켓을 `pending` 상태로 큐에 즉시 인양.

### 3.3.2 ⚖️ 기술 대안 비교분석 (Tab 2) ➔ 지식 갭 보완 티켓 발행 연동
- **화면 트리거**: 비교분석 매트릭스(화면 2-B) 최하단 `온톨로지 보완 제안 전송` 배너
- **호출 규격**:
  - 비교분석 응답 내에 포함된 `governanceProposal` 메타데이터를 담아 검토 센터의 **`POST /api/v1/review-tickets`** 호출.
  - 출처가 `comparison_gap`으로 태깅되어 검토관에게 비교 당시의 맥락과 결함 리스크가 그대로 전달됨.

---

## 3.4 거버넌스 기술 안전성 3대 원칙

1. **단일 작업 초안 (Single Working Draft) 무결성**:
   - AI 초안과 사람 수정본을 분리하지 않고 하나의 버퍼로 관리하여, 수정 지시나 직접 타이핑 중 데이터가 덮어써지거나 미리보기에서 누락되는 문제를 원천 차단합니다.
2. **이중 잠금 편집 충돌 방지 (Distributed Presence Lock + Optimistic Lock)**:
   - 입장 시 Redis/메모리 기반 비차단 프레즌스 락으로 동시 접속자를 안내하고, 저장 시 `ticket_version` 낙관적 락으로 덮어쓰기 사고를 원천 차단합니다.
3. **가상 병합(Virtual Merge)과 단일 원자적 게시 (Atomic Publishing)**:
   - 승인 전까지는 메모리 상 가상 병합으로만 미리보기를 서빙하여 프로덕션 DB를 100% 무결하게 유지하며, 최종 승인 시에만 단일 DB 트랜잭션으로 공용 위키에 즉시 반영하고 캐시를 갱신합니다.

---

# 4. 📑 [Tab 4] 외부 문헌·백서 조사 (Deep Research) 도메인 설계

## 4.1 화면 UI/UX 개편 및 듀얼 트랙(Dual Track) 워크플로우

외부 문헌·백서 조사실은 사내 온톨로지 DB에 아직 등록되지 않은 첨단 패키징/소자 기술의 **공인 학회 논문(IEEE, ECTC)과 제조사 공식 백서(Intel, TSMC 등)를 지능형 에이전트가 탐색·교차 분석하여, 사내 온톨로지에 신규 지식 후보로 편입(Publish to Governance)**시키는 지식 확장 엔진입니다.

```
                  [사용자 진입: 외부 문헌 조사실]
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
 [Track 1: 탐색형 (초보자 / 모호한 고민)]        [Track 2: 목적형 (숙련자 / 명확한 타깃)]
 "유리기판 TGV 균열 어떻게 잡지?"                "대상 개념: 유리기판(TGV), 출처: IEEE + Intel 백서"
         ↓                                               ↓
 에이전트 질문 구체화 (Clarify)                  온톨로지 검색창으로 개념 지정 + 출처 필터 직접 체크
         ↓                                               ↓
 ★ 3대 조사 범위(Scope) 칩 선택                 ★ 즉시 [심층 문헌 발굴 시작] 실행
         └───────────────────────┬───────────────────────┘
                                 ▼
         [⚡ 심층 조사 실행 ➔ 스텝 2: 2-Column 결과실 이동]
```

### ① 과감히 제거된 불필요 요소 (화면 집중도 극대화)
- **신뢰출처풀(Publisher Trust Pool) 거대 배너 전면 제거**:
  - Intel, TSMC, IEEE 등이 나열된 상단 거대 배너를 걷어내어 첫 화면 세로 공간을 확보하고 시각적 노이즈 차단.
- **발굴 추천 예시 칩 전면 제거**:
  - 고정된 클릭 유도용 칩들을 모두 없애 엔지니어가 본인의 탐구 목적에만 온전히 집중하도록 정돈.

### ② 좌측 사이드바: [날짜별 그룹화 (Date-based Grouping)] 이력 관리
- 외부 문헌 조사는 **"최신성(Recency)"과 "언제 조사했는가"가 핵심**이므로, 복잡한 폴더 대신 날짜별 그룹으로 정돈:
  - 📅 **오늘 (Today)**
  - 📅 **어제 (Yesterday)**
  - 📅 **이번 주 (This Week)**
  - 📅 **이전 기록 (Older)**
  - *(상단에 키워드 검색창 및 즐겨찾기 ⭐ Pin 기능 지원)*

### ③ 스텝 2: 결과실 2-Column Split View 레이아웃
- 발굴된 정보의 신뢰성을 엔지니어가 즉시 검증할 수 있도록 **좌측(원문 증빙 피드) vs 우측(AI 종합 분석 & 온톨로지 편입 제안)**을 한 화면에 나란히 대조 배치:

```
┌──────────────────────────────────────┬──────────────────────────────────────┐
│ [좌측 Pane: 공인 출처 증빙 피드]     │ [우측 Pane: AI 종합 분석 & 온톨로지 편입 후보]│
├──────────────────────────────────────┼──────────────────────────────────────┤
│ 📄 Intel Glass Core Architecture     │ 📊 AI 교차 분석 종합 리포트          │
│ - 출처: Intel Corp (Tier 1 공인 백서)│ - 물리적 메커니즘 요약               │
│ - 인용: "...Aspect ratio 10:1 초과 시│ - 학계 vs 제조사 공정 마진 비교       │
│   레이저 식각 미세 균열 경계 한계..."│ - 미세 균열 방지 보상 파라미터 도출  │
│ - [공식 원문 PDF 열람 ↗]            │                                      │
│                                      │ ──────────────────────────────────── │
│ 📄 IEEE ECTC 2025 Paper              │ 💡 온톨로지 편입 제안 후보 (Candidate) │
│ - 출처: IEEE (Tier 1 공인 학회 논문) │ - [신규 개념 제안]: TGV 미세 균열 상쇄 레시피│
│ - 인용: "화학적 연마 15nm 처리 시..."│ - [기존 보완 제안]: 유리기판 열팽창 계수 패치│
│                                      │ - [✍️ 검토 센터로 티켓 발행하기 ➔]   │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

## 4.2 도메인 컨트롤러 & 서비스 계층 정의

### [도메인 1] 최근 발굴 로그 및 날짜별 세션 관리 (`ResearchSessionController`)
- **담당 역할**:
  - 외부 문헌 조사 세션의 영속화(DB 저장), 날짜별 그룹 서빙(`today`, `yesterday`, `thisWeek`, `older`), 북마크(⭐ Pin), 검색 필터링, 이력 삭제.
- **컨트롤러 엔드포인트**:
  - `GET    /api/v1/research/sessions` (세션 목록 조회: 날짜별 그룹 및 Pinned 상단 고정 서빙)
  - `GET    /api/v1/research/sessions/{session_id}` (세션 단건 상세 및 결과 복원 서빙)
  - `PATCH  /api/v1/research/sessions/{session_id}` (세션 메타 수정: 즐겨찾기 토글, 제목 변경)
  - `DELETE /api/v1/research/sessions/{session_id}` (세션 삭제)
- **서비스**: `ResearchSessionService`
- **레포지토리**: `ResearchSessionRepository`
- **엔티티**: `ResearchSessionModel` (테이블: `research_sessions`)
- **응답 DTO (`ResearchSessionListResponse`)**:
  ```json
  {
    "groups": {
      "today": [ ...세션 요약 DTO... ],
      "yesterday": [ ... ],
      "thisWeek": [ ... ],
      "older": [ ... ]
    },
    "totalCount": 24
  }
  ```

---

### [도메인 2] 대화형 조사 범위 구체화 에이전트 (`ResearchClarifyController`)
- **담당 역할**:
  - [Track 1: 탐색형] 사용자의 자연어 질문(예: "유리기판 TGV 균열 문제") 입력 시, 온톨로지 지식 그래프와 학술 인덱스를 조회하여 **3대 조사 범위(Scope Filters) 및 핵심 검색 키워드**를 자동으로 좁혀서 도출.
- **컨트롤러 엔드포인트**:
  - `POST /api/v1/research/clarify`
- **서비스**: `ResearchClarifyService` (내부적으로 `deep_research_agent.clarify` 호출)
- **요청 DTO**: `ResearchClarifyRequest`: `{ "query": "차세대 유리기판 TGV 공정 및 물성 표준 규격" }`
- **응답 DTO**: `ResearchClarifyResponse` (추천 조사 스코프 칩 목록, 타깃 기관 후보, 정제된 학술 검색어)

---

### [도메인 3] 공인 출처 증빙 피드 수집·발굴 (`ResearchDiscoverController`)
- **담당 역할**:
  - 확정된 키워드와 선택된 스코프/기관 필터를 기반으로 공인 출처 풀(Intel/TSMC 백서, IEEE 논문, SEMI 표준)에서 **실제 공인 원문 증빙 피드(Evidence Feed)**를 발굴 및 적재.
  - 가짜 정보나 환각을 방지하기 위해 출처명, 발행처, 발행일자, 원문 인용구(Quote), 신뢰도 등급(Tier 1/2), 원문 링크를 엄격히 구조화하여 서빙.
- **컨트롤러 엔드포인트**:
  - `POST /api/v1/research/sessions/{session_id}/discover`
- **서비스**: `ResearchDiscoverService`
- **요청 DTO**: `ResearchDiscoverRequest`: `{ "scopeFilterIds": ["gen-ai-package", "thickness-100um"] }`
- **응답 DTO**: `ResearchDiscoverResponse` (`evidenceFeed: List[ResearchEvidenceFeedItem]`)

---

### [도메인 4] 문헌 종합 교차 분석 및 온톨로지 편입 후보 도출 (`ResearchSynthesisController`)
- **담당 역할**:
  - 발굴된 복수의 문헌들을 지능형 에이전트가 교차 분석(Cross-Analysis)하여 **종합 분석 리포트(`synthesis_report`)**를 작성하고,
  - 사내 온톨로지에 편입할 만한 **지식 후보(`candidates`)를 도출** (신규 개념 후보 등록 또는 기존 개념 수치 패치).
- **컨트롤러 엔드포인트**:
  - `POST /api/v1/research/sessions/{session_id}/synthesize`
- **서비스**: `ResearchSynthesisService` (내부적으로 `deep_research_agent.synthesize` 호출)
- **응답 DTO**: 
  - `ResearchSynthesizeResponse`
    - `synthesisReport`: 물리적 메커니즘, 기술적 한계 및 트레이드오프, 학계 vs 업계 이견 분석
    - `candidates`: 온톨로지 편입 제안 후보 목록 (제목, 제안 사유, 대상 개념 ID, 추천 파라미터)

---

### [도메인 5] 문헌 조사 종합 리포트 내보내기/다운로드 (`ResearchExportController`)
- **담당 역할**:
  - 수집된 공인 출처 증빙 피드(인용구, 메타데이터, 원문 링크), AI 교차 분석 종합 리포트, 온톨로지 편입 후보를 사내 기술 표준 마크다운(Markdown) 보고서 파일로 조합하여 다운로드 서빙.
- **컨트롤러 엔드포인트**:
  - `GET /api/v1/research/sessions/{session_id}/export?format={md|pdf}`
- **서비스**: `ResearchExportService` (세션 데이터를 기술 동향 보고서 템플릿으로 렌더링)
- **응답**: `FileResponse` (Markdown/PDF 파일 다운로드 스트림)

---

## 4.3 타 도메인 연계 컴포넌트 명세 (타 도메인과의 중복 신설 방지 규격)

### 4.3.1 🔍 Track 2 목적형 개념 타깃팅 (전역 검색 재사용)
- **화면 트리거**: [Track 2: 목적형] 검색실의 대상 개념 입력창
- **처리 원칙**:
  - 별도의 검색 컨트롤러를 신설하지 않고 전역 검색 도메인의 **`GET /api/v1/search/spotlight?type=concept&q={keyword}`**를 100% 재사용.
  - 사내 온톨로지 DB에 이미 등록되어 있는 단위 공정/소자 개념을 0ms 자동완성으로 타깃팅.

### 4.3.2 ✍️ 온톨로지 편입 후보 ➔ 검토 센터 거버넌스 티켓 직결 연동
- **화면 트리거**: 우측 하단 온톨로지 편입 제안 후보 카드의 `[✍️ 검토 센터로 티켓 발행하기 ➔]` 버튼
- **호출 규격**:
  - 프론트엔드가 후보 카드 클릭 시 검토 센터의 **`POST /api/v1/review-tickets`**를 직결 호출.
  - 요청 페이로드:
    ```json
    {
      "conceptId": "concept-tgv-etching",
      "reviewType": "literature_candidate",
      "title": "[문헌 발굴] 유리기판 레이저 식각 미세 균열 방지 보상 레시피 반영",
      "humanEdits": "IEEE ECTC 2025 논문 실측치 기반 가압력 및 화학적 연마 보상 조건...",
      "originType": "research_candidate",
      "sourceSessionId": "res-20261016-01"
    }
    ```
  - 검토 센터는 이를 접수하여 티켓을 `pending` 대기열에 인양하고, 좌측 Pane에 발굴 당시의 백서 인용구와 출처 링크를 그대로 보존하여 검토관에게 서빙.

---

## 4.4 외부 문헌 조사 3대 엔지니어링 신뢰 원칙

1. **날짜별 직관적 이력 관리 (Recency-first Memory)**:
   - "언제 조사했는가"를 기준으로 날짜 그룹을 나누어, 빠르게 변화하는 최신 반도체 학술/백서 탐색 이력을 가장 직관적으로 재탐색할 수 있게 지원합니다.
2. **공인 출처 근거 중심주의 (Zero Hallucination / Evidence-anchored)**:
   - LLM 자체의 모호한 기억이 아닌, 반드시 Intel, TSMC, IEEE 등 공인 출처의 원문 인용구(Quote)와 링크를 확보한 상태에서만 분석 리포트를 렌더링합니다.
3. **발굴에서 거버넌스 승인까지의 단일 지식 파이프라인 (Discovery-to-Governance Pipeline)**:
   - 조사실에서 발견된 첨단 지식이 단순 일회성 열람으로 끝나지 않고, 단 한 번의 클릭으로 검토 센터(Tab 3) 큐에 안착하여 공용 위키(Tab 1)까지 공식 승계되는 선순환 구조를 완성합니다.

---

# 5. 🤖 [F-01] 플로팅 엔지니어 챗봇 & 공통 도메인 설계 (작성 예정)

*(사용자님과 다음 대화에서 요구사항 분석 후 통합 작성)*
