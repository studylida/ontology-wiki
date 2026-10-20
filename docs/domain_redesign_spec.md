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
- **컨트롤러 엔드포인트**:
  - `POST /api/v1/comparison-sessions/{session_id}/matrix`
- **서비스**: `ComparisonMatrixService` (내부적으로 `comparison_agent` 호출)
- **응답 DTO**: `ComparisonMatrixResponse` (동적 축 행 데이터, 지식 갭 경고, AI 종합 인과 코멘트)

---

### [도메인 4] AI 파라미터 튜닝 상담 (스냅샷 2 시점) (`ParameterAdvisorController`)
- **담당 역할**:
  - 엔지니어가 설비 한계(예: "우리 라인은 가압력을 150N 이상 못 줌")를 자연어로 제시할 때, 온톨로지 물리 인과 모델을 기반으로 **보상 수치 조합(추천안 A, B)과 트레이드오프(TAT 증가 등)를 역제안**.
- **컨트롤러 엔드포인트**:
  - `POST /api/v1/comparison-sessions/{session_id}/tune-advisor`
- **서비스**: `ParameterAdvisorService` (내부적으로 `advisor_agent` 호출)
- **응답 DTO**: `TuningAdvisorResponse` (안전 마진 분석, 추천 파라미터 세트 2종, 예상 결함 변화율)

---

### [도메인 5] 엔지니어 꼬리질문 3-Hop 역추적 (`DeepDiveCausalController`)
- **담당 역할**:
  - "원인의 원인을 파고드는" 엔지니어의 심층 질의에 대해, 온톨로지 인과 그래프를 3-hop까지 역추적하여 인과 체인 다이어그램과 물리 방정식 기반 해설 제공.
- **컨트롤러 엔드포인트**:
  - `POST /api/v1/comparison-sessions/{session_id}/deep-dive`
- **서비스**: `DeepDiveCausalService` (내부적으로 `CausalGraphRepository` 및 LLM 게이트웨이 연계)
- **응답 DTO**: `DeepDiveCausalResponse` (3-hop 인과 노드 체인, 핵심 물리 방정식, 추천 꼬리질문 칩)

---

## 2.3 에이전트 호출을 컨트롤러 단에서 분리해야 하는 3대 공학적 근거

1. **DTO 타입 계약(Type Safety)의 엄격성**:
   - `질문 구체화(분기 카드 반환)`와 `파라미터 튜닝(보상안 수치 반환)`, `꼬리질문(인과 체인 반환)`은 Request와 Response의 형태가 완전히 다릅니다.
   - 하나의 컨트롤러로 뭉뚱그리면 DTO가 온갖 Optional 필드로 뒤범벅된 거대 잡탕 스키마가 되어 프론트엔드 연동 시 타입 에러를 양산합니다.
2. **RESTful 리소스 지향성**:
   - 세션 내부의 하위 리소스(`/matrix`, `/tune-advisor`, `/deep-dive`)로 분리되어 URL만 보아도 어떤 결과물을 기대하는지 명확합니다.
3. **독립적 장애 격리**:
   - 파라미터 튜닝 상담에 일시적인 LLM 타임아웃이 발생해도, 기본 비교 매트릭스 조회나 세션 목록 조회 등 다른 기능은 100% 정상 작동합니다.

---

# 3. ✍️ [Tab 3] 검토·승인 센터 (Review & Governance) 도메인 설계 (작성 예정)

*(사용자님과 다음 대화에서 요구사항 분석 후 통합 작성)*

---

# 4. 📑 [Tab 4] 외부 문헌·백서 조사 (Deep Research) 도메인 설계 (작성 예정)

*(사용자님과 다음 대화에서 요구사항 분석 후 통합 작성)*

---

# 5. 🤖 [F-01] 플로팅 엔지니어 챗봇 & 공통 도메인 설계 (작성 예정)

*(사용자님과 다음 대화에서 요구사항 분석 후 통합 작성)*
