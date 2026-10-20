# 📖 온톨로지 위키 도메인 재설계 및 계층별 아키텍처 명세서

> **문서 목적**:  
> 위키 화면의 실제 사용자 인터랙션 및 User Flow를 기반으로,  
> 기존의 비대한 단일 `concepts` 구조를 관심사별로 분리하여  
> **Controller ➔ Service ➔ Repository ➔ Entity** 구조를 정밀하게 재설계하기 위한 기준 문서입니다.

---

## 1. 위키 페이지 컴포넌트별 5대 핵심 도메인 컨트롤러 & 서비스 정의

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
  - **폴백 방식 (온디맨드 팝오버 API)**: 사전 적재되지 않은 낯선 용어 클릭 시 단독 호출.
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

## 2. 컨트롤러 vs 서비스 역할 분리 기준

| 계층 | 역할 (Role) | 허용되는 작업 | 절대 금지 작업 |
| :--- | :--- | :--- | :--- |
| **Controller** | HTTP 진입점 (Gatekeeper) | URL 파라미터 검증, 권한 헤더(`X-User-Role`) 추출, 서비스 호출, HTTP 상태 코드(200, 404) 반환 | DB 쿼리 실행, SQL 작성, 비즈니스 가공, 마스킹 정규식 실행 |
| **Service** | 비즈니스 로직 (Brain) | 레포지토리 호출, 엔티티 결합, 비식별화/마스킹 정책 적용, 그래프 DTO 가공, 캐시 처리 | HTTP 세션/헤더 직접 접근, Request 객체 파싱 |
| **Repository** | 순수 데이터 접근 (Data Access) | SQLAlchemy `AsyncSession` 기반 쿼리 수행, 엔티티 객체 또는 원시 Row 리스트 반환 | 비즈니스 조건문 분기, 가짜 하드코딩 폴백 반환 |
| **Entity** | 물리 스키마 매핑 (Data Model) | SQLite 물리 테이블 컬럼 및 외래키/관계 정의 | 로직이나 변환 코드 포함 |
