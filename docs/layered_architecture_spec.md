# 🏛️ 반도체 온톨로지 계층형 아키텍처 상세 설계서
## (Layered Architecture Spec: Entity ➔ DTO ➔ Repository ➔ Service)

> **문서 목적**:  
> 본 문서는 [Tab 1 위키], [Tab 2 비교분석], [Tab 3 검토센터], [Tab 4 문헌조사], [플로팅 챗봇] 전 도메인을 대상으로,  
> 기존의 "화면 DTO를 JSON 컬럼에 통째로 때려 박았던 기형적 Entity"를 전면 개편하고,  
> **Entity(물리 RDBMS 정규화 스키마) ➔ DTO(Pydantic 계약 스펙) ➔ Repository(순수 데이터 접근) ➔ Service(비즈니스 로직)**의  
> 정통 4계층 분리 기준과 인터페이스 규격을 단일 문서에서 통합 관리하기 위한 마스터 기준서입니다.

---

# 1. 📖 [Tab 1] 위키 본문 뷰 (Public Wiki) 계층 설계

## 1.1 물리 Entity 스키마 설계 (Physical Database Schema)

기존의 `principles`, `limitations`, `relations`, `specifications` 등 JSON 컬럼 남용을 전면 철폐하고, **외래키 무결성과 3정규형을 충족하는 정규화 물리 테이블로 재구축**합니다.

```
┌─────────────────────────────────┐
│     concepts (개념 마스터)      │
├─────────────────────────────────┤
│ PK  id                          │
│     title, eng_name, aliases    │
│     domain_facet, scale_level   │
│     version, summary, purpose   │
└──────────────┬──────────────────┘
               │ 1:N
       ┌───────┼──────────────────┬──────────────────┐
       ▼       ▼                  ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────────────────┐
│concept_      │ │concept_      │ │perspective_  │ │causal_edges             │
│principles    │ │limitations   │ │cases         │ │(온톨로지 관계 단일 통합)│
├──────────────┤ ├──────────────┤ ├──────────────┤ ├─────────────────────────┤
│PK id         │ │PK id         │ │PK id         │ │PK id                    │
│FK concept_id │ │FK concept_id │ │FK concept_id │ │FK source_concept_id     │
│   step_order │ │   title      │ │   title      │ │FK target_concept_id     │
│   title      │ │   description│ │   context    │ │   relation_type         │
│   content    │ │FK evidence_id│ └──────┬───────┘ │   (is_a, part_of,       │
│   formula    │ └──────────────┘        │ 1:N     │    next_step, causes...)│
└──────────────┘                         ▼         │   mechanism_label       │
                                  ┌──────────────┐ │   compensating_params   │
                                  │perspective_  │ └─────────────────────────┘
                                  │specifications│
                                  ├──────────────┤
                                  │PK id         │
                                  │FK case_id    │
                                  │   label      │
                                  │   val_numeric│
                                  │   unit       │
                                  │   is_conf_l3 │
                                  │FK evidence_id│
                                  └──────────────┘
```

---

### [테이블 1] `concepts` (개념 물리 마스터 테이블)
- **테이블명**: `concepts`
- **책임**: 단위 공정 및 소자 개념의 기본 신원(Identity), 카테고리 계층, 동적 버전 관리.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | 개념 고유 식별자 (예: `concept-mrmuf`) |
| `title` | `VARCHAR(128)` | `NOT NULL` | 개념 한글 공식 명칭 (예: `MR-MUF`) |
| `eng_name` | `VARCHAR(128)` | `NOT NULL` | 공식 영문 명칭 (예: `Molded Underfill`) |
| `aliases` | `JSON` | `DEFAULT '[]'` | 동의어 및 약칭 리스트 (`["MUF", "액상 몰딩 언더필"]`) |
| `domain_facet` | `VARCHAR(32)` | `NOT NULL, INDEX` | 4대 업무 분야 (`device_family`, `unit_process`, `fab_intelligence`, `materials_infra`) |
| `process_category` | `VARCHAR(64)` | `NOT NULL, INDEX` | 상세 공정 분류 (`첨단 패키징`, `건식 식각`, `박막 증착` 등) |
| `scale_level` | `INTEGER` | `NOT NULL, INDEX` | 온톨로지 스케일 레벨 (1~5) |
| `scale_name` | `VARCHAR(64)` | `NULLABLE` | 스케일 표기명 (`L3 단위 공정`) |
| `version` | `VARCHAR(16)` | `DEFAULT 'v1.2', NOT NULL` | 동적 판본 버전 번호 (승인 시 v1.3 등 승계) |
| `status` | `VARCHAR(16)` | `DEFAULT 'adopted', NOT NULL` | 지식 상태 (`adopted`, `under_review`, `deprecated`) |
| `last_reviewed_at`| `DATETIME` | `NULLABLE` | 최종 거버넌스 승인 일시 |
| `last_reviewed_by`| `VARCHAR(64)` | `NULLABLE` | 최종 승인권자 ID/사번 |
| `summary` | `TEXT` | `NOT NULL` | 1번 섹션: 개념 개요 본문 |
| `purpose` | `TEXT` | `NOT NULL` | 공정 도입 목적 및 핵심 엔지니어링 미션 |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 레코드 생성 일시 |
| `updated_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 레코드 최종 수정 일시 |

> **🚨 개편 핵심**: 기존의 `principles`, `limitations`, `relations` JSON 컬럼을 완전히 영구 삭제함.

---

### [테이블 2] `concept_principles` (공정 물리 작동 원리 및 단계 정규화 테이블)
- **테이블명**: `concept_principles`
- **책임**: 2번 섹션 "물리적 작동 원리"의 단계별(Step-by-Step) 공정 메커니즘과 KaTeX 수식 정규화 관리.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 원리 단계 고유 ID |
| `concept_id` | `VARCHAR(64)` | `NOT NULL, FK(concepts.id ON DELETE CASCADE), INDEX` | 대상 개념 ID |
| `step_order` | `INTEGER` | `NOT NULL` | 작동 단계 순서 (1, 2, 3...) |
| `title` | `VARCHAR(128)` | `NOT NULL` | 단계 제목 (예: `일괄 솔더 리플로우 (Mass Reflow)`) |
| `content` | `TEXT` | `NOT NULL` | 물리 원리 설명 본문 |
| `formula` | `TEXT` | `NULLABLE` | KaTeX 수식 텍스트 (예: `Q = \frac{\pi r^4 \Delta P}{8 \eta L}`) |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 생성 일시 |
| `updated_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 수정 일시 |

---

### [테이블 3] `concept_limitations` (공정 물리 한계 및 결함 메커니즘 정규화 테이블)
- **테이블명**: `concept_limitations`
- **책임**: 2번 섹션 "물리적 공정 한계"의 결함 리스크와 공인 출처 증빙(`evidence_id`) 외래키 연결.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 한계 항목 고유 ID |
| `concept_id` | `VARCHAR(64)` | `NOT NULL, FK(concepts.id ON DELETE CASCADE), INDEX` | 대상 개념 ID |
| `title` | `VARCHAR(128)` | `NOT NULL` | 한계 제목 (예: `필러 트래핑 (Filler Jamming)`) |
| `description` | `TEXT` | `NOT NULL` | 결함 발생 원인 및 물리적 한계 메커니즘 |
| `evidence_id` | `VARCHAR(64)` | `NULLABLE, FK(evidence_sources.id ON DELETE SET NULL), INDEX` | 공인 출처 증빙 ID (`E-01`) |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 생성 일시 |
| `updated_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 수정 일시 |

---

### [테이블 4] `perspective_cases` (다도메인 실무 적용 사례 테이블)
- **테이블명**: `perspective_cases`
- **책임**: 3번 섹션 "다도메인 실무 적용 사례(Perspectives)"의 맥락 서술 및 관리 코드 관리.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | 사례 고유 식별자 (예: `case-mrmuf-hbm3e`) |
| `concept_id` | `VARCHAR(64)` | `NOT NULL, FK(concepts.id ON DELETE CASCADE), INDEX` | 대상 개념 ID |
| `perspective_id` | `VARCHAR(32)` | `NOT NULL` | 관점 식별자 (`hbm3e_advanced`, `yield`, `capex`) |
| `perspective_title`| `VARCHAR(128)` | `NOT NULL` | 관점 제목 (예: `HBM3E 16단 적층 열방열 극대화 관점`) |
| `perspective_badge`| `VARCHAR(64)` | `NOT NULL` | 관점 뱃지명 (예: `양산 적용 사례 · Tier 3`) |
| `management_code` | `VARCHAR(64)` | `NULLABLE` | 사내 관리 코드 (예: `HBM-PKG-MRMUF-001`) |
| `context_narrative`| `TEXT` | `NOT NULL` | 양산 실무 적용 맥락 스토리텔링 |
| `caution` | `TEXT` | `NOT NULL` | 현업 적용 시 필수 주의사항 |
| `evidence_id` | `VARCHAR(64)` | `NULLABLE, FK(evidence_sources.id ON DELETE SET NULL), INDEX` | 공인 출처 증빙 ID |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 생성 일시 |
| `updated_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 수정 일시 |

> **🚨 개편 핵심**: 기존의 `specifications` JSON 컬럼을 완전히 제거하고 아래 하위 테이블로 정규화 분리함.

---

### [테이블 5] `perspective_specifications` (양산 절대 수치 스펙 및 L3 보안 플래그 정규화 테이블)
- **테이블명**: `perspective_specifications`
- **책임**: 3번 섹션 내의 핵심 수치 지표(온도, 압력, 열전도도 등)의 정밀 수치, 단위, 허용 오차 범위, 그리고 **L3 보안 비식별화 대상 플래그(`is_confidential_l3`)를 물리 컬럼으로 엄격 관리**.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 사양 항목 고유 ID |
| `case_id` | `VARCHAR(64)` | `NOT NULL, FK(perspective_cases.id ON DELETE CASCADE), INDEX` | 소속된 관점 사례 ID |
| `label` | `VARCHAR(128)` | `NOT NULL` | 지표 명칭 (예: `리플로우 피크 온도`, `액상 몰딩 주입 압력`) |
| `val_numeric` | `VARCHAR(64)` | `NOT NULL` | 양산 실측 수치 원본 (예: `260`, `0.45`, `2.5`) |
| `unit` | `VARCHAR(32)` | `NOT NULL` | 물리 단위 (예: `℃`, `MPa`, `W/m·K`) |
| `criteria` | `VARCHAR(128)` | `NULLABLE` | 허용 공차/판정 기준 (예: `255℃ ~ 265℃`, `0.40 ~ 0.50MPa`) |
| `role` | `VARCHAR(64)` | `NOT NULL` | 엔지니어링 역할 식별자 (`reflow_temp`, `injection_pressure`) |
| `is_confidential_l3`| `BOOLEAN` | `DEFAULT TRUE, NOT NULL` | **L1/L2 권한 시 마스킹해야 하는 L3 절대 기밀 수치 여부** |
| `evidence_id` | `VARCHAR(64)` | `NULLABLE, FK(evidence_sources.id ON DELETE SET NULL), INDEX` | 공인 출처 증빙 ID |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 생성 일시 |
| `updated_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 수정 일시 |

---

### [테이블 6] `causal_edges` (온톨로지 인과 및 관계 단일 진실 공급원 - Single Source of Truth)
- **테이블명**: `causal_edges`
- **책임**: 
  - `ConceptModel.relations` JSON 컬럼을 없애고, **온톨로지의 모든 관계(`is_a`, `part_of`, `next_step`, `alternative_to`, `causes_defect`, `compensates`)를 단일 물리 테이블에서 일원화 관리**.
  - 2-Hop SQLite 재귀 CTE 그래프 탐색 및 보상 파라미터(`compensating_params`) 관리.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 에지 고유 식별자 |
| `source_concept_id`| `VARCHAR(64)` | `NOT NULL, FK(concepts.id ON DELETE CASCADE), INDEX` | 출발 노드 개념 ID |
| `target_concept_id`| `VARCHAR(64)` | `NOT NULL, FK(concepts.id ON DELETE CASCADE), INDEX` | 도착 노드 개념 ID |
| `relation_type` | `VARCHAR(32)` | `NOT NULL, INDEX` | 관계 유형: `is_a`, `part_of`, `next_step`, `alternative_to`, `causes_defect`, `compensates` |
| `polarity` | `VARCHAR(16)` | `DEFAULT '+'` | 인과 극성 (`+`, `-`, `tradeoff`) |
| `weight` | `NUMERIC(3, 2)`| `DEFAULT 1.00` | 관계 가중치 및 신뢰도 |
| `mechanism_label` | `TEXT` | `NOT NULL` | 물리 메커니즘 라벨 ("180N 초과 시 NCF 유동성 한계...") |
| `compensating_params`| `JSON` | `NULLABLE` | 보상 파라미터 수식 및 트레이드오프 JSON |
| `evidence_id` | `VARCHAR(64)` | `NULLABLE, FK(evidence_sources.id ON DELETE SET NULL)` | 공인 증빙 ID |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 생성 일시 |
| `updated_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 수정 일시 |

---

### [테이블 7] `evidence_sources` (공식 검증 출처 원문 물리 테이블)
- **테이블명**: `evidence_sources`
- **책임**: 본문 각주 `[E-01]` 클릭 시 서빙되는 공인 논문/백서 메타데이터와 인용구 관리.
- **컬럼 정의**: `id(PK)`, `source_name`, `source_type`, `publisher`, `published_date`, `quote`, `section_context`, `relevance_score`, `external_url`, `url_label`, `credibility_tier`.

---

## 1.2 계약 DTO 설계 (API Contract Schemas)

프론트엔드 화면 컴포넌트와 통신하는 Pydantic DTO 스키마입니다.  
**물리 Entity를 클라이언트에 직접 노출하지 않고, Service 계층에서 보안 등급에 따라 수치를 마스킹한 후 DTO로 변환하여 서빙**합니다.

```python
# 1. 공정 원리 단계 DTO
class PrincipleItemDTO(BaseModel):
    step: int
    title: str
    content: str
    formula: Optional[str] = None

# 2. 공정 한계 DTO
class LimitationItemDTO(BaseModel):
    title: str
    description: str
    evidenceId: Optional[str] = None

# 3. 양산 수치 사양 DTO (마스킹 적용 결과)
class SpecificationDTO(BaseModel):
    label: str
    value: str               # 권한 부족 시 "[비식별화 보호 - L3 보안 인가 필요]"
    unit: str
    criteria: Optional[str] = None
    role: str
    isMasked: bool           # L3 마스킹 적용 여부
    evidenceId: Optional[str] = None

# 4. 다도메인 실무 사례 DTO
class PerspectiveCaseDTO(BaseModel):
    id: str
    perspectiveId: str
    perspectiveTitle: str
    perspectiveBadge: str
    managementCode: Optional[str] = None
    contextNarrative: str
    specifications: List[SpecificationDTO]
    caution: str
    evidenceId: Optional[str] = None

# 5. 온톨로지 관계 링크 칩 묶음 DTO (Service가 causal_edges에서 조립)
class RelationTargetDTO(BaseModel):
    id: str
    name: str

class AlternativeTargetDTO(BaseModel):
    targetId: str
    targetName: str
    commonGoal: str

class RelationsBundleDTO(BaseModel):
    is_a: List[RelationTargetDTO] = []
    part_of: List[RelationTargetDTO] = []
    next_step: List[RelationTargetDTO] = []
    alternative_to: List[AlternativeTargetDTO] = []

# 6. 위키 본문 전체 상세 응답 DTO (WikiEntryDetailResponse)
class WikiEntryDetailResponse(BaseModel):
    id: str
    title: str
    engName: str
    aliases: List[str]
    domainFacet: str
    processCategory: str
    scaleLevel: int
    scaleName: str
    version: str
    status: str
    lastReviewedAt: Optional[str]
    lastReviewedBy: Optional[str]
    summary: str
    purpose: str
    principles: List[PrincipleItemDTO]
    limitations: List[LimitationItemDTO]
    perspectives: List[PerspectiveCaseDTO]
    relations: RelationsBundleDTO
    preloadedExplainers: Dict[str, str] = {}
```

---

## 1.3 Repository 계층 설계 (Data Access Layer)

비즈니스 로직이나 HTTP 헤더를 일절 다루지 않으며, **오직 SQLAlchemy `AsyncSession` 기반의 순수 DB 쿼리(CRUD, Eager Loading, SQLite 재귀 CTE)만 수행하여 Entity 객체들을 반환**합니다.

### ① `ConceptRepository` 인터페이스
```python
class ConceptRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, concept_id: str) -> Optional[ConceptModel]:
        """개념 단건 조회 (principles, limitations Eager Loading 결합)."""
        stmt = (
            select(ConceptModel)
            .options(
                selectinload(ConceptModel.principles),
                selectinload(ConceptModel.limitations)
            )
            .where(ConceptModel.id == concept_id)
        )
        return (await self.db.execute(stmt)).scalars().first()

    async def get_by_facet(self, facet: str) -> List[ConceptModel]:
        """카테고리 트리 구성을 위한 업무 분야별 개념 목록 조회."""
        stmt = (
            select(ConceptModel)
            .where(ConceptModel.domain_facet == facet)
            .order_by(ConceptModel.scale_level.asc(), ConceptModel.title.asc())
        )
        return (await self.db.execute(stmt)).scalars().all()

    async def search_by_prefix(self, query: str, facet: Optional[str], limit: int = 10) -> List[ConceptModel]:
        """스포트라이트 전역 검색을 위한 접두사/키워드 검색."""
        ...
```

### ② `PerspectiveRepository` 인터페이스
```python
class PerspectiveRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_concept_id(self, concept_id: str) -> List[PerspectiveCaseModel]:
        """개념에 딸린 실무 사례 및 수치 사양(specifications) Eager Loading 조회."""
        stmt = (
            select(PerspectiveCaseModel)
            .options(selectinload(PerspectiveCaseModel.specifications))
            .where(PerspectiveCaseModel.concept_id == concept_id)
            .order_by(PerspectiveCaseModel.id.asc())
        )
        return (await self.db.execute(stmt)).scalars().all()
```

### ③ `CausalGraphRepository` 인터페이스
```python
class CausalGraphRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_relations_by_concept(self, concept_id: str) -> List[CausalEdgeModel]:
        """is_a, part_of, next_step, alternative_to 온톨로지 에지 조회."""
        stmt = (
            select(CausalEdgeModel)
            .where(CausalEdgeModel.source_concept_id == concept_id)
            .where(CausalEdgeModel.relation_type.in_(["is_a", "part_of", "next_step", "alternative_to"]))
        )
        return (await self.db.execute(stmt)).scalars().all()

    async def find_2hop_subgraph(self, concept_id: str, max_depth: int = 2) -> List[CausalEdgeModel]:
        """SQLite 재귀 CTE를 실행하여 1~2단계 연쇄 결함 및 보상 에지 탐색 (하드코딩 폴백 완전 배제)."""
        cte_query = """
        WITH RECURSIVE causal_path(source_concept_id, target_concept_id, relation_type, depth) AS (
            SELECT source_concept_id, target_concept_id, relation_type, 1
            FROM causal_edges
            WHERE source_concept_id = :concept_id
            UNION ALL
            SELECT e.source_concept_id, e.target_concept_id, e.relation_type, p.depth + 1
            FROM causal_edges e
            JOIN causal_path p ON e.source_concept_id = p.target_concept_id
            WHERE p.depth < :max_depth
        )
        SELECT * FROM causal_edges WHERE ...;
        """
        ...
```

### ④ `EvidenceRepository` 인터페이스
```python
class EvidenceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, evidence_id: str) -> Optional[EvidenceSourceModel]:
        """공인 출처 단건 상세 조회."""
        return await self.db.get(EvidenceSourceModel, evidence_id)

    async def get_by_concept_id(self, concept_id: str) -> List[EvidenceSourceModel]:
        """개념과 연계된 모든 공인 출처 목록 조회."""
        ...
```

---

## 1.4 Service 계층 설계 (Business Logic Layer)

비즈니스 로직과 보안 정책을 책임지며, **여러 Repository를 조율하고 비식별화(L3 마스킹)를 집행하여 최종 DTO로 변환**합니다.

### ① `DeidentificationService` (보안 비식별화 전담 엔진)
- **책임**: 요청자의 보안 권한 등급(`user_role`)과 각 수치 사양의 `is_confidential_l3` 플래그를 대조하여 수치 가림 처리.
- **비즈니스 규칙**:
  - `user_role`이 `chief_reviewer` 또는 `cleared_engineer`인 경우: 원본 수치(`val_numeric`) 노출 (`isMasked = False`).
  - 일반 `line_engineer` 또는 게스트인 경우: `is_confidential_l3 == True`인 모든 사양의 `value`를 `"[비식별화 보호 - L3 보안 인가 필요]"`로 치환 (`isMasked = True`).

### ② `WikiEntryService` (위키 본문 통합 조립 엔진)
- **책임**:
  1. `ConceptRepository.get_by_id(entry_id)` 호출
  2. `PerspectiveRepository.get_by_concept_id(entry_id)` 호출
  3. `CausalGraphRepository.get_relations_by_concept(entry_id)` 호출하여 relations DTO 번들 합성
  4. `DeidentificationService.mask_perspective_cases(perspectives, user_role)` 실행
  5. `ExplainerService.get_preloaded_explainers(entry_id)`를 실행하여 인라인 용어 요약 사전 적재
  6. 완전한 `WikiEntryDetailResponse` DTO로 조립하여 반환.

---

# 2. ⚖️ [Tab 2] 기술 대안 비교분석 계층 설계 (작성 예정)

*(사용자님과 다음 대화에서 Tab 2 Entity/DTO/Repository/Service 설계 후 통합 수록)*

---

# 3. ✍️ [Tab 3] 검토·승인 센터 계층 설계 (작성 예정)

*(사용자님과 다음 대화에서 Tab 3 Entity/DTO/Repository/Service 설계 후 통합 수록)*

---

# 4. 📑 [Tab 4] 외부 문헌·백서 조사 계층 설계 (작성 예정)

*(사용자님과 다음 대화에서 Tab 4 Entity/DTO/Repository/Service 설계 후 통합 수록)*

---

# 5. 🤖 [F-01] 플로팅 챗봇 & 공통 계층 설계 (작성 예정)

*(사용자님과 다음 대화에서 챗봇/공통 Entity/DTO/Repository/Service 설계 후 통합 수록)*
