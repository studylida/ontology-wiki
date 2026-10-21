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
- **책임**: 
  - 2번 섹션 "물리적 작동 원리"의 단계별(Step-by-Step) 공정 메커니즘과 KaTeX 수식 정규화 관리.
  - 공인 출처 증빙(`evidence_id`)을 물리 외래키로 연결하여 원리 지식의 신뢰성 보장.
  - **수식 결합 원리**: 프론트엔드에서는 `formula`를 KaTeX로 시각화하고, 백엔드 AI 에이전트는 본문 `content`와 `formula`에 기술된 물리 법칙(예: 하겐-푸아죄유 방정식 \(Q = \frac{\pi r^4 \Delta P}{8 \eta L}\))을 상충 관계(Trade-off) 추론의 근거(Grounding Anchor)로 활용.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 원리 단계 고유 ID |
| `concept_id` | `VARCHAR(64)` | `NOT NULL, FK(concepts.id ON DELETE CASCADE), INDEX` | 대상 개념 ID |
| `step_order` | `INTEGER` | `NOT NULL` | 작동 단계 순서 (1, 2, 3...) |
| `title` | `VARCHAR(128)` | `NOT NULL` | 단계 제목 (예: `일괄 솔더 리플로우 (Mass Reflow)`) |
| `content` | `TEXT` | `NOT NULL` | 물리 원리 설명 본문 |
| `formula` | `TEXT` | `NULLABLE` | KaTeX 수식 텍스트 (예: `Q = \frac{\pi r^4 \Delta P}{8 \eta L}`) |
| `evidence_id` | `VARCHAR(64)` | `NULLABLE, FK(evidence_sources.id ON DELETE SET NULL), INDEX` | **공인 출처 증빙 ID (`E-01`)** |
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
    evidenceId: Optional[str] = None     # 🌟 공인 출처 [E-01] 외래키 연결

# 2. 공정 한계 DTO
class LimitationItemDTO(BaseModel):
    title: str
    description: str
    evidenceId: Optional[str] = None

# 3-A. 내부 계층 전용 원시 사양 DTO (SecretStr 철통 보안 적용)
class RawPerspectiveSpecificationDTO(BaseModel):
    id: int
    caseId: str
    label: str
    valNumeric: SecretStr                # 🌟 Pydantic SecretStr: repr/str/로그 출력 시 '**********'로 자동 마스킹 (터미널/로그 평문 유출 0% 보장)
    unit: str
    criteria: Optional[str] = None
    role: str
    isConfidentialL3: bool
    evidenceId: Optional[str] = None

# 3-B. 외부 클라이언트 서빙용 사양 DTO (마스킹 적용 결과)
class SpecificationDTO(BaseModel):
    label: str
    value: str                           # 인가자: val_numeric.get_secret_value() ➔ "260" / 비인가자: "[비식별화 보호 - L3 보안 인가 필요]"
    unit: str
    criteria: Optional[str] = None
    role: str
    isMasked: bool                       # L3 마스킹 적용 여부
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

# 7. 좌측 카테고리 계층 트리 DTO (CategoryHierarchyController 서빙용)
class CategoryConceptNodeDTO(BaseModel):
    id: str
    title: str
    scaleLevel: int
    scaleName: str
    version: str
    status: str

class CategoryNodeDTO(BaseModel):
    categoryName: str
    concepts: List[CategoryConceptNodeDTO]

class CategoryTreeResponse(BaseModel):
    domainFacet: str
    categories: List[CategoryNodeDTO]

# 8. 공식 검증 출처 원문 드로어 DTO (EvidenceController 서빙용)
class EvidenceDetailDTO(BaseModel):
    id: str                              # "E-01"
    sourceName: str
    sourceType: str
    publisher: str
    publishedDate: Optional[str] = None
    quote: str
    sectionContext: Optional[str] = None
    relevanceScore: float
    externalUrl: str
    urlLabel: str
    credibilityTier: str

class EvidenceListResponse(BaseModel):
    conceptId: str
    evidences: List[EvidenceDetailDTO]

# 9. 인라인 용어 팝업 요약 DTO (ContextualExplainerController 서빙용)
class ContextualExplanationDTO(BaseModel):
    childId: str
    parentId: str
    childTitle: str
    parentTitle: str
    summary: str
    relationshipNarrative: str

# 10. 2-Hop 인과 서브그래프 네트워크 DTO (CausalGraphController 서빙용)
class SubgraphNodeDTO(BaseModel):
    id: str
    title: str
    scaleLevel: int
    nodeType: str                        # "concept" | "defect" | "parameter"

class SubgraphEdgeDTO(BaseModel):
    source: str
    target: str
    relationType: str                    # "causes_defect" | "compensates" | "alternative_to"
    polarity: str                        # "+" | "-" | "tradeoff"
    weight: float
    mechanismLabel: str
    compensatingParams: Optional[Dict[str, Any]] = None

class CausalSubgraphResponse(BaseModel):
    centerConceptId: str
    nodes: List[SubgraphNodeDTO]
    edges: List[SubgraphEdgeDTO]
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

    async def find_2hop_subgraph(self, concept_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """SQLite 재귀 CTE를 실행하여 1~2단계 연쇄 결함 및 보상 에지 탐색 (하드코딩 폴백 완전 배제).
        
        🌟 노드 타입 자동 태깅: relation_type에 따라 node_type을 즉석 분류하여 프론트엔드 추가 호출 0ms 보장.
        - causes_defect: 'defect' (결함 노드, 빨간색)
        - compensates: 'parameter' (설비 파라미터 노드, 노란색)
        - else: 'concept' (일반 공정/소자 개념 노드, 파란색)
        """
        cte_query = """
        WITH RECURSIVE causal_path(source_id, target_id, rel_type, depth) AS (
            SELECT source_concept_id, target_concept_id, relation_type, 1
            FROM causal_edges
            WHERE source_concept_id = :concept_id
            UNION ALL
            SELECT e.source_concept_id, e.target_concept_id, e.relation_type, p.depth + 1
            FROM causal_edges e
            JOIN causal_path p ON e.source_concept_id = p.target_id
            WHERE p.depth < :max_depth
        )
        SELECT 
            p.source_id, 
            p.target_id, 
            p.rel_type, 
            p.depth,
            e.polarity,
            e.weight,
            e.mechanism_label,
            e.compensating_params,
            CASE 
                WHEN p.rel_type = 'causes_defect' THEN 'defect'
                WHEN p.rel_type = 'compensates' THEN 'parameter'
                ELSE 'concept'
            END AS target_node_type
        FROM causal_path p
        JOIN causal_edges e ON p.source_id = e.source_concept_id AND p.target_id = e.target_concept_id AND p.rel_type = e.relation_type;
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
- **비즈니스 규칙 (SecretStr 기반 무누출 파이프라인)**:
  - 내부적으로 모든 수치는 `val_numeric: SecretStr`로 안전하게 래핑되어 있어 터미널/로그 평문 노출이 원천 차단됨.
  - `user_role`이 `chief_reviewer` 또는 `cleared_engineer`인 인가자인 경우:
    - 명시적으로 `spec.val_numeric.get_secret_value()`를 호출하여 실제 수치 평문(예: `"260"`)을 DTO `value`에 바인딩하고 `isMasked = False`로 설정.
  - 일반 `line_engineer` 또는 게스트인 비인가자인 경우:
    - `is_confidential_l3 == True`인 모든 사양의 DTO `value`를 `"[비식별화 보호 - L3 보안 인가 필요]"`로 치환하고 `isMasked = True` 플래그를 설정. (절대 `get_secret_value()`를 호출하지 않음)

### ② `WikiEntryService` (위키 본문 통합 조립 엔진)
- **책임**:
  1. `entry_id == 'home'` 또는 미지정 시:
     - 온톨로지 지식 탐색 가이드, 4대 업무 분야 바로가기, L3 보안 규정 안내를 담은 **가상 웰컴 홈 엔트리 DTO**를 즉시 반환.
  2. 일반 개념 상세 조회 시:
     - `ConceptRepository.get_by_id(entry_id)` 호출
     - `PerspectiveRepository.get_by_concept_id(entry_id)` 호출
     - `CausalGraphRepository.get_relations_by_concept(entry_id)` 호출하여 relations DTO 번들 합성
     - `DeidentificationService.mask_perspective_cases(perspectives, user_role)` 실행
     - **3단계 팝업 1단계(0ms) 사전 적재**: `relations`에 포함된 타깃 개념들의 `summary`를 메모리/캐시에서 긁어와 `preloadedExplainers: Dict[str, str]` 맵을 즉시 조립 (마우스 호버 시 0ms 즉시 노출). 만약 사전 적재 맵에 없는 단어에 호버할 때만 프론트가 2단계 `ContextualExplainerController` 호출.
     - 완전한 `WikiEntryDetailResponse` DTO로 조립하여 반환.

### ③ `NavigationService` (좌측 카테고리 트리 서빙 엔진)
- **책임**:
  - `domainFacet` 파라미터가 누락된 경우 기본값으로 메인 도메인인 **`unit_process` (단위 공정)** 트리를 자동 폴백하여 서빙.
  - `ConceptRepository.get_by_facet(facet)` 호출 결과를 공정 분류(`process_category`) 및 스케일 레벨(`scale_level`) 순으로 그룹화하여 `CategoryTreeResponse`로 합성.

---

# 2. ⚖️ [Tab 2] 기술 대안 비교분석 (Perspective Studio) 계층 설계

## 2.1 물리 Entity 스키마 설계 (Physical Database Schema)

기존의 `snapshots`, `context_params` 등 거대 JSON 덤프와 `val_a`, `val_b` 화면 중심의 비정규화 컬럼을 전면 폐기하고, **세션 ➔ 프로젝트 폴더 ➔ 평가 축 ➔ 격자 셀 ➔ 튜닝 레시피로 이어지는 5대 정규화 물리 테이블로 재구축**합니다.

```
┌──────────────────────────────┐
│  comparison_folders (폴더)   │
├──────────────────────────────┤
│ PK id, user_id, name         │
└──────────────┬───────────────┘
               │ 1:N
               ▼
┌────────────────────────────────────────────────────────┐
│              comparison_sessions (세션 마스터)         │
├────────────────────────────────────────────────────────┤
│ PK id, user_id, title, query, target_a_id, target_b_id │
│    is_pinned, FK folder_id, ai_summary, created_at     │
└──────────────┬──────────────────────────┬──────────────┘
               │ 1:N                      │ 1:N
               ▼                          ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐
│  comparison_axes (평가 축)   │ │  comparison_tunings (상담)   │
├──────────────────────────────┤ ├──────────────────────────────┤
│ PK id                        │ │ PK id                        │
│ FK session_id                │ │ FK session_id                │
│    axis_name, category       │ │    constraint_query          │
│    display_order, is_custom  │ │    tradeoff_analysis         │
└──────────────┬───────────────┘ └──────────────┬───────────────┘
               │ 1:N                            │ 1:N
               ▼                                ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐
│  comparison_cells (격자 셀)  │ │  comparison_tuning_recipes   │
│  (★ 3정규형 독립 셀 보존)    │ │  (★ 보상 레시피 정규화 행)   │
├──────────────────────────────┤ ├──────────────────────────────┤
│ PK id                        │ │ PK id                        │
│ FK axis_id                   │ │ FK tuning_id                 │
│ FK target_concept_id (대안)  │ │    plan_type (생산성/결함)   │
│    target_role (target_a/b)  │ │    parameter_name (파라미터) │
│    val_text (수치/텍스트)    │ │    recommended_value (추천값) │
│    unit (물리 단위)          │ │    unit (단위)               │
│    is_knowledge_gap (갭 여부)│ │    expected_tradeoff(페널티) │
│ FK evidence_id (공인 출처)   │ └──────────────────────────────┘
└──────────────────────────────┘
```

---

### [테이블 1] `comparison_folders` (프로젝트 폴더 마스터 테이블)
- **테이블명**: `comparison_folders`
- **책임**: 엔지니어링 세션을 프로젝트/제품군별로 정리하는 폴더링 물리 엔티티.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | 폴더 고유 ID (예: `fld-hbm4-pkg`) |
| `user_id` | `VARCHAR(64)` | `NOT NULL, INDEX` | 폴더 소유자 사번/엔지니어 ID |
| `name` | `VARCHAR(128)` | `NOT NULL` | 폴더명 (예: `HBM4 패키징 선행 연구`) |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 생성 일시 |

---

### [테이블 2] `comparison_sessions` (비교 연구 자산 세션 마스터)
- **테이블명**: `comparison_sessions`
- **책임**: 엔지니어가 수행한 비교 분석 작업 공간(Workspace)의 루트 엔티티(Aggregate Root).
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | 세션 고유 식별자 (예: `csess-20261020-01`) |
| `user_id` | `VARCHAR(64)` | `NOT NULL, INDEX` | 작성자 사번/엔지니어 ID |
| `title` | `VARCHAR(256)` | `NOT NULL` | 세션 제목 (예: `HBM3E 16단 적층 열방열 대안 비교`) |
| `query` | `TEXT` | `NOT NULL` | 엔지니어의 최초 자연어 고민 문장 |
| `target_a_id` | `VARCHAR(64)` | `NOT NULL, FK(concepts.id), INDEX` | 비교 대상 A 개념 ID (예: `concept-mrmuf`) |
| `target_b_id` | `VARCHAR(64)` | `NOT NULL, FK(concepts.id), INDEX` | 비교 대상 B 개념 ID (예: `concept-tcncf`) |
| `is_pinned` | `BOOLEAN` | `DEFAULT FALSE, NOT NULL` | 상단 즐겨찾기 고정 여부 |
| `folder_id` | `VARCHAR(64)` | `NULLABLE, FK(comparison_folders.id ON DELETE SET NULL), INDEX` | 소속 프로젝트 폴더 ID |
| `ai_summary` | `TEXT` | `NULLABLE` | 두 대안에 대한 AI 종합 인과 코멘트 |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 생성 일시 |
| `updated_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 수정 일시 |

> **🚨 개편 핵심**: 기존의 `snapshots`, `context_params` JSON 덤프 컬럼을 영구 삭제함.

---

### [테이블 3] `comparison_axes` (평가 축 척도 마스터)
- **테이블명**: `comparison_axes`
- **책임**: 두 대안을 평가하는 세로 행(Row) 기준(열저항, TAT, CAPEX 등) 정규화 관리 및 Delta 신규 축 추가 지원.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 축 고유 식별자 |
| `session_id` | `VARCHAR(64)` | `NOT NULL, FK(comparison_sessions.id ON DELETE CASCADE), INDEX` | 소속 세션 ID |
| `axis_name` | `VARCHAR(128)` | `NOT NULL` | 평가 축 명칭 (예: `열저항 (Thermal Resistance)`) |
| `category` | `VARCHAR(64)` | `NOT NULL` | 축 분류 (`물성 및 열특성`, `공정 결함 리스크`, `팹 양산성 & CAPEX`) |
| `display_order` | `INTEGER` | `NOT NULL` | 테이블 행 정렬 순서 |
| `is_custom` | `BOOLEAN` | `DEFAULT FALSE, NOT NULL` | 엔지니어가 `POST /axes`로 즉석 추가한 사용자 정의 축 여부 |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 생성 일시 |

---

### [테이블 4] `comparison_cells` (대안별 평가 격자 셀 정규화 테이블)
- **테이블명**: `comparison_cells`
- **책임**: 
  - 특정 평가 축(`axis_id`)에서 특정 대상(`target_concept_id`)이 갖는 실제 값, 단위, 지식 갭 상태, 공인 출처 증빙을 1:1로 물리 보존.
  - `val_a`, `val_b` 안티패턴을 완전히 폐기하고, 각 대안의 독립적인 출처(`evidence_id`)와 지식 갭(`is_knowledge_gap`)을 개별 행으로 엄격 격리.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 셀 고유 식별자 |
| `axis_id` | `INTEGER` | `NOT NULL, FK(comparison_axes.id ON DELETE CASCADE), INDEX` | 소속된 평가 축 ID |
| `target_concept_id`| `VARCHAR(64)` | `NOT NULL, FK(concepts.id), INDEX` | **평가 대상 개념 ID (MR-MUF, TC-NCF 등)** |
| `target_role` | `VARCHAR(16)` | `NOT NULL` | 대안 역할 (`target_a` 또는 `target_b`) |
| `val_text` | `VARCHAR(128)` | `NOT NULL` | 평가 수치/텍스트 (예: `"0.42"`, `"양호"`, `"미세 보이드 위험"`) |
| `unit` | `VARCHAR(32)` | `NULLABLE` | 물리 단위 (예: `"K/W"`, `"초"`, `"%"` 등) |
| `is_knowledge_gap` | `BOOLEAN` | `DEFAULT FALSE, NOT NULL` | 사내 공인 실측치 부재(지식 갭) 여부 |
| `evidence_id` | `VARCHAR(64)` | `NULLABLE, FK(evidence_sources.id ON DELETE SET NULL), INDEX` | 공인 출처 증빙 ID (`E-01`) |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 생성 일시 |

---

### [테이블 5] `comparison_tunings` (AI 파라미터 튜닝 상담 마스터)
- **테이블명**: `comparison_tunings`
- **책임**: 엔지니어가 입력한 설비 제약 조건과 AI의 종합 트레이드오프 분석 코멘트 이력 보존.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 튜닝 상담 고유 식별자 |
| `session_id` | `VARCHAR(64)` | `NOT NULL, FK(comparison_sessions.id ON DELETE CASCADE), INDEX` | 소속 세션 ID |
| `constraint_query` | `TEXT` | `NOT NULL` | 엔지니어가 입력한 설비 제약 (예: `"가압력 150N 상한"`) |
| `tradeoff_analysis`| `TEXT` | `NOT NULL` | AI 종합 트레이드오프 및 결함 리스크 분석 해설 |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 생성 일시 |

---

### [테이블 6] `comparison_tuning_recipes` (추천 파라미터 보상 레시피 정규화 테이블)
- **테이블명**: `comparison_tuning_recipes`
- **책임**: AI가 추천한 보상 레시피(파라미터명, 추천값, 단위, 페널티)를 JSON 덤프 없이 정규화 행(Row)으로 관리하여 사내 팹 통계 쿼리 지원.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 레시피 항목 고유 식별자 |
| `tuning_id` | `INTEGER` | `NOT NULL, FK(comparison_tunings.id ON DELETE CASCADE), INDEX` | 소속 튜닝 상담 ID |
| `plan_type` | `VARCHAR(16)` | `NOT NULL` | 플랜 유형 (`plan_a`: 생산성 우선, `plan_b`: 결함 방지 우선) |
| `parameter_name` | `VARCHAR(128)` | `NOT NULL` | 보상 파라미터명 (예: `초음파 인가 시간`, `몰딩 온도`) |
| `recommended_value`| `VARCHAR(64)` | `NOT NULL` | 추천 수치 (예: `"240ms"`, `"175℃"`) |
| `unit` | `VARCHAR(32)` | `NOT NULL` | 물리 단위 (`"ms"`, `"℃"`) |
| `expected_tradeoff`| `VARCHAR(256)` | `NOT NULL` | 예상 페널티 (예: `"택트타임 8.5% 증가"`) |

---

## 2.2 계약 DTO 설계 (API Contract Schemas - 전수 19종 완비)

### ① 세션 및 폴더 관리 DTO
```python
# 1. 세션 생성 요청 DTO
class ComparisonSessionCreateRequest(BaseModel):
    query: str
    targetAId: str
    targetBId: str
    title: Optional[str] = None
    folderId: Optional[str] = None

# 2. 세션 메타 수정 요청 DTO
class ComparisonSessionUpdateRequest(BaseModel):
    title: Optional[str] = None
    isPinned: Optional[bool] = None
    folderId: Optional[str] = None

# 3. 폴더 DTO
class ComparisonFolderDTO(BaseModel):
    id: str
    name: str
    sessionCount: int = 0

# 4. 세션 목록 요약 DTO
class ComparisonSessionSummaryDTO(BaseModel):
    id: str
    title: str
    query: str
    targetA: ConceptSummaryDTO
    targetB: ConceptSummaryDTO
    isPinned: bool
    folderId: Optional[str] = None
    updatedAt: str

# 5. 세션 목록 전체 응답 DTO (페이징 + 폴더 트리 번들)
class ComparisonSessionListResponse(BaseModel):
    items: List[ComparisonSessionSummaryDTO]
    totalCount: int
    hasMore: bool
    folders: List[ComparisonFolderDTO] = []

# 6. 세션 상세 복원 응답 DTO
class ComparisonSessionDetailResponse(BaseModel):
    session: ComparisonSessionSummaryDTO
    matrix: Optional["ComparisonMatrixResponse"] = None
    tunings: List["TuningAdvisorResponse"] = []
```

### ② 대화형 질문 구체화 DTO (`POST /comparison/clarify`)
```python
# 7. 질문 구체화 요청 DTO
class ComparisonClarifyRequest(BaseModel):
    query: str
    baseConceptId: Optional[str] = None

# 8. 3대 공학 분기 카드 DTO
class BranchCardDTO(BaseModel):
    branchId: str
    title: str
    targetA: ConceptSummaryDTO
    targetB: ConceptSummaryDTO
    coreTradeoff: str
    recommendedAxes: List[str]

# 9. 질문 구체화 최종 응답 DTO
class ComparisonClarifyResponse(BaseModel):
    query: str
    branchCards: List[BranchCardDTO]
    inferredTargetA: Optional[str] = None
    inferredTargetB: Optional[str] = None
```

### ③ 매트릭스 & 평가 축 DTO (`POST /matrix`, `POST /axes`)
```python
# 10. 단일 평가 셀 DTO
class MatrixCellDTO(BaseModel):
    conceptId: str
    targetRole: str            # "target_a" | "target_b"
    value: str                 # "0.42"
    unit: Optional[str] = None # "K/W"
    isKnowledgeGap: bool       # True일 경우 화면에 [미실측 지식 갭] 뱃지 표출
    evidenceId: Optional[str] = None

# 11. 매트릭스 단일 평가 행 DTO (가로 대조표 형태)
class MatrixRowDTO(BaseModel):
    axisId: int
    axisName: str              # "열저항 (Thermal Resistance)"
    category: str              # "물성 및 열특성"
    targetA: MatrixCellDTO     # 대상 A의 셀 데이터
    targetB: MatrixCellDTO     # 대상 B의 셀 데이터
    isCustom: bool = False

# 12. 지식 갭 발생 시 검토 센터 발행 연동 DTO (보안 마스킹 적용)
class GovernanceProposalDTO(BaseModel):
    proposalId: str
    targetConceptId: str
    targetConceptTitle: str
    axisName: str                      # 지식 갭이 발생한 축명
    gapType: str                       # "missing_measurement" | "data_conflict"
    inferredValue: str                 # 🌟 인가자: "0.42" / 비인가자: "[비식별화 보호 - L3 보안 인가 필요]"
    isMasked: bool                     # 🌟 L3 마스킹 여부 플래그
    unit: Optional[str] = None
    reasonNarrative: str
    sourceSessionId: str               # 발의 근거가 된 비교 세션 ID (데이터 계보 보존)

# 13. 매트릭스 전체 완성 응답 DTO
class ComparisonMatrixResponse(BaseModel):
    sessionId: str
    targetA: ConceptSummaryDTO
    targetB: ConceptSummaryDTO
    rows: List[MatrixRowDTO]
    overallComment: Optional[str] = None
    governanceProposal: Optional[GovernanceProposalDTO] = None

# 14. 평가 축 즉석 추가 요청 DTO
class ComparisonAxisCreateRequest(BaseModel):
    axisName: str
    category: str

# 15. 평가 축 즉석 추가 단일 행 Delta 응답 DTO (POST /axes - 1초 미만 응답)
class ComparisonAxisRowResponse(BaseModel):
    sessionId: str
    row: MatrixRowDTO
```

### ④ 파라미터 튜닝 상담 DTO (`POST /tune-advisor`)
```python
# 16. 파라미터 튜닝 상담 요청 DTO
class TuningAdvisorRequest(BaseModel):
    constraintQuery: str       # "우리 라인은 가압력을 150N 이상 못 줌"

# 17. 추천 보상 레시피 항목 DTO
class TuningRecipeItemDTO(BaseModel):
    parameterName: str
    recommendedValue: str
    unit: str
    expectedTradeoff: str

# 18. 추천 플랜 DTO (생산성안 / 결함방지안)
class TuningPlanDTO(BaseModel):
    planType: str              # "plan_a" | "plan_b"
    planTitle: str             # "생산성(TAT) 우선 최적화안"
    recipes: List[TuningRecipeItemDTO]

# 19. 파라미터 튜닝 상담 최종 응답 DTO
class TuningAdvisorResponse(BaseModel):
    tuningId: int
    constraintQuery: str
    tradeoffAnalysis: str
    plans: List[TuningPlanDTO]
```

---

## 2.3 다형성 거버넌스 연계 규격 (Tab 2 ➔ Tab 3 연동)

검토의 대상이 **문서 본문(위키 글/수치)**뿐만 아니라 **도메인 구조(인과 에지 연결, 신규 개념 등록)**까지 확장되도록 다형성 DTO를 규정합니다:

```python
class ReviewTargetScope(str, Enum):
    CONCEPT_CONTENT   = "concept_content"   # ① 위키 본문 및 수치 수정 (문서 레벨)
    NEW_CONCEPT       = "new_concept"       # ② 사내 온톨로지 신규 개념 등록 (도메인 레벨)
    CAUSAL_RELATION   = "causal_relation"   # ③ 두 개념 간 인과 에지 신설/수정 (관계망 레벨)
    TAXONOMY_RECLASS  = "taxonomy_reclass"  # ④ 스케일/분류 체계 변경 (분류 레벨)

class ReviewTicketCreateRequest(BaseModel):
    targetScope: ReviewTargetScope          # 🌟 검토 대상 스코프 지정
    title: str                              # "[비교분석 도출] MR-MUF 16단 적층 계면 전단 응력 수치 보완"
    reason: str                             # 발의 사유
    originType: str                         # "comparison_gap"
    sourceSessionId: Optional[str] = None   # "csess-20261020-01" (영구 보존)
    
    # 문서 레벨 제안 시 바인딩
    conceptId: Optional[str] = None
    workingDraft: Optional[str] = None      # 🌟 단일 작업 초안 버퍼로 직결
    
    # 도메인 관계망/신규 개념 제안 시 바인딩
    relationData: Optional[Dict[str, Any]] = None
    newConceptData: Optional[Dict[str, Any]] = None
```

---

## 2.4 Repository 계층 설계 (Data Access Layer - 4대 레포지토리 전수)

### ① `ComparisonSessionRepository`
```python
class ComparisonSessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, session: ComparisonSessionModel) -> ComparisonSessionModel:
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_by_id(self, session_id: str) -> Optional[ComparisonSessionModel]:
        """대상 A, B 개념 메타 Eager Loading."""
        stmt = (
            select(ComparisonSessionModel)
            .options(
                selectinload(ComparisonSessionModel.target_a),
                selectinload(ComparisonSessionModel.target_b)
            )
            .where(ComparisonSessionModel.id == session_id)
        )
        return (await self.db.execute(stmt)).scalars().first()

    async def get_detail(self, session_id: str) -> Optional[ComparisonSessionModel]:
        """축, 셀, 튜닝 이력 전수 Eager Loading."""
        stmt = (
            select(ComparisonSessionModel)
            .options(
                selectinload(ComparisonSessionModel.axes).selectinload(ComparisonAxisModel.cells),
                selectinload(ComparisonSessionModel.tunings).selectinload(ComparisonTuningModel.recipes)
            )
            .where(ComparisonSessionModel.id == session_id)
        )
        return (await self.db.execute(stmt)).scalars().first()

    async def list_by_user(self, user_id: str, is_pinned: Optional[bool], folder_id: Optional[str], limit: int, offset: int) -> Tuple[List[ComparisonSessionModel], int]:
        stmt = select(ComparisonSessionModel).where(ComparisonSessionModel.user_id == user_id)
        if is_pinned is not None:
            stmt = stmt.where(ComparisonSessionModel.is_pinned == is_pinned)
        if folder_id:
            stmt = stmt.where(ComparisonSessionModel.folder_id == folder_id)
        
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await self.db.execute(count_stmt)).scalar() or 0
        
        stmt = stmt.order_by(ComparisonSessionModel.is_pinned.desc(), ComparisonSessionModel.created_at.desc()).limit(limit).offset(offset)
        items = (await self.db.execute(stmt)).scalars().all()
        return items, total_count

    async def update_metadata(self, session_id: str, title: Optional[str], is_pinned: Optional[bool], folder_id: Optional[str]) -> Optional[ComparisonSessionModel]:
        session = await self.get_by_id(session_id)
        if session:
            if title is not None: session.title = title
            if is_pinned is not None: session.is_pinned = is_pinned
            if folder_id is not None: session.folder_id = folder_id
            await self.db.commit()
            await self.db.refresh(session)
        return session

    async def delete_session(self, session_id: str) -> bool:
        session = await self.get_by_id(session_id)
        if session:
            await self.db.delete(session) # ON DELETE CASCADE로 축/셀/튜닝 일괄 정리
            await self.db.commit()
            return True
        return False
```

### ② `ComparisonFolderRepository`
```python
class ComparisonFolderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_folders(self, user_id: str) -> List[ComparisonFolderModel]:
        stmt = select(ComparisonFolderModel).where(ComparisonFolderModel.user_id == user_id).order_by(ComparisonFolderModel.name.asc())
        return (await self.db.execute(stmt)).scalars().all()

    async def create_folder(self, user_id: str, name: str) -> ComparisonFolderModel:
        folder = ComparisonFolderModel(id=f"fld-{uuid.uuid4().hex[:8]}", user_id=user_id, name=name)
        self.db.add(folder)
        await self.db.commit()
        await self.db.refresh(folder)
        return folder

    async def delete_folder(self, folder_id: str) -> bool:
        folder = await self.db.get(ComparisonFolderModel, folder_id)
        if folder:
            await self.db.delete(folder)
            await self.db.commit()
            return True
        return False
```

### ③ `ComparisonMatrixRepository`
```python
class ComparisonMatrixRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_axes_with_cells(self, session_id: str) -> List[ComparisonAxisModel]:
        stmt = (
            select(ComparisonAxisModel)
            .options(selectinload(ComparisonAxisModel.cells))
            .where(ComparisonAxisModel.session_id == session_id)
            .order_by(ComparisonAxisModel.display_order.asc())
        )
        return (await self.db.execute(stmt)).scalars().all()

    async def save_matrix_full(self, session_id: str, axes_with_cells: List[Tuple[ComparisonAxisModel, List[ComparisonCellModel]]]) -> None:
        for axis, cells in axes_with_cells:
            self.db.add(axis)
            await self.db.flush()
            for cell in cells:
                cell.axis_id = axis.id
                self.db.add(cell)
        await self.db.commit()

    async def add_single_axis_with_cells(self, axis: ComparisonAxisModel, cells: List[ComparisonCellModel]) -> ComparisonAxisModel:
        self.db.add(axis)
        await self.db.flush()
        for cell in cells:
            cell.axis_id = axis.id
            self.db.add(cell)
        await self.db.commit()
        await self.db.refresh(axis)
        return axis
```

### ④ `ComparisonTuningRepository`
```python
class ComparisonTuningRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tuning_with_recipes(self, tuning: ComparisonTuningModel, recipes: List[ComparisonTuningRecipeModel]) -> ComparisonTuningModel:
        self.db.add(tuning)
        await self.db.flush()
        for r in recipes:
            r.tuning_id = tuning.id
            self.db.add(r)
        await self.db.commit()
        await self.db.refresh(tuning)
        return tuning

    async def list_tunings_by_session(self, session_id: str) -> List[ComparisonTuningModel]:
        stmt = (
            select(ComparisonTuningModel)
            .options(selectinload(ComparisonTuningModel.recipes))
            .where(ComparisonTuningModel.session_id == session_id)
            .order_by(ComparisonTuningModel.created_at.desc())
        )
        return (await self.db.execute(stmt)).scalars().all()
```

---

## 2.5 Service 계층 설계 (Business Logic Layer - 7대 전문 Service 전수)

### ① `ComparisonSessionService` (세션 라이프사이클 총괄)
- **책임**: 세션 생성, 단건 상세 복원, 즐겨찾기(⭐ Pin) 토글, 폴더 이동, 세션 삭제, 페이징 목록 조율.

### ② `OntologyClarifierService` (🌟 전 도메인 공통 지능형 질문 구체화 및 온톨로지 추론 엔진)
- **책임**:
  - Tab 2에 국한되지 않고 Tab 4(문헌조사 스코프 도출)와 플로팅 챗봇(인과 추론 및 의도 라우팅)이 공유하는 공통 두뇌.
  - `clarify_comparison(query)`: 온톨로지 그래프 탐색 ➔ **3대 공학 분기 카드(`BranchCardDTO`) 및 추천 축 도출**.
  - `clarify_research_scope(query)`: 문헌 조사 3대 스코프 칩 도출.
  - `route_chatbot_intent(utterance, context)`: 챗봇 3단 라우터 질의 처리.
  - `recommend_concept_placement(title, summary)`: 신규 문서 발의 시 온톨로지 그래프를 스캔하여 **최적 패싯(`domainFacet`), 스케일(`scaleLevel`), 공정군(`processCategory`), 상위개념(`parentConceptId`) 원클릭 자동 추천** (`POST /api/v1/ontology/recommend-placement`).

### ③ `ComparisonMatrixService` (매트릭스 종합 오케스트레이터)
- **책임**:
  1. 두 대상 개념(`targetA`, `targetB`)의 엔티티와 물리 수치 사양(`perspective_specifications`) 대조.
  2. 사내 DB에 실측치가 없는 축인 경우 `is_knowledge_gap = True`로 설정.
  3. **`OntologyGapDetectorService` 호출**: 수치 모순(Conflict)이나 실측치 부재(Gap) 감지 시 `governanceProposal` 생성.
  4. 정규화된 `ComparisonAxisModel`과 `ComparisonCellModel`을 결합하여 가로 대조표 형태의 `ComparisonMatrixResponse` DTO로 합성.

### ④ `ComparisonAxisService` (신규 축 Delta 1초 미만 고속 추가 전담)
- **책임**:
  - `POST /axes` 호출 시 전체 매트릭스를 재계산하지 않고, 요청된 1개 축에 대해서만 물리 지표를 즉석 산출한 뒤 `ComparisonMatrixRepository.add_single_axis_with_cells()`로 단일 행 저장 및 **1초 미만 고속 Delta 응답(`ComparisonAxisRowResponse`) 반환**.

### ⑤ `ParameterAdvisorService` (AI 파라미터 튜닝 상담 엔진)
- **책임**: 엔지니어의 설비 제약 조건(`constraintQuery`) 수신 ➔ `advisor_agent` 호출 ➔ 물리 모델 기반 안전 마진 계산 ➔ 생산성안/결함방지안 2종 레시피 생성 및 DB 정규화 저장.

### ⑥ `OntologyGapDetectorService` (지식 갭 감지 및 보안 마스킹 전담)
- **책임**:
  - 매트릭스 계산 중 공인 실측치 부재(Gap)나 출처 간 수치 모순(Conflict) 감지.
  - **주체 개념 1:1 확정 바인딩 규칙**:
    - 대안 A의 셀(`cell_a`)에서 갭이 발생한 경우: `targetConceptId = session.target_a_id`, `targetConceptTitle = session.target_a_title`로 확정.
    - 대안 B의 셀(`cell_b`)에서 갭이 발생한 경우: `targetConceptId = session.target_b_id`, `targetConceptTitle = session.target_b_title`로 확정.
    - 에이전트가 복잡한 추론 없이 구멍 난 셀의 주체 개념을 100% 무결하게 티켓 발의 대상으로 지정하도록 규정.
  - **`DeidentificationService` 연계**: 요청자가 비인가자(`line_engineer`)일 경우 `inferredValue`를 `"[비식별화 보호 - L3 보안 인가 필요]"`로 치환하고 `isMasked=True` 설정.

### ⑦ `ComparisonExportService` (엔지니어링 리포트 내보내기 엔진)
- **책임**: 세션 마스터, 매트릭스 테이블, 지식 갭 경고, 튜닝 레시피, AI 인과 분석을 표준 엔지니어링 마크다운(Markdown) 보고서 문서로 렌더링하여 다운로드 서빙.

---

# 3. ✍️ [Tab 3] 검토·승인 및 지식 거버넌스 센터 계층 설계

## 3.1 물리 Entity 스키마 설계 (Physical Database Schema)

기존의 단일 텍스트 컬럼 덮어쓰기 및 JSON 컬럼 몰빵 구조를 전면 폐기하고, **검토 티켓 마스터 ➔ 지시문 대화 이력 ➔ 정합성 점검 리포트 ➔ WORM 불변 감사 로그로 이어지는 4대 정규화 물리 테이블로 재구축**합니다.

```
┌────────────────────────────────────────────────────────┐
│              review_tickets (검토 티켓 마스터)         │
├────────────────────────────────────────────────────────┤
│ PK id, target_scope (existing/new_concept/causal_edge) │
│    FK concept_id (NULLABLE), concept_title, title      │
│    review_type, author, department, status             │
│    current_version, target_version                     │
│    working_draft (★ 단일 작업 초안 버퍼)               │
│    presence_lock_holder, presence_lock_expires_at      │
│    ticket_version (낙관적 락), approved_at, approved_by│
└──────────────┬──────────────────────────┬──────────────┘
               │ 1:N                      │ 1:N
               ▼                          ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐
│ review_directives (지시 이력)│ │review_integrity_checks (점검)│
├──────────────────────────────┤ ├──────────────────────────────┤
│ PK id                        │ │ PK id                        │
│ FK ticket_id                 │ │ FK ticket_id                 │
│    step_order                │ │    evidence_match_rate       │
│    directive_text            │ │    has_ontology_conflict     │
│    target_layer (specs/prose)│ │    impact_scope_count        │
│    revised_draft             │ │    validation_details        │
│    override_reason           │ │    conflict_details (JSON)   │
│    created_at                │ │    status (PASS/WARN/FAIL)   │
└──────────────────────────────┘ └──────────────────────────────┘
                                          │ 1:N
                                          ▼
                               ┌────────────────────────────────┐
                               │     audit_logs (WORM 감사로그) │
                               ├────────────────────────────────┤
                               │ PK id                          │
                               │    audit_id                    │
                               │ FK ticket_id                   │
                               │    action_type (approve/reject)│
                               │    actor (JSON)                │
                               │    governance_snapshot (JSON)  │
                               │    previous_log_hash           │
                               │    entry_hash (SHA-256 Merkle) │
                               │    digital_signature (HMAC)    │
                               │    timestamp                   │
                               └────────────────────────────────┘
```

---

### [테이블 1] `review_tickets` (검토 티켓 물리 마스터 테이블)
- **테이블명**: `review_tickets`
- **책임**: 
  - 공용 위키 개정 발의 및 사내 신규 개념/인과 에지 발의의 생애주기를 관리하는 루트 엔티티(Aggregate Root).
  - **단일 작업 초안(`working_draft`) 버퍼 보존**: AI 지시문 수정본과 인간 직접 편집본을 이원화하지 않고 하나의 버퍼에 보존하여 초안 유실을 원천 차단.
  - **다형성 티켓 스코프(`target_scope`) 수용**: 기존 개념 수정(`existing_concept`), 신규 개념 등록(`new_concept`), 신규 인과 에지 제안(`causal_relation`) 3대 발의를 모두 수용.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | 티켓 고유 식별자 (예: `rev-20261020-a1b2`) |
| `target_scope` | `VARCHAR(32)` | `NOT NULL, DEFAULT 'existing_concept'` | 발의 스코프 (`existing_concept`, `new_concept`, `causal_relation`) |
| `concept_id` | `VARCHAR(64)` | `NULLABLE, FK(concepts.id ON DELETE SET NULL), INDEX` | 대상 개념 ID (신규 개념 등록 시 NULL 허용) |
| `concept_title` | `VARCHAR(128)` | `NOT NULL` | 대상 개념 명칭 (신규 개념 시 발의된 명칭) |
| `title` | `VARCHAR(256)` | `NOT NULL` | 검토 티켓 발의 제목 |
| `review_type` | `VARCHAR(32)` | `NOT NULL` | 검토 유형 (`파라미터 수정`, `오류 정정`, `신규 공정 편입`, `인과 에지 보완`) |
| `author` | `VARCHAR(64)` | `NOT NULL, INDEX` | 발의자 사번/엔지니어 ID |
| `department` | `VARCHAR(64)` | `NULLABLE` | 발의 부서 (예: `첨단패키징개발팀`) |
| `submitted_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP, INDEX` | 발의 일시 |
| `status` | `VARCHAR(16)` | `NOT NULL, DEFAULT 'pending', INDEX` | 상태 (`pending`, `approved`, `rejected`) |
| `origin_type` | `VARCHAR(32)` | `NULLABLE` | 발의 출처 (`manual_expert`, `comparison_gap`, `deep_research`) |
| `current_version` | `VARCHAR(16)` | `DEFAULT 'v1.2', NOT NULL` | 발의 시점 기준 버전 번호 |
| `target_version` | `VARCHAR(16)` | `DEFAULT 'v1.3', NULLABLE` | 승인 시 승계될 목표 버전 번호 |
| `current_content` | `TEXT` | `NOT NULL` | 발의 시점의 원본 스냅샷 텍스트 |
| `working_draft` | `TEXT` | `NOT NULL` | **단일 작업 초안 버퍼** (AI 지시/직접 편집이 누적되는 단일 원본) |
| `proposed_payload` | `JSON` | `NULLABLE` | 신규 개념/에지 발의 시 필요한 정규화 구조체 JSON |
| `presence_lock_holder`| `VARCHAR(64)` | `NULLABLE` | 현재 편집 락을 점유 중인 엔지니어 ID |
| `presence_lock_expires_at`| `DATETIME` | `NULLABLE` | 편집 락 만료 일시 (TTL 기준 자동 해제) |
| `ticket_version` | `INTEGER` | `DEFAULT 1, NOT NULL` | 낙관적 동시성 락을 위한 버전 번호 |
| `approved_at` | `DATETIME` | `NULLABLE` | 최종 승인 일시 |
| `approved_by` | `VARCHAR(64)` | `NULLABLE` | 최종 승인권자 ID (Chief Reviewer) |
| `reject_reason` | `TEXT` | `NULLABLE` | 반려 시 사유 전문 |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 티켓 생성 일시 |
| `updated_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 최종 수정 일시 |

---

### [테이블 2] `review_directives` (전문가 AI 지시문 대화 이력 테이블)
- **테이블명**: `review_directives`
- **책임**: 전문가가 하단 지시문 바에서 입력한 자연어 수정 지시와 AI 재작성 초안의 누적 변경 이력을 영구 보존.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 지시문 이력 고유 ID |
| `ticket_id` | `VARCHAR(64)` | `NOT NULL, FK(review_tickets.id ON DELETE CASCADE), INDEX` | 연계 검토 티켓 ID |
| `step_order` | `INTEGER` | `NOT NULL` | 지시문 수행 회차 (1, 2, 3...) |
| `directive_text`| `TEXT` | `NOT NULL` | 전문가가 입력한 자연어 지시문 |
| `target_layer` | `VARCHAR(32)` | `NOT NULL, DEFAULT 'hybrid'` | 수정 대상 레이어 (`specs`, `relations`, `prose`, `hybrid`) |
| `revised_draft` | `TEXT` | `NOT NULL` | 본 지시문 수행 후 재작성된 초안 결과 |
| `override_reason`| `TEXT` | `NULLABLE` | 출처 수치 변경 시 필수 입력된 사유 |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 지시문 처리 일시 |

---

### [테이블 3] `review_integrity_checks` (온톨로지 무결성 점검 이력 테이블)
- **테이블명**: `review_integrity_checks`
- **책임**: 
  - 지시문 반영 또는 직접 편집 저장 시마다 자동 산출되는 3대 무결성 지표의 이력을 정규화 저장.
  - 승인 집행 시 무결성 통과 여부를 검증하는 **승인 차단 게이트웨이(`ApprovalBlockerGate`)의 물리적 근거**.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 점검 이력 고유 ID |
| `ticket_id` | `VARCHAR(64)` | `NOT NULL, FK(review_tickets.id ON DELETE CASCADE), INDEX` | 연계 검토 티켓 ID |
| `evidence_match_rate` | `NUMERIC(3, 2)` | `NOT NULL, DEFAULT 1.00` | 공인 출처 불변 제약 준수율 (0.00 ~ 1.00) |
| `has_ontology_conflict`| `BOOLEAN` | `NOT NULL, DEFAULT FALSE` | 인과 모순 및 물리적 제약 충돌 여부 |
| `impact_scope_count` | `INTEGER` | `NOT NULL, DEFAULT 1` | 수정 시 영향받는 2-Hop 인과 연관 개념 수 |
| `validation_details` | `TEXT` | `NOT NULL` | 점검 요약 텍스트 |
| `conflict_details` | `JSON` | `DEFAULT '[]'` | 충돌 발생 시 상세 원인-결함 체인 목록 |
| `status` | `VARCHAR(16)` | `NOT NULL, DEFAULT 'PASS'` | 종합 점검 판정 (`PASS`, `WARN`, `FAIL`) |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 점검 일시 |

---

### [테이블 4] `audit_logs` (WORM 불변 머클 해시 감사 로그 테이블)
- **테이블명**: `audit_logs`
- **책임**: WORM(Write Once, Read Many) 원칙에 입각하여 승인 및 반려 시 머클 SHA-256 해시 체인과 HMAC 서명을 영구 기록.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 순차 물리 ID |
| `audit_id` | `VARCHAR(64)` | `NOT NULL, UNIQUE, INDEX` | 감사 로그 고유 식별자 (`aud-YYYYMMDDHHMMSS-...`) |
| `ticket_id` | `VARCHAR(64)` | `NOT NULL, INDEX` | 대상 검토 티켓 ID |
| `concept_id` | `VARCHAR(64)` | `NULLABLE, INDEX` | 대상 온톨로지 개념 ID |
| `action_type` | `VARCHAR(32)` | `NOT NULL` | 거버넌스 집행 유형 (`approve`, `reject`) |
| `actor` | `JSON` | `NOT NULL` | 집행자 정보 (`{ "userId": "...", "role": "chief_reviewer" }`) |
| `governance_snapshot` | `JSON` | `NOT NULL` | 승인 당시 적용 버전, 사유, 변경 초안 요약 스냅샷 |
| `previous_log_hash` | `VARCHAR(64)` | `NOT NULL` | 직전 감사 로그의 `entry_hash` (해시 체인 연결) |
| `entry_hash` | `VARCHAR(64)` | `NOT NULL` | 본 감사 로그의 SHA-256 머클 해시 |
| `digital_signature` | `TEXT` | `NULLABLE` | HMAC-SHA256 디지털 서명 |
| `timestamp` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP, INDEX` | 감사 로그 확정 일시 |

---

## 3.2 DTO 계약 스펙 설계 (Pydantic Data Transfer Objects - 8종 전수)

### ① 티켓 목록 & 페이징 DTO (`GET /review-tickets`)
```python
# 1. 티켓 목록 단건 요약 DTO
class ReviewTicketListItemDTO(BaseModel):
    id: str
    targetScope: str                   # "existing_concept" | "new_concept" | "causal_relation"
    conceptId: Optional[str] = None
    conceptTitle: str
    title: str
    reviewType: str
    author: str
    department: Optional[str] = None
    submittedAt: str
    status: str                        # "pending" | "approved" | "rejected"
    originType: Optional[str] = None
    currentVersion: str
    targetVersion: Optional[str] = None
    integrityStatus: str               # "PASS" | "WARN" | "FAIL"
    impactScopeCount: int

# 2. 상단 탭 숫자 뱃지 번들 DTO
class ReviewTabCountsDTO(BaseModel):
    pending: int
    approved: int
    rejected: int

# 3. 티켓 목록 페이징 종합 응답 DTO (ReviewTicketPageResponse)
class ReviewTicketPageResponse(BaseModel):
    items: List[ReviewTicketListItemDTO]
    totalCount: int
    hasMore: bool
    offset: int
    limit: int
    tabCounts: ReviewTabCountsDTO      # 상단 탭 [대기중(12)] [승인완료(38)] [반려됨(5)] 뱃지 번들

# 4. 티켓 신규 발행 요청 DTO (POST /review-tickets - 위키 모달 M-05, 비교분석 연동 및 신규 개념 발의)
class ReviewTicketCreateRequest(BaseModel):
    targetScope: str = "existing_concept" # "existing_concept" | "new_concept" | "causal_relation"
    conceptId: Optional[str] = None    # 기존 개념 수정 시 필수, 완전 신규 개념 등록 시 None 가능
    conceptTitle: Optional[str] = None # 신규 기술/개념명
    engName: Optional[str] = None      # 영문 명칭
    title: str                         # 발의 제목
    reviewType: str                    # "파라미터 수정", "오류 정정", "신규 개념 등록", "인과 에지 보완"
    author: str                        # 발의자 사번/ID
    department: Optional[str] = None
    originType: str = "manual_expert"  # "manual_expert" | "comparison_gap" | "deep_research"
    userNote: Optional[str] = None     # 엔지니어 제안 의견
    suggestedDraft: Optional[str] = None # 제안 초안 및 기술 개요 (Summary & Purpose)
    sourceSessionId: Optional[str] = None # 비교분석 세션 연계 시 세션 ID
    proposedPayload: Optional[Dict[str, Any]] = None # 구조화 페이로드

    # 🌟 온톨로지 트리 편입 위치 지정 필드 (targetScope == "new_concept" 또는 reviewType == "신규 개념 등록" 시 필수)
    domainFacet: Optional[str] = "unit_process" # "device" | "unit_process" | "fab" | "infra"
    processCategory: Optional[str] = "첨단 패키징" # 세부 공정군
    scaleLevel: Optional[int] = 3               # 온톨로지 5대 스케일 (1~5)
    scaleName: Optional[str] = "Scale 3: 단위 공정"
    parentConceptId: Optional[str] = None       # 상위 개념 ID (relations.is_a)
```

### ② 2-Pane 검토 상세 워크스페이스 DTO (`GET /review-tickets/{id}`, `POST /presence`)
```python
# 4. 정합성 점검 보고서 상세 DTO
class IntegrityReportDTO(BaseModel):
    evidenceMatchRate: float
    hasOntologyConflict: bool
    impactScopeCount: int
    validationDetails: str
    conflictDetails: List[Dict[str, Any]] = []
    status: str                        # "PASS" | "WARN" | "FAIL"

# 5. 지시문 대화 이력 항목 DTO
class DirectiveHistoryItemDTO(BaseModel):
    stepOrder: int
    directiveText: str
    targetLayer: str
    revisedDraft: str
    overrideReason: Optional[str] = None
    createdAt: str

# 6. 티켓 2-Pane 상세 종합 DTO (ReviewTicketDetailDTO)
class ReviewTicketDetailDTO(BaseModel):
    id: str
    targetScope: str
    conceptId: Optional[str] = None
    conceptTitle: str
    title: str
    reviewType: str
    author: str
    department: Optional[str] = None
    submittedAt: str
    status: str
    currentVersion: str
    targetVersion: Optional[str] = None
    currentContent: str                # 좌측 Pane: 원본 지식 본문
    workingDraft: str                  # 우측 Pane: 단일 작업 초안 (AI+인간 누적본)
    ticketVersion: int                 # 낙관적 동시성 락 버전 번호
    integrityReport: IntegrityReportDTO
    directiveHistory: List[DirectiveHistoryItemDTO]
    currentEditor: Optional[str] = None
    isLocked: bool = False             # 타 엔지니어 편집 락 점유 여부

# 7. Presence Lock 요청 및 응답 DTO
class PresenceLockRequest(BaseModel):
    userId: str
    action: str                        # "acquire" | "renew" | "release" | "status"
    ttlSeconds: int = 30

class PresenceLockResponse(BaseModel):
    acquired: bool
    holder: Optional[str] = None
    isLocked: bool
    message: str
```

### ③ 전문가 AI 보완 지시문 DTO (`POST /review-tickets/{id}/directive`)
```python
# 8. AI 지시문 요청 DTO
class DirectiveRequest(BaseModel):
    directiveText: str                 # "가압력 150N 상한선에 따른 보상 파라미터 언급 추가해줘"
    overrideReason: Optional[str] = None # 실측치 상충 시 필수 입력 사유

# 9. AI 지시문 응답 DTO
class DirectiveResponse(BaseModel):
    ticketId: str
    stepOrder: int
    workingDraft: str                  # 지시사항이 반영된 최신 단일 초안
    integrityReport: IntegrityReportDTO
    addedDirective: DirectiveHistoryItemDTO
```

### ④ 직접 편집 저장 & 가상 미리보기 DTO (`PUT /draft`, `GET /wiki-preview`)
```python
# 10. 섹션별 정규화 diff 패치 DTO
class SectionDiffPatchDTO(BaseModel):
    sectionKey: str                    # "principles" | "limitations" | "specifications" | "summary"
    targetId: Optional[int] = None     # 물리 테이블 PK (신규 항목 시 None)
    field: str                         # 수정할 컬럼명 ("description", "formula", "val_numeric")
    oldValue: Optional[str] = None
    newValue: str

# 11. 직접 편집 저장 요청 및 응답 DTO
class DraftSaveRequest(BaseModel):
    editedContent: str                 # 전체 마크다운 작업 초안
    ticketVersion: int                 # 낙관적 락 버전 번호
    patches: Optional[List[SectionDiffPatchDTO]] = None # 정규화 분해 반영용 섹션별 패치

class DraftSaveResponse(BaseModel):
    ticketId: str
    ticketVersion: int
    workingDraft: str
    integrityReport: IntegrityReportDTO
    updatedAt: str

# 12. 공용 위키 가상 렌더링 미리보기 응답 DTO (ReviewWikiPreviewResponse)
class WikiPreviewResponse(BaseModel):
    ticketId: str
    conceptId: Optional[str] = None
    targetVersion: str
    previewConcept: Dict[str, Any]      # 메모리 상에서 가상 병합된 완전한 위키 상세 DTO
    diffSummary: Dict[str, Any]         # 변경된 단락 개수 및 추가/수정 하이라이트 요약
```

### ⑤ 거버넌스 승인 및 반려 집행 DTO (`POST /approve`, `POST /reject`)
```python
# 13. 승인 집행 요청 DTO
class ReviewApproveRequest(BaseModel):
    approvedBy: str                    # 승인자 사번/ID (Chief Reviewer)
    overrideReason: Optional[str] = None # 무결성 경고 또는 사유 존재 시 최종 승인 사유

# 14. 반려 집행 요청 DTO
class ReviewRejectRequest(BaseModel):
    rejectedBy: str                    # 반려 검토관 ID
    rejectReason: str                  # 반려 사유 상세

# 15. 거버넌스 의사결정 집행 공통 응답 DTO (ReviewDecisionResponse)
class ReviewDecisionResponse(BaseModel):
    ticketId: str
    status: str                        # "approved" | "rejected"
    appliedVersion: Optional[str] = None # 승인된 새 버전 번호 (예: "v1.3")
    auditLogId: str                    # 생성된 머클 감사 로그 ID
    message: str
```

---

## 3.3 Repository 계층 설계 (Data Access Layer - 2개 Repository)

### ① `ReviewTicketRepository` 인터페이스
```python
class ReviewTicketRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_tickets(
        self, 
        status: Optional[str], 
        concept_id: Optional[str], 
        limit: int = 20, 
        offset: int = 0
    ) -> List[ReviewTicketModel]:
        """필터링 목록 조회 (기본값 status='pending')."""
        stmt = select(ReviewTicketModel)
        if status:
            stmt = stmt.where(ReviewTicketModel.status == status)
        if concept_id:
            stmt = stmt.where(ReviewTicketModel.concept_id == concept_id)
        stmt = stmt.order_by(ReviewTicketModel.submitted_at.desc()).limit(limit).offset(offset)
        return (await self.db.execute(stmt)).scalars().all()

    async def count_by_status(self) -> Dict[str, int]:
        """상단 탭 숫자 뱃지용 상태별 건수 단일 쿼리 집계."""
        stmt = select(ReviewTicketModel.status, func.count(ReviewTicketModel.id)).group_by(ReviewTicketModel.status)
        rows = (await self.db.execute(stmt)).all()
        counts = {"pending": 0, "approved": 0, "rejected": 0}
        for st, cnt in rows:
            if st in counts:
                counts[st] = cnt
        return counts

    async def get_by_id_with_relations(self, ticket_id: str) -> Optional[ReviewTicketModel]:
        """티켓 단건 조회 (directives 및 integrity_checks Eager Loading)."""
        stmt = (
            select(ReviewTicketModel)
            .options(
                selectinload(ReviewTicketModel.directives),
                selectinload(ReviewTicketModel.integrity_checks)
            )
            .where(ReviewTicketModel.id == ticket_id)
        )
        return (await self.db.execute(stmt)).scalars().first()

    async def update_draft_with_optimistic_lock(
        self, 
        ticket_id: str, 
        new_draft: str, 
        expected_version: int
    ) -> bool:
        """낙관적 동시성 락을 적용한 단일 작업 초안 갱신."""
        stmt = (
            update(ReviewTicketModel)
            .where(ReviewTicketModel.id == ticket_id)
            .where(ReviewTicketModel.ticket_version == expected_version)
            .values(
                working_draft=new_draft,
                ticket_version=expected_version + 1,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def create_ticket(self, ticket: ReviewTicketModel) -> ReviewTicketModel:
        """신규 검토 티켓 발행 저장 (기존 개념 개정, 신규 개념 편입, 인과 에지 보완)."""
        self.db.add(ticket)
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket
```

### ② `AuditLogRepository` 인터페이스
```python
class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest_entry_hash(self) -> str:
        """머클 해시 체인 연결을 위한 최신 감사 로그의 entry_hash 조회."""
        stmt = select(AuditLogModel.entry_hash).order_by(AuditLogModel.id.desc()).limit(1)
        latest_hash = (await self.db.execute(stmt)).scalar()
        return latest_hash if latest_hash else "0" * 64

    async def create_audit_entry(self, entry: AuditLogModel) -> AuditLogModel:
        """불변 WORM 감사 로그 레코드 영구 저장."""
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def list_by_ticket_id(self, ticket_id: str) -> List[AuditLogModel]:
        """티켓에 귀속된 감사 체인 이력 조회."""
        stmt = select(AuditLogModel).where(AuditLogModel.ticket_id == ticket_id).order_by(AuditLogModel.id.asc())
        return (await self.db.execute(stmt)).scalars().all()

    async def verify_chain_integrity(self, ticket_id: str) -> bool:
        """해당 티켓 감사 체인의 머클 해시 및 HMAC 위변조 여부 전수 검증."""
        logs = await self.list_by_ticket_id(ticket_id)
        prev_hash = "0" * 64
        for log in logs:
            if log.previous_log_hash != prev_hash:
                return False
            # entry_hash 재계산 및 디지털 서명 검증
            recalculated = hashlib.sha256(
                f"{log.previous_log_hash}|{log.audit_id}|{log.ticket_id}|{log.action_type}|{json.dumps(log.actor, sort_keys=True)}|{json.dumps(log.governance_snapshot, sort_keys=True)}|{log.timestamp.isoformat()}".encode('utf-8')
            ).hexdigest()
            if recalculated != log.entry_hash:
                return False
            prev_hash = log.entry_hash
        return True
```

---

## 3.4 Service 계층 설계 (Business Logic Layer - 5대 전문 Service 전수)

### ① `ReviewTicketService` (티켓 대기열 및 상세 오케스트레이터)
- **책임**:
  - `create_ticket(request)`: 
    - 위키 모달 `[M-05]` 또는 비교분석 지식 갭 배너에서 접수된 발의 수신.
    - `targetScope`에 따라 기존 개념(`existing_concept`)이면 `ConceptRepository.get_by_id`로 원본 스냅샷 취득, 신규 개념(`new_concept`)이면 404 없이 `proposed_payload` 구조체 보존.
    - 단일 작업 초안 `working_draft` 초기화, 3대 무결성 점검 기본값 세팅 후 `ReviewTicketRepository.create_ticket` 호출.
  - `get_ticket_list(status, concept_id, limit, offset)`: 기본값 `status="pending"`으로 대기열 서빙, `count_by_status()`를 병렬 호출하여 `tabCounts`를 번들 조립.
  - `get_ticket_detail(ticket_id)`: 원본 본문(`current_content`), 최신 단일 초안(`working_draft`), 3대 정합성 보고서, 지시문 대화 이력, 현재 동시 접속자 락 상태를 2-Pane DTO로 합성.

### ② `PresenceLockService` (비차단 분산 편집 락 전담 엔진 - 10분 상한 이중 타이머)
- **책임**:
  - `acquire_lock(ticket_id, user_id, ttl=30)`: 
    - Redis 또는 인메모리 락 매니저를 통해 점유자 확인. 미점유 시 획득 성공 및 최초 잠금 일시(`locked_at`) 기록.
    - 타인 점유 시 읽기 전용 상태 안내.
  - `renew_lock(ticket_id, user_id, ttl=30)`: 
    - **15초 주기 클라이언트 Heartbeat 갱신**: 점유 엔지니어의 브라우저가 15초마다 갱신 신호를 보내 30초 단기 유효시간을 연장.
    - **🌟 10분(600초) 절대 점유 상한선(Max Hold Timeout) 가드레일**:
      - `locked_at` 시점으로부터 누적 10분이 경과한 경우, 하트비트 신호가 오더라도 연장을 거부하고 락을 강제 만료시킴 ("최대 편집 시간 10분 초과").
  - `steal_lock(ticket_id, new_user_id)`:
    - 10분 이상 자리를 비우거나 점유 중인 티켓에 대해, 다른 검토관이 "편집권 강제 회수"를 요청했을 때 이전 점유자의 락을 강제 반납시키고 새 점유권을 인계.
  - `release_lock(ticket_id, user_id)`: 탭 퇴장 또는 승인/반려 시 안전하게 락 즉시 반납.

### ③ `ReviewDirectiveService` (전문가 AI 보완 지시문 실행 엔진)
- **책임**:
  - 엔지니어의 자연어 지시문 수신 ➔ **공통 게이트웨이 `call_agent(agent_type="directive", ...)` 호출**.
  - 30초 타임아웃 및 Graceful Fallback (타임아웃 발생 시 기존 초안 보존 및 재시도 안내).
  - 공인 온톨로지 에지(`CausalEdgeModel`) 탐색을 결합하여 상충 관계 및 보상 파라미터 백서 문체 합성.
  - 단일 작업 초안(`working_draft`)을 즉시 갱신하고, `review_directives` 테이블에 실행 이력 INSERT.
  - 3대 정합성 점검(출처 매칭률, 온톨로지 모순, 영향 범위)을 재수행하여 `review_integrity_checks` 테이블 갱신.

### ④ `ReviewDraftSaveService` (직접 편집 실시간 저장 & 출처 불변 가드레일)
- **책임**:
  - **`SourceImmutabilityValidator` (출처 삭제 방어 가드레일)**:
    - 직접 편집 초안 내에 원본 공인 출처 각주(`\[E-\d+\]`) 목록이 온전히 보존되어 있는지 정규식 전수 검사.
    - 사용자가 백스페이스로 실수 삭제한 경우, 누락된 출처 뱃지를 문장 끝에 자동으로 복원 주입하여 공인 출처 영구 소실을 원천 차단.
  - **낙관적 동시성 락(`ticket_version`) 검증**: 판본 충돌 발생 시 HTTP 409 Conflict 반환.
  - 단일 버퍼 `working_draft` 저장 및 갱신된 DTO 반환.

### ⑤ `ReviewWikiPreviewService` (승인 전 공용 위키 가상 미리보기 엔진)
- **책임**:
  - **Virtual Merge (메모리 상 가상 오버레이 병합)**:
    - Tab 1의 `WikiEntryService` 조립 로직을 재사용.
    - DB 원본 개념의 데이터(카테고리, 2-Hop 서브그래프, 연관 에지) 위에 현재 티켓의 최신 `working_draft`를 메모리 상에서 덮어씌움.
    - 원본 텍스트 대비 변경된 단락에 `<mark class="diff-added">` 하이라이트 클래스를 자동 바인딩하여 완전한 `WikiEntryDetailResponse` 규격으로 사전 렌더링 서빙.
  - 프로덕션 DB 오염 0% 보장.

### ⑥ `ReviewDecisionService` (거버넌스 승인 및 원자적 위키 반영 엔진)
- **책임**:
  - **1. 권한 검증**: 요청 헤더 `X-User-Role`이 `chief_reviewer`인지 엄격 검증 (일반 `line_engineer`는 HTTP 403 Forbidden 차단).
  - **2. `ApprovalBlockerGate` (승인 차단 게이트웨이)**:
    - 최신 정합성 점검 결과가 `status == 'FAIL'`이거나 인과 모순(`has_ontology_conflict == True`)이 존재하는 경우:
    - 사유(`overrideReason`)가 비어 있으면 **HTTP 422 Unprocessable Entity로 승인을 물리 차단**.
  - **3. 단일 원자적 DB 트랜잭션 (Atomic Decomposition & Polymorphic Apply)**:
    - `target_scope`에 따라 기존 개념 개정과 신규 개념 등록을 자동 분기하여 단일 트랜잭션 처리:
      - **분기 A [신규 개념 등록 승인 (`target_scope == 'new_concept'` 또는 `is_new == True`)]**:
        1. **온톨로지 편입 위치 바인딩**: 티켓 발의 시 지정된 메타데이터(`domain_facet`, `scale_level`, `process_category`, `scale_name`, `relations.is_a`)를 취득.
        2. **`concepts` 테이블 신규 행 INSERT**: 고유 ID `concept-xxx` 발급, 취득한 패싯/스케일 레벨에 배치, `version='v1.0'`, `status='adopted'`, `summary=working_draft`.
        3. **하위 인과 엔티티 연동**: 발급된 `concept_id`를 외래키로 바인딩하여 제안된 원리(`concept_principles`), 공정 한계(`concept_limitations`), 관점별 실무 사례(`perspectives`) 신규 INSERT.
        4. **온톨로지 인과 에지(`causal_edges`) 등록**: `parent_concept_id`와의 상위 계층 에지(`is_a`) 및 공정 전후 인과 관계 에지 자동 생성.
      - **분기 B [기존 개념 개정 승인 (`target_scope == 'existing_concept'`)]**:
        1. `concepts`: 세맨틱 버전 자동 승계 (일반 수정 ➔ `PATCH`, 공인 출처 폐기 ➔ `MINOR`), `summary` 갱신.
        2. `working_draft`의 섹션별 패치를 분해하여 하위 테이블 UPDATE/INSERT (`principles`, `limitations`, `specifications`).
  - **4. WORM 머클 감사 체인 확정**:
    - 직전 `entry_hash`를 조회하여 현재 승인 스냅샷과 결합한 새 SHA-256 해시를 생성하고 HMAC 전자 서명과 함께 `audit_logs`에 INSERT.
  - **5. 위키 캐시 즉시 무효화 (0ms 전사 공표)**:
    - 공통 모듈 `CacheOrchestrator.invalidate_concept_domain(concept_id)`를 호출하여 위키 상세, 서브그래프, 문맥 설명, 전역 검색 캐시를 0ms 일괄 소거.

---

# 4. 📑 [Tab 4] 외부 문헌·백서 조사 (Deep Research) 계층 설계

## 4.1 물리 Entity 스키마 설계 (Physical Database Schema)

기존의 `synthesis_report(JSON)`, `candidates(JSON)`, `evidence_feed(JSON)` 몰빵 방식을 전면 폐기하고, **연구 세션 마스터 ➔ 공인 증빙 피드 ➔ 심층 기술 분석 리포트 ➔ 온톨로지 편입 제안 후보로 이어지는 4대 정규화 물리 테이블로 재구축**합니다.

```
┌────────────────────────────────────────────────────────┐
│             research_sessions (연구 세션 마스터)       │
├────────────────────────────────────────────────────────┤
│ PK id (res-YYYYMMDD-...), user_id, search_topic        │
│    is_pinned (⭐ 즐겨찾기), target_concept_id (선택)    │
│    scope_filters (JSON), target_institutions (JSON)    │
│    created_at (★ 날짜별 4단 그룹화 기준), updated_at   │
└──────────────┬──────────────────────────┬──────────────┘
               │ 1:N                      │ 1:1
               ▼                          ▼
┌──────────────────────────────┐ ┌────────────────────────────────────────┐
│research_evidence_feeds (증빙)│ │   research_syntheses (심층 분석 리포트)│
├──────────────────────────────┤ ├────────────────────────────────────────┤
│ PK id (AUTOINCREMENT)        │ │ PK id (AUTOINCREMENT)                  │
│ FK session_id                │ │ FK session_id (UNIQUE)                 │
│    evidence_id (선택)        │ │    executive_summary (1. 총괄 요약)    │
│    source_name (논문/백서명) │ │    physical_mechanism (2. 물리 메커니즘)│
│    publisher (Intel, IEEE 등)│ │    academic_vs_industry (3. 마진대조)  │
│    published_date (발행일)   │ │    tradeoff_analysis (4. 트레이드오프) │
│    quote (핵심 원문 인용구)  │ │    actionable_recommendations (5. 권고)│
│    credibility_tier (Tier 1) │ │    citation_notes (6. 상세 각주 JSON)  │
│    external_url (PDF 링크)   │ │    created_at, updated_at              │
│ ★  is_selected (엔지니어선별)│ └────────────────────────────────────────┘
│ ★  promoted_evidence_id (승격)│
│    created_at                │
└──────────────────────────────┘
               │ 1:N
               ▼
┌────────────────────────────────────────────────────────┐
│       research_candidates (온톨로지 편입 제안 후보)    │
├────────────────────────────────────────────────────────┤
│ PK id (AUTOINCREMENT)                                  │
│ FK session_id                                          │
│    candidate_type (new_concept | property_patch)       │
│    target_concept_id (기존 개념 보완 시 대상 ID)        │
│    title (후보 제목)                                   │
│    rationale (제안 근거 및 백서 인용 요약)             │
│    proposed_payload (신규 개념 또는 수치 패치 JSON)    │
│ ★  exported_ticket_id (Tab 3 검토 센터 직결 외래키)     │
│ ★  status (draft ➔ exported ➔ adopted)                 │
│    created_at                                          │
└────────────────────────────────────────────────────────┘
```

---

### [테이블 1] `research_sessions` (연구 세션 마스터)
- **테이블명**: `research_sessions`
- **책임**: 연구 작업 공간 루트 엔티티(Aggregate Root). 엔지니어의 연구 주제, 타깃 개념, 선택 필터를 관리하고 날짜별 그룹화의 기준점 제공.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(64)` | `PRIMARY KEY` | 세션 고유 식별자 (`res-YYYYMMDD-UUID`) |
| `user_id` | `VARCHAR(64)` | `NOT NULL, INDEX` | 세션 소유자 사번/엔지니어 ID |
| `search_topic` | `VARCHAR(256)` | `NOT NULL` | 연구 테마/엔지니어링 질의 |
| `is_pinned` | `BOOLEAN` | `NOT NULL, DEFAULT FALSE, INDEX` | 즐겨찾기 (⭐ 사이드바 그룹 최상단 고정) |
| `target_concept_id` | `VARCHAR(64)` | `NULLABLE, FK(concepts.id ON DELETE SET NULL)` | 목적형 탐색 시 타깃 개념 ID |
| `scope_filters` | `JSON` | `DEFAULT '[]'` | 선택된 조사 스코프 칩 ID 리스트 |
| `target_institutions`| `JSON` | `DEFAULT '[]'` | 선택된 타깃 기관 리스트 (Intel, IEEE 등) |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP, INDEX` | **좌측 사이드바 날짜별 4단 그룹화 기준 일시** |
| `updated_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 세션 최종 수정 일시 |

---

### [테이블 2] `research_evidence_feeds` (공인 출처 증빙 피드 정규화 테이블)
- **테이블명**: `research_evidence_feeds`
- **책임**:
  - 수집된 논문/백서 원문 증빙 피드를 개별 행(Row) 단위로 정규화 보존.
  - **엔지니어 선별 상태(`is_selected`) 제어**: AI가 수집한 피드 중 엔지니어가 유효하다고 채택한 피드만 분석 및 편입에 활용.
  - **사내 공식 출처 승격 추적(`promoted_evidence_id`)**: 검토 센터를 거쳐 공용 위키로 편입될 시 사내 공식 출처(`evidence_sources`) ID 매핑.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 증빙 피드 고유 물리 ID |
| `session_id` | `VARCHAR(64)` | `NOT NULL, FK(research_sessions.id ON DELETE CASCADE), INDEX` | 연계 연구 세션 ID |
| `evidence_id` | `VARCHAR(64)` | `NULLABLE` | 기존 공인 출처 연계 시 출처 ID |
| `source_name` | `VARCHAR(256)` | `NOT NULL` | 공인 논문/백서 공식 명칭 |
| `publisher` | `VARCHAR(64)` | `NOT NULL, INDEX` | 발행처 (Intel, TSMC, IEEE, ECTC, SEMI 등) |
| `published_date` | `VARCHAR(32)` | `NULLABLE` | 발행 일자 (예: `2025.03`) |
| `quote` | `TEXT` | `NOT NULL` | 핵심 원문 인용구 전문 |
| `credibility_tier`| `VARCHAR(32)` | `NOT NULL, DEFAULT 'Tier 1'` | 신뢰도 등급 (`Tier 1` 공인 학회/제조사 백서) |
| `external_url` | `TEXT` | `NOT NULL` | 공식 원문 열람 / PDF 다운로드 링크 |
| `is_selected` | `BOOLEAN` | `NOT NULL, DEFAULT TRUE, INDEX` | **엔지니어 선별 상태 (체크박스 채택/제외 플래그)** |
| `promoted_evidence_id`| `VARCHAR(64)` | `NULLABLE, FK(evidence_sources.id ON DELETE SET NULL)` | **사내 공식 출처 승격 번호 (예: `E-05`)** |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 피드 수집 일시 |

---

### [테이블 3] `research_syntheses` (심층 기술 분석 리포트 정규화 테이블)
- **테이블명**: `research_syntheses`
- **책임**:
  - 수집된 복수 문헌을 AI 에이전트가 교차 분석하여 도출한 **심층 엔지니어링 테크니컬 화이트페이퍼 수준의 종합 분석 리포트**를 보존.
  - 6대 전문 섹션(총괄 요약, 물리 메커니즘, 공정 마진 대조표, 트레이드오프, 사내 팹 권고안, 상세 각주)을 온전히 저장.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 분석 리포트 고유 ID |
| `session_id` | `VARCHAR(64)` | `NOT NULL, UNIQUE, FK(research_sessions.id ON DELETE CASCADE)` | 연계 연구 세션 ID (1:1 관계) |
| `executive_summary` | `TEXT` | `NOT NULL` | 1. 총괄 요약 (배경, 병목, 글로벌 동향) |
| `physical_mechanism`| `TEXT` | `NOT NULL` | 2. 물리 메커니즘 심층 해설 (KaTeX 수식 포함) |
| `academic_vs_industry`| `JSON` | `NOT NULL` | 3. 학계 vs 제조사 공정 마진 대조 행 리스트 |
| `tradeoff_analysis` | `TEXT` | `NOT NULL` | 4. 핵심 엔지니어링 트레이드오프 및 병목 극복 대안 |
| `actionable_recommendations`| `TEXT`| `NOT NULL` | 5. 사내 팹 라인 적용 권고안 (단기/중기) |
| `citation_notes` | `JSON` | `NOT NULL` | 6. 인용 백서/논문 페이지 및 DOI 각주 리스트 |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 리포트 생성 일시 |
| `updated_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 리포트 갱신 일시 |

---

### [테이블 4] `research_candidates` (온톨로지 편입 제안 후보 정규화 테이블)
- **테이블명**: `research_candidates`
- **책임**:
  - 외부 문헌 조사 결과 중 사내 온톨로지에 공식 편입시킬 제안 후보의 생애주기 관리.
  - **조사실(Tab 4)과 검토센터(Tab 3)를 잇는 거버넌스 직결 브릿지**: 검토 티켓 ID(`exported_ticket_id`)를 외래키로 보존.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 편입 제안 후보 고유 ID |
| `session_id` | `VARCHAR(64)` | `NOT NULL, FK(research_sessions.id ON DELETE CASCADE), INDEX` | 연계 연구 세션 ID |
| `candidate_type` | `VARCHAR(32)` | `NOT NULL` | 후보 유형 (`new_concept` [신규 개념], `property_patch` [수치 보완]) |
| `target_concept_id`| `VARCHAR(64)` | `NULLABLE, FK(concepts.id ON DELETE SET NULL)` | 기존 개념 보정 시 대상 개념 ID |
| `title` | `VARCHAR(256)` | `NOT NULL` | 제안 후보 제목 (예: `TGV 미세 균열 방어 보상 레시피`) |
| `rationale` | `TEXT` | `NOT NULL` | 제안 근거 및 문헌 인용구 요약 |
| `proposed_payload` | `JSON` | `NOT NULL` | 신규 개념 DTO 또는 정규화 수치 패치 페이로드 |
| `exported_ticket_id`| `VARCHAR(64)` | `NULLABLE, FK(review_tickets.id ON DELETE SET NULL), INDEX` | **Tab 3 검토 센터로 발의된 거버넌스 티켓 ID** |
| `status` | `VARCHAR(16)` | `NOT NULL, DEFAULT 'draft'` | 발의 상태 (`draft` ➔ `exported` ➔ `adopted`) |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 후보 생성 일시 |

---

## 4.2 DTO 계약 스펙 설계 (Pydantic Data Transfer Objects - 9종 전수)

### ① 세션 목록 및 날짜별 4단 그룹 DTO (`GET /research/sessions`)
```python
# 1. 세션 단건 요약 DTO
class ResearchSessionListItemDTO(BaseModel):
    id: str
    searchTopic: str
    isPinned: bool
    createdAt: str
    feedCount: int
    candidateCount: int

# 2. 날짜별 4단 그룹 번들 DTO
class ResearchSessionGroupDTO(BaseModel):
    today: List[ResearchSessionListItemDTO]
    yesterday: List[ResearchSessionListItemDTO]
    thisWeek: List[ResearchSessionListItemDTO]
    older: List[ResearchSessionListItemDTO]

# 3. 세션 목록 종합 응답 DTO
class ResearchSessionListResponse(BaseModel):
    groups: ResearchSessionGroupDTO
    totalCount: int
```

### ② 대화형 조사 범위 구체화 DTO (`POST /research/clarify`)
```python
# 4. 조사 스코프 칩 DTO
class ResearchScopeChipDTO(BaseModel):
    chipId: str                        # "aspect-ratio-10"
    label: str                         # "10:1 고종횡비 공정 한계"
    category: str                      # "공정 조건" | "결함 메커니즘"

# 5. 조사 범위 구체화 요청 및 응답 DTO
class ResearchClarifyRequest(BaseModel):
    query: str                         # "유리기판 TGV 미세 균열 방어"
    targetConceptId: Optional[str] = None

class ResearchClarifyResponse(BaseModel):
    query: str
    recommendedScopes: List[ResearchScopeChipDTO]
    targetInstitutions: List[str]      # ["Intel", "TSMC", "IEEE", "ECTC", "SEMI"]
    refinedKeywords: List[str]         # ["TGV laser induced deep etching", "micro-crack mitigation"]
```

### ③ 공인 원문 증빙 피드 수집 및 선별 DTO (`POST /discover`, `PATCH /feeds/{id}`)
```python
# 6. 증빙 피드 단건 DTO
class EvidenceFeedItemDTO(BaseModel):
    id: int
    sourceName: str
    publisher: str
    publishedDate: Optional[str] = None
    quote: str
    credibilityTier: str               # "Tier 1", "Tier 2"
    externalUrl: str
    isSelected: bool = True            # 엔지니어 선별 상태
    promotedEvidenceId: Optional[str] = None

class ResearchDiscoverRequest(BaseModel):
    scopeFilterIds: List[str]
    targetInstitutions: List[str]

class ResearchDiscoverResponse(BaseModel):
    sessionId: str
    totalDiscovered: int
    evidenceFeed: List[EvidenceFeedItemDTO]

class FeedSelectionUpdateRequest(BaseModel):
    isSelected: bool                   # 엔지니어의 체크박스 토글 요청
```

### ④ 심층 기술 분석 종합 리포트 및 편입 후보 DTO (`POST /synthesize`)
```python
# 7. 학계 vs 제조사 공정 마진 대조 단일 행 DTO
class MarginComparisonRowDTO(BaseModel):
    specName: str                      # "비아 종횡비 (Aspect Ratio)"
    academicSpec: str                  # "20 : 1 (직경 10µm / 두께 200µm)"
    industryMargin: str                # "10 : 1 (직경 50µm / 두께 500µm)"
    commentary: str                    # "양산 도금 필링 시 보이드 방어를 위한 보수적 타협 해설"

# 8. 인용 문헌 상세 각주 DTO
class SynthesisCitationNoteDTO(BaseModel):
    citationTag: str                   # "[E-01]"
    sourceName: str                    # "Intel Glass Core Architecture Whitepaper"
    sectionOrPage: str                 # "pp. 12-18, Section 4.2"
    credibilityTier: str
    url: str

# 9. 심층 기술 분석 리포트 DTO (SynthesisReportDTO - 6대 전문 섹션 완비)
class SynthesisReportDTO(BaseModel):
    executiveSummary: str              # 1. 총괄 요약
    physicalMechanism: str             # 2. 물리 메커니즘 심층 해설 (KaTeX 수식 포함)
    academicVsIndustry: List[MarginComparisonRowDTO] # 3. 공정 마진 대조표
    tradeoffAnalysis: str              # 4. 엔지니어링 트레이드오프 및 병목 극복 대안
    actionableRecommendations: str     # 5. 사내 팹 라인 적용 권고안 (단기/중기)
    citationNotes: List[SynthesisCitationNoteDTO]   # 6. 공인 출처 상세 각주

# 10. 온톨로지 편입 제안 후보 DTO
class ResearchCandidateItemDTO(BaseModel):
    candidateId: int
    candidateType: str                 # "new_concept" | "property_patch"
    targetConceptId: Optional[str] = None
    title: str
    rationale: str
    proposedPayload: Dict[str, Any]
    status: str                        # "draft" | "exported" | "adopted"
    exportedTicketId: Optional[str] = None

# 11. 결과실 2-Column Split View 종합 응답 DTO (ResearchSessionDetailResponse)
class ResearchSessionDetailResponse(BaseModel):
    sessionId: str
    searchTopic: str
    isPinned: bool
    createdAt: str
    evidenceFeeds: List[EvidenceFeedItemDTO]   # 좌측 Pane: 공인 증빙 피드 (체크박스 제어)
    synthesisReport: Optional[SynthesisReportDTO] # 우측 Pane 상단: 심층 기술 분석 리포트
    candidates: List[ResearchCandidateItemDTO] # 우측 Pane 하단: 온톨로지 편입 후보 카드 목록
```

---

## 4.3 Repository 계층 설계 (Data Access Layer - 4개 Repository)

### ① `ResearchSessionRepository` 인터페이스
```python
class ResearchSessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_user(self, user_id: str) -> List[ResearchSessionModel]:
        """사용자 세션 목록 최신순 조회."""
        stmt = (
            select(ResearchSessionModel)
            .where(ResearchSessionModel.user_id == user_id)
            .order_by(ResearchSessionModel.created_at.desc())
        )
        return (await self.db.execute(stmt)).scalars().all()

    async def get_by_id_with_relations(self, session_id: str) -> Optional[ResearchSessionModel]:
        """세션 2-Column 상세 복원 (feeds, synthesis, candidates 1회 Eager Loading)."""
        stmt = (
            select(ResearchSessionModel)
            .options(
                selectinload(ResearchSessionModel.evidence_feeds),
                selectinload(ResearchSessionModel.synthesis),
                selectinload(ResearchSessionModel.candidates)
            )
            .where(ResearchSessionModel.id == session_id)
        )
        return (await self.db.execute(stmt)).scalars().first()

    async def create_session(self, session: ResearchSessionModel) -> ResearchSessionModel:
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def update_meta(self, session_id: str, is_pinned: Optional[bool], search_topic: Optional[str]) -> bool:
        values = {}
        if is_pinned is not None:
            values["is_pinned"] = is_pinned
        if search_topic:
            values["search_topic"] = search_topic
        values["updated_at"] = datetime.utcnow()
        stmt = update(ResearchSessionModel).where(ResearchSessionModel.id == session_id).values(**values)
        res = await self.db.execute(stmt)
        await self.db.commit()
        return res.rowcount > 0

    async def delete_session_cascade(self, session_id: str) -> bool:
        stmt = delete(ResearchSessionModel).where(ResearchSessionModel.id == session_id)
        res = await self.db.execute(stmt)
        await self.db.commit()
        return res.rowcount > 0
```

### ② `ResearchEvidenceFeedRepository` 인터페이스
```python
class ResearchEvidenceFeedRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_insert_feeds(self, session_id: str, feeds: List[ResearchEvidenceFeedModel]) -> List[ResearchEvidenceFeedModel]:
        for f in feeds:
            f.session_id = session_id
            self.db.add(f)
        await self.db.commit()
        return feeds

    async def update_feed_selection(self, feed_id: int, is_selected: bool) -> bool:
        stmt = update(ResearchEvidenceFeedModel).where(ResearchEvidenceFeedModel.id == feed_id).values(is_selected=is_selected)
        res = await self.db.execute(stmt)
        await self.db.commit()
        return res.rowcount > 0

    async def list_selected_feeds(self, session_id: str) -> List[ResearchEvidenceFeedModel]:
        """교차 분석 대상인 채택된(is_selected == True) 피드만 추출."""
        stmt = (
            select(ResearchEvidenceFeedModel)
            .where(ResearchEvidenceFeedModel.session_id == session_id)
            .where(ResearchEvidenceFeedModel.is_selected == True)
            .order_by(ResearchEvidenceFeedModel.id.asc())
        )
        return (await self.db.execute(stmt)).scalars().all()
```

### ③ `ResearchSynthesisRepository` 인터페이스
```python
class ResearchSynthesisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_synthesis(self, session_id: str, synthesis: ResearchSynthesisModel) -> ResearchSynthesisModel:
        """심층 분석 리포트 6대 전문 섹션 갱신/저장."""
        stmt = select(ResearchSynthesisModel).where(ResearchSynthesisModel.session_id == session_id)
        existing = (await self.db.execute(stmt)).scalars().first()
        if existing:
            existing.executive_summary = synthesis.executive_summary
            existing.physical_mechanism = synthesis.physical_mechanism
            existing.academic_vs_industry = synthesis.academic_vs_industry
            existing.tradeoff_analysis = synthesis.tradeoff_analysis
            existing.actionable_recommendations = synthesis.actionable_recommendations
            existing.citation_notes = synthesis.citation_notes
            existing.updated_at = datetime.utcnow()
            await self.db.commit()
            return existing
        else:
            synthesis.session_id = session_id
            self.db.add(synthesis)
            await self.db.commit()
            await self.db.refresh(synthesis)
            return synthesis
```

### ④ `ResearchCandidateRepository` 인터페이스
```python
class ResearchCandidateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_candidates_batch(self, session_id: str, candidates: List[ResearchCandidateModel]) -> List[ResearchCandidateModel]:
        for c in candidates:
            c.session_id = session_id
            self.db.add(c)
        await self.db.commit()
        return candidates

    async def update_export_status(self, candidate_id: int, ticket_id: str) -> bool:
        """Tab 3 검토 센터로 발의 완료 시 티켓 ID 매핑 및 상태 갱신."""
        stmt = (
            update(ResearchCandidateModel)
            .where(ResearchCandidateModel.id == candidate_id)
            .values(exported_ticket_id=ticket_id, status="exported")
        )
        res = await self.db.execute(stmt)
        await self.db.commit()
        return res.rowcount > 0
```

---

## 4.4 Service 계층 설계 (Business Logic Layer - 5대 전문 Service 전수)

### ① `ResearchSessionService` (날짜별 세션 생애주기 총괄)
- **책임**:
  - `get_session_groups(user_id)`: KST 기준 세션 `created_at`을 판별하여 `today`, `yesterday`, `thisWeek`, `older` 4단으로 그룹화하고 `is_pinned` 세션을 각 그룹 최상단에 배치하여 `ResearchSessionListResponse` 반환.
  - `get_session_detail(session_id)`: Eager Loading으로 `feeds`, `synthesis`, `candidates`를 1회 쿼리로 조립하여 2-Column Split View DTO 반환.
  - `delete_session(session_id)`: 하위 피드/리포트/후보 원자적 Cascade 삭제.

### ② `ResearchClarifyService` (조사 범위 구체화 엔진)
- **책임**:
  - Tab 2와 공통 두뇌(`OntologyClarifierService`)를 공유.
  - 온톨로지 지식 그래프에서 엔지니어 질의와 관련된 결함-보상 파라미터 에지를 탐색하여 3대 스코프 칩(예: `10:1 고종횡비`, `화학적 기계 연마`, `휨 방지`)을 0ms 도출.

### ③ `ResearchDiscoverService` (공인 출처 증빙 피드 수집 & 선별 엔진)
- **책임**:
  - 공인 출처 풀(`evidence_sources` 및 학술 인덱스)에서 Tier 1/2 공인 원문 증빙을 수집하여 `research_evidence_feeds`에 벌크 INSERT.
  - 엔지니어가 체크박스를 끄거나 켤 때 `update_feed_selection(feed_id, is_selected)`를 통해 즉시 채택 상태 반영.

### ④ `ResearchSynthesisService` (심층 기술 분석 리포트 & 편입 후보 오케스트레이터)
- **책임**:
  - 엔지니어가 선별한(`is_selected == True`) 피드들만 수집하여 `deep_research_agent.synthesize` 호출.
  - LLM과 온톨로지 에지 추론기를 결합하여, **6대 심층 섹션(Executive Summary, KaTeX 메커니즘, 공정 마진 대조표, 트레이드오프, 사내 팹 권고안, 상세 각주)**을 충실한 볼륨의 엔지니어링 텍스트로 합성.
  - `ResearchSynthesisRepository`에 정규화 저장.
  - 사내 온톨로지 편입 제안 후보(`research_candidates`)를 자동 도출.

### ⑤ `ResearchExportService` (테크니컬 화이트페이퍼 렌더러)
- **책임**:
  - 6대 심층 분석 섹션 + 좌측 증빙 피드 인용구 + 편입 후보를 조합하여 **"사내 공식 기술 동향 보고서 템플릿(Markdown / PDF)"**으로 렌더링하여 다운로드 스트림 서빙.
  - 엔지니어가 팀 세미나나 결재 문서로 즉시 제출할 수 있도록 완결된 파일 제공.

---

# 5. 🤖 [F-01] 플로팅 엔지니어 챗봇 & 공통 계층 설계

## 5.1 물리 Entity 스키마 설계 (Physical Database Schema)

기존의 챗봇 단일 덤프 로그 방식을 폐기하고, **스레드(대화 세션)와 메시지(대화 턴)를 분리하여 세션 혼선을 차단하고, L3 보안 수치를 마스킹 저장하는 2대 정규화 물리 테이블로 구축**합니다.

```
┌────────────────────────────────────────────────────────┐
│             chatbot_threads (대화 스레드 마스터)       │
├────────────────────────────────────────────────────────┤
│ PK thread_id: VARCHAR(64) (th-YYYYMMDD-UUID)           │
│    user_id: VARCHAR(64) NOT NULL, INDEX                │
│    tab: VARCHAR(32) NOT NULL, INDEX                    │
│    target_concept_id: VARCHAR(64) NULLABLE, INDEX      │
│    is_active: BOOLEAN DEFAULT TRUE                     │
│    created_at, updated_at: DATETIME                    │
└──────────────┬─────────────────────────────────────────┘
               │ 1:N
               ▼
┌────────────────────────────────────────────────────────┐
│             chatbot_messages (대화 턴 메시지)          │
├────────────────────────────────────────────────────────┤
│ PK message_id: INTEGER AUTOINCREMENT                   │
│ FK thread_id: VARCHAR(64) ON DELETE CASCADE            │
│    sender: VARCHAR(16) NOT NULL ("user" | "bot")       │
│    content_masked: TEXT NOT NULL (★ L3 보안 마스킹)    │
│    intent_type: VARCHAR(32) ("factoid", "causal", ...) │
│    grounding_citations: JSON (참조된 공인 출처 리스트) │
│    action_card: JSON NULLABLE (화면 이동 카드 페이로드) │
│    created_at: DATETIME                                │
└────────────────────────────────────────────────────────┘
```

---

### [테이블 1] `chatbot_threads` (대화 스레드 마스터 테이블)
- **테이블명**: `chatbot_threads`
- **책임**: 
  - 엔지니어가 각 탭(위키, 비교, 검토, 문헌, 전역)에서 챗봇을 열고 대화할 때 생성되는 독립된 대화 스레드 마스터.
  - 대화 초기화(`DELETE /messages`) 시 활성 플래그(`is_active=False`)를 내리고 새 스레드를 발급하여 과거 대화와 현재 대화가 뒤섞이는 안티패턴을 원천 차단.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `thread_id` | `VARCHAR(64)` | `PRIMARY KEY` | 스레드 고유 식별자 (`th-YYYYMMDD-UUID`) |
| `user_id` | `VARCHAR(64)` | `NOT NULL, INDEX` | 대화 엔지니어 사번/ID |
| `tab` | `VARCHAR(32)` | `NOT NULL, INDEX` | 생성 탭 (`wiki`, `comparison`, `review`, `research`, `global`) |
| `target_concept_id` | `VARCHAR(64)` | `NULLABLE, INDEX` | 연계 개념 ID (통계 및 개념별 질의 분석용) |
| `is_active` | `BOOLEAN` | `NOT NULL, DEFAULT TRUE, INDEX` | 활성 대화 스레드 여부 (초기화 시 False 처리) |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP, INDEX` | 스레드 생성 일시 |
| `updated_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | 최종 갱신 일시 |

---

### [테이블 2] `chatbot_messages` (대화 턴 메시지 테이블)
- **테이블명**: `chatbot_messages`
- **책임**:
  - 스레드에 귀속된 사용자 질문과 챗봇 답변 턴을 정규화 보존.
  - **L3 보안 무누출 저장(`content_masked`)**: 챗봇 답변에 포함된 기밀 수치를 `DeidentificationService`로 마스킹 처리하여 DB에 저장함으로써 로그를 통한 사내 기밀 유출을 원천 방어.
- **컬럼 정의**:

| 컬럼명 | 물리 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `message_id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | 메시지 고유 순차 ID |
| `thread_id` | `VARCHAR(64)` | `NOT NULL, FK(chatbot_threads.thread_id ON DELETE CASCADE), INDEX` | 연계 대화 스레드 ID |
| `sender` | `VARCHAR(16)` | `NOT NULL` | 발화 주체 (`user` [엔지니어], `bot` [지능형 챗봇]) |
| `content_masked` | `TEXT` | `NOT NULL` | 발화 텍스트 전문 (기밀 수치는 `[L3 보안 인가 필요]`로 마스킹) |
| `intent_type` | `VARCHAR(32)` | `NULLABLE` | 판별된 의도 (`factoid`, `causal_clarifier`, `action_trigger`) |
| `grounding_citations`| `JSON` | `DEFAULT '[]'` | 답변 근거로 활용된 공인 출처 목록 (`["E-01", "E-02"]`) |
| `action_card` | `JSON` | `NULLABLE` | 화면 이동 액션 카드 페이로드 |
| `created_at` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP, INDEX` | 메시지 전송 일시 |

---

## 5.2 DTO 계약 스펙 설계 (Pydantic Data Transfer Objects - 6종 전수)

### ① 0ms 탭 적응형 컨텍스트 DTO (`GET /chatbot/context`)
```python
# 1. 0ms 탭 적응형 컨텍스트 응답 DTO (No-LLM Instant Context)
class ChatbotContextResponse(BaseModel):
    tab: str                           # "comparison"
    contextTitle: str                  # "MR-MUF vs TC-NCF 비교 분석 중"
    badgeText: str                     # "Scale 3 · 첨단 패키징 비교 모드"
    engineMode: str                    # "live" | "fallback"
    welcomeMessage: str                # "현재 MR-MUF와 TC-NCF 비교 분석을 진행 중이시군요. 무엇이 궁금하신가요?"
    quickQuestionChips: List[str]      # 0ms 고속 렌더링 칩 3종
```

### ② 대화 질의 및 문맥 강제 주입 DTO (`POST /chatbot/messages`)
```python
# 2. 문맥 강제 주입용 화면 상태 페이로드 (프롬프트 인젝션 방어 정규식 적용)
class ChatbotContextPayload(BaseModel):
    tab: Literal["wiki", "comparison", "review", "research", "global"]
    conceptId: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_-]{3,64}$")
    targetA: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_-]{3,64}$")
    targetB: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_-]{3,64}$")
    ticketId: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_-]{3,64}$")
    sessionId: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_-]{3,64}$")

# 3. 대화 질의 요청 DTO
class ChatbotMessageRequest(BaseModel):
    message: str                       # "둘 중에 뭐가 더 열에 강해?"
    context: ChatbotContextPayload     # 프론트엔드가 캡처한 현재 작업 맥락
    threadId: Optional[str] = None     # 기존 대화 스레드 ID (미지정 시 신규 스레드 발급)

# 4. 액션 트리거 카드 DTO
class ChatbotActionCardDTO(BaseModel):
    title: str                         # "⚡ 기술 대안 비교 스튜디오로 이동"
    targetTab: str                     # "comparison"
    payload: Dict[str, Any]            # { "targetA": "concept-mrmuf", "targetB": "concept-tcncf" }

# 5. 대화 질의 단건 동기 응답 DTO
class ChatbotMessageResponse(BaseModel):
    threadId: str
    intentType: str                    # "factoid" | "causal_clarifier" | "action_trigger"
    answerMarkdown: str                # KaTeX 수식 및 [E-01] 각주가 포함된 완성형 마크다운
    groundingCitations: List[str]      # ["E-01 (Intel Whitepaper)", "E-02 (IEEE 2025)"]
    actionCard: Optional[ChatbotActionCardDTO] = None

# 6. SSE 실시간 스트리밍 청크 DTO (POST /messages/stream 응답 규격)
class ChatbotStreamChunkDTO(BaseModel):
    eventType: Literal["token", "intent", "citation", "action_card", "done", "error"]
    token: Optional[str] = None        # 실시간 타이핑 토큰
    intentType: Optional[str] = None   # 의도 분류 결과
    citation: Optional[str] = None     # 공인 출처 각주 태그
    actionCard: Optional[ChatbotActionCardDTO] = None
    errorMessage: Optional[str] = None
```

### ③ 대화 초기화 및 전역 스포트라이트 검색 DTO (`DELETE /messages`, `GET /search/spotlight`)
```python
# 7. 대화 스레드 초기화 응답 DTO
class ChatbotResetResponse(BaseModel):
    status: str                        # "reset_success"
    newThreadId: str
    restoredContext: ChatbotContextResponse # 초기화 직후 즉시 복원된 환영 상태와 퀵 칩

# 8. 전역 스포트라이트 검색 DTO (동음이의어/카테고리 식별 보강)
class SpotlightItemDTO(BaseModel):
    id: str                            # "concept-thermal-ox"
    title: str                         # "열산화 (Thermal Oxidation)"
    engName: str                       # "Thermal Oxidation"
    domainFacet: str                   # "unit_process"
    processCategory: str               # "산화 및 확산 (Oxidation & Diffusion)"
    scaleLevel: int                    # 3
    scaleName: str                     # "L3 단위 공정"
    summarySnippet: str                # "고온 산소 분위기에서 실리콘 표면에 균일한 절연막을 형성하는 기본 공정"
    matchedField: str                  # "title" | "alias" | "eng_name"

class SpotlightSearchResponse(BaseModel):
    query: str
    results: List[SpotlightItemDTO]
```

---

## 5.3 Repository 계층 설계 (Data Access Layer - 2개 Repository)

### ① `ChatbotThreadRepository` 인터페이스
```python
class ChatbotThreadRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_active_thread(self, user_id: str, tab: str, target_concept_id: Optional[str]) -> ChatbotThreadModel:
        """사용자의 특정 탭 활성 대화 스레드 조회 또는 신규 발급."""
        stmt = (
            select(ChatbotThreadModel)
            .where(ChatbotThreadModel.user_id == user_id)
            .where(ChatbotThreadModel.tab == tab)
            .where(ChatbotThreadModel.is_active == True)
            .order_by(ChatbotThreadModel.created_at.desc())
        )
        thread = (await self.db.execute(stmt)).scalars().first()
        if not thread:
            thread_id = f"th-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
            thread = ChatbotThreadModel(
                thread_id=thread_id,
                user_id=user_id,
                tab=tab,
                target_concept_id=target_concept_id,
                is_active=True
            )
            self.db.add(thread)
            await self.db.commit()
            await self.db.refresh(thread)
        return thread

    async def deactivate_thread(self, thread_id: str) -> bool:
        """대화 초기화 시 기존 스레드 비활성화."""
        stmt = update(ChatbotThreadModel).where(ChatbotThreadModel.thread_id == thread_id).values(is_active=False, updated_at=datetime.utcnow())
        res = await self.db.execute(stmt)
        await self.db.commit()
        return res.rowcount > 0
```

### ② `ChatbotMessageRepository` 인터페이스
```python
class ChatbotMessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_message(
        self, 
        thread_id: str, 
        sender: str, 
        content_masked: str, 
        intent_type: Optional[str] = None, 
        citations: Optional[List[str]] = None, 
        action_card: Optional[Dict[str, Any]] = None
    ) -> ChatbotMessageModel:
        """대화 턴 정규화 저장 (L3 보안 마스킹 적용 텍스트 저장)."""
        msg = ChatbotMessageModel(
            thread_id=thread_id,
            sender=sender,
            content_masked=content_masked,
            intent_type=intent_type,
            grounding_citations=citations or [],
            action_card=action_card
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def list_recent_turns(self, thread_id: str, limit: int = 10) -> List[ChatbotMessageModel]:
        """멀티턴 대화 맥락 조립을 위한 최근 대화 목록 조회."""
        stmt = (
            select(ChatbotMessageModel)
            .where(ChatbotMessageModel.thread_id == thread_id)
            .order_by(ChatbotMessageModel.message_id.asc())
            .limit(limit)
        )
        return (await self.db.execute(stmt)).scalars().all()
```

---

## 5.4 Service 계층 설계 (Business Logic Layer - 3대 전문 Service 전수)

### ① `ChatbotContextService` (0ms 탭 적응형 컨텍스트 어셈블러)
- **책임**:
  - LLM을 일절 호출하지 않고(비용 0원, 5ms 지연시간 보장) 순수 DB RDBMS 메타데이터만으로 작업 맥락 뱃지와 맞춤 환영 인사, 퀵 칩 3종을 즉시 조립.
  - **인과 에지 부재 시 3단계 계층형 폴백(Hierarchical Fallback)**을 완벽히 집행:
    - 1순위: `causal_edges`에 결함/보상 파라미터가 있으면 ➔ 초정밀 공학 칩 생성.
    - 2순위: 에지가 없으면 ➔ `concepts`의 `limitations`, `principles` 텍스트를 파싱하여 질문 칩 생성.
    - 3순위: 텍스트도 없으면 ➔ 기본 표준 엔지니어링 템플릿(공인 실측 출처 보기 등) 적용.

### ② `ChatbotMessageService` (문맥 강제 주입 & 3단 인텐트 라우터 & 보안 로깅)
- **책임**:
  - **시스템 프롬프트 상단에 작업 맥락 강제 주입(Context Injection)**:
    - *"사용자가 '둘 중에', '그 공정' 등 대명사를 사용하면 즉시 대상 A(MR-MUF)와 대상 B(TC-NCF)를 지칭하는 것으로 해석할 것."*
  - `ClarifierAgent`를 호출하여 3단 의도 실시간 분류 및 답변 합성:
    - `factoid`: 공인 출처 `[E-01]` 각주와 함께 절대 수치 즉답.
    - `causal_clarifier`: 2-Hop 인과망을 바탕으로 원인-결함 체인 설명.
    - `action_trigger`: 답변과 함께 Tab 2 비교 화면으로 즉시 이동하는 액션 카드 DTO 동봉.
  - **SSE(Server-Sent Events) 실시간 토큰 스트리밍** 지원 (`POST /messages/stream`).
  - **L3 기밀 무누출 보안 파이프라인**:
    - 인가자에게 전달되는 응답에는 평문이 포함될 수 있으나, **DB에 대화 이력을 영구 보존할 때는 `DeidentificationService`를 경유하여 L3 기밀 수치를 마스킹한 후 저장**.

### ③ `SpotlightSearchService` (0ms 전역 개념 검색 게이트웨이)
- **책임**:
  - 상단 헤더 및 단축키(`Ctrl + K`) 입력 시 `ConceptRepository.search_by_prefix`를 호출하여 0ms 자동완성 서빙.
  - 공정 카테고리(`processCategory`)와 1줄 설명 요약(`summarySnippet`)을 동봉하여 동음이의어 혼선 원천 차단.
  - Tab 2 비교 대안 검색 및 Tab 4 문헌 조사 개념 타깃팅에서 100% 재사용.

---

# 6. 🌐 [공통 코어 인프라] 4대 전역 모듈화 아키텍처 (Global Core Orchestrators)

시스템 전반(Tab 1~4 및 챗봇)에 걸쳐 코드 중복을 제거하고, 모델 교체 유연성과 데이터 무결성을 단일 창구에서 일괄 통제하기 위해 **4대 전역 코어 모듈**을 구축합니다.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   전 도메인 서비스 계층 (Domain Services)              │
└───────┬─────────────────┬──────────────────┬───────────────────┬───────┘
        │                 │                  │                   │
        ▼                 ▼                  ▼                   ▼
┌──────────────┐  ┌──────────────┐   ┌──────────────┐    ┌──────────────┐
│  call_agent  │  │ Evidence     │   │ Report       │    │ Cache        │
│  (총괄게이트)│  │ CitationMgr  │   │ Renderer     │    │ Orchestrator │
├──────────────┤  ├──────────────┤   ├──────────────┤    ├──────────────┤
│- 모델원클릭교체│  │- [E-01]파싱  │   │- 마크다운렌더│    │- 도메인전체  │
│- 30초타임아웃│  │- 출처자동복원│   │- KaTeX 수식  │    │  캐시일괄소거│
│- Graceful    │  │- 사내공식승격│   │- 마진대조표  │    │- Stale Cache │
│  Fallback    │  │  (E-05발급)  │   │- Jinja2 템플릿│   │  원천 차단   │
└──────────────┘  └──────────────┘   └──────────────┘    └──────────────┘
```

---

## 6.1 `AgentGateway` (`call_agent` 4-Tier 단일 총괄 함수)

- **책임**: 파편화된 에이전트 클래스 호출을 단일 게이트웨이 함수로 일원화하고, **[지연시간 / 추론 난이도 / 사내 보안 기밀도]에 따른 4-Tier 하이브리드 인과 추론 체계**를 단일 인터페이스에서 통제.
- **4-Tier 아키텍처 계층 구조**:
  1. **Tier 1 (Fast Cloud LLM)**: `gpt-4o-mini` / `gemini-flash` (0.5~1.2초 저지연 팝오버 문맥 해설, 단답 챗봇)
  2. **Tier 2 (Deep Reasoning Cloud LLM)**: `gpt-4o` / `gemini-pro` (30초 복합 다차원 비교 매트릭스, 튜닝 수식, 거버넌스 JSON 패치)
  3. **Tier 3 (On-Premise Air-Gapped Local LLM)**: 사내 폐쇄망 vLLM / Ollama (Qwen-7B) + `DLPTokenizer` 구간 가명화 (L3 극비 양산 레시피 외부 반출 원천 차단)
  4. **Tier 4 (Deterministic Zero-AI Engine)**: SQLite `causal_edges` 0.65ms Recursive CTE & 물리 안전 마진 수식 (AI 전면 단절 시 최후의 100% 무중단 물리 안전망)

- **인터페이스 규격**:

```python
async def call_agent(
    agent_type: Literal["explainer", "chatbot", "clarifier", "directive", "advisor", "deep_research", "comparison"],
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
    system_instruction: Optional[str] = None,
    model_name: Optional[str] = None,
    tier: Optional[Literal["tier1_fast", "tier2_reasoning", "tier3_local"]] = None,
    timeout_seconds: Optional[float] = None,
    gemini_key: Optional[str] = None,
    openai_key: Optional[str] = None
) -> AgentResponse:
    """전 도메인 에이전트/LLM 호출 4-Tier 단일 총괄 게이트웨이 함수.
    
    1. 4-Tier 자동 디스패치:
       - explainer, chatbot ➔ Tier 1 (초경량 고속 클라우드 AI, 5초)
       - comparison, advisor, directive, deep_research ➔ Tier 2 (고성능 심층 추론 AI, 30초)
       - isSecretRecipe / isTier3 컨텍스트 ➔ Tier 3 (사내 에어갭 폐쇄망 로컬 AI)
       - AI 호출 실패 / 오프라인 ➔ Tier 4 (순수 온톨로지 결정론적 추론 엔진 안전 착륙)
    2. Active Cross-Failover: 1순위 모델 실패 시 2순위 모델로 자동 교차 전환.
    3. 타임아웃 및 무중단 보장: 타임아웃 초과 시 500 크래시 방지 및 Tier 4 안전 기본 응답 반환.
    """
    ...
```

---

## 6.2 `EvidenceCitationManager` (공인 출처 각주 총괄 매니저)

- **책임**: Tab 1(위키 본문 링크), Tab 3(직접 편집 출처 삭제 방어), Tab 4(문헌 조사 각주 부여 및 승격), 챗봇(근거 출처 바인딩) 전역에서 일관된 출처 규칙 집행.
- **주요 메서드**:
  - `parse_citations(text: str) -> List[str]`: 본문 내 `\[E-\d+\]` 정규식 태그 전수 추출.
  - `validate_and_restore(original: str, edited: str) -> str`: 편집 과정에서 사용자가 실수로 삭제한 공인 출처 뱃지를 감지하여 문장 끝에 자동 복원 주입.
  - `promote_to_evidence_source(feed_id: int, db: AsyncSession) -> str`: Tab 4 외부 문헌이 검토 승인되었을 때 사내 공식 출처 마스터(`evidence_sources`)에 `E-05` 같은 정식 고유 번호를 발급하고 영구 승격.

---

## 6.3 `ReportRenderer` (표준 기술 보고서 렌더러)

- **책임**: Tab 2 비교 분석 리포트, Tab 4 외부 문헌 6대 심층 분석 리포트, Tab 3 거버넌스 감사 보고서를 일관된 사내 표준 기술 문서 스타일의 마크다운(Markdown) 및 PDF 파일로 렌더링.
- **주요 메서드**:
  - `render_markdown(template_name: str, context: Dict[str, Any]) -> str`: Jinja2 기반으로 메타데이터 헤더, KaTeX 수식 블록, 학계 vs 산업계 마진 대조표, 공인 출처 상세 각주를 깔끔한 기술 문서로 합성.
  - `export_file_response(filename: str, content: str) -> FileResponse`: 다운로드 스트림 서빙.

---

## 6.4 `CacheOrchestrator` (전 도메인 캐시 일괄 무효화 오케스트레이터)

- **책임**: 위키 승인(`POST /approve`) 또는 개념 수정 시, 하드코딩된 문자열 오타로 인한 Stale Cache 잔존 버그를 원천 차단하고 연관 캐시를 원자적으로 일괄 소거.
- **주요 메서드**:
  - `invalidate_concept_domain(concept_id: str)`:
    - 1. 위키 본문 캐시 소거: `concept:detail:{concept_id}`
    - 2. 2-Hop 인과 서브그래프 캐시 소거: `concept:subgraph:{concept_id}:*`
    - 3. 인라인 용어 설명 캐시 소거: `concept:explainer:{concept_id}:*`
    - 4. 전역 스포트라이트 검색 캐시 소거: `spotlight:*`
    - 5. 플로팅 챗봇 컨텍스트 캐시 소거: `chatbot:context:*`
    - 단 한 번의 호출로 전 도메인의 캐시 정합성을 0ms로 보장.

---

# 7. 🛡️ 보안 거버넌스 및 사용자 권한(Auth & RBAC) 계층 설계

> **책임 및 도메인 목적**:  
> 사내 폐쇄망 환경에서 구글 등 외부 인증 의존성 없이 자체 엔지니어 계정을 안전하게 발급/관리하고,  
> 4단계 권한 레벨(Level 1~4) 기반의 엄격한 역할 기반 접근 제어(RBAC)와 비인가 지식(L3 극비 레시피) 열람 신청·심사·승인·회수 거버넌스를 관장한다.  
> 반도체 WORM 무결성 원칙에 따라 사용자 계정 삭제는 물리 삭제(Hard Delete)를 금지하고 비활성화(Soft Delete: `is_active = False`) 방식으로 안전하게 처리한다.

---

## 7.1 물리 Entity 스키마 설계 (Physical Database Schema)

```
┌─────────────────────────────────┐
│              users              │
├─────────────────────────────────┤
│ PK  id (사번/고유식별자)        │
│     username (로그인 ID)        │
│     password_hash (솔팅 해시)   │
│     name, department            │
│     role (기본 'line_engineer') │
│     level (1~4 정수형 등급)     │
│     is_active (Soft Delete 플래그)
│     created_at, updated_at      │
└──────────────┬──────────────────┘
               │ 1:N
               ▼
┌─────────────────────────────────┐
│         access_requests         │
│ (비인가 지식 열람 권한 신청 큐) │
├─────────────────────────────────┤
│ PK  id (req-YYYYMMDD-xxxx)      │
│ FK  user_id (신청 엔지니어)     │
│ FK  concept_id (대상 공정 개념) │
│     concept_title               │
│     reason (열람 목적 사유)     │
│     status                      │
│     (pending/approved/rejected/ │
│      revoked)                   │
│ FK  reviewed_by (심사 관리자)   │
│     reviewed_at                 │
│     review_comment              │
│     created_at, updated_at      │
└─────────────────────────────────┘
```

### [테이블 1] `users` (사내 엔지니어 계정 마스터 테이블)
- **테이블명**: `users`
- **컬럼 정의**:
  - `id`: `VARCHAR(64) PRIMARY KEY` (사번 또는 고유 ID, 예: `EMP-2026-001`)
  - `username`: `VARCHAR(64) UNIQUE NOT NULL` (로그인 아이디)
  - `password_hash`: `VARCHAR(256) NOT NULL` (PBKDF2-HMAC-SHA256 솔팅 암호문)
  - `name`: `VARCHAR(64) NOT NULL` (엔지니어 실명)
  - `department`: `VARCHAR(64) NOT NULL` (소속 부서, 예: `HBM패키징개발팀`)
  - `role`: `VARCHAR(32) NOT NULL DEFAULT 'line_engineer'` (`line_engineer` | `chief_reviewer` | `admin`)
  - `level`: `INTEGER NOT NULL DEFAULT 2` (1: 게스트, 2: 현장 엔지니어, 3: 수석 검토관, 4: 시스템 관리자)
  - `is_active`: `BOOLEAN NOT NULL DEFAULT 1` (계정 활성화 상태, 탈퇴/차단 시 0)
  - `created_at`: `DATETIME DEFAULT CURRENT_TIMESTAMP`
  - `updated_at`: `DATETIME DEFAULT CURRENT_TIMESTAMP`

### [테이블 2] `access_requests` (비인가 지식 열람 신청 및 거버넌스 심사 테이블)
- **테이블명**: `access_requests`
- **컬럼 정의**:
  - `id`: `VARCHAR(64) PRIMARY KEY` (신청 티켓 ID, 예: `req-20261021-001`)
  - `user_id`: `VARCHAR(64) NOT NULL, FK(users.id ON DELETE CASCADE)`
  - `concept_id`: `VARCHAR(64) NOT NULL, FK(concepts.id ON DELETE CASCADE)`
  - `concept_title`: `VARCHAR(128) NOT NULL` (대상 공정 명칭)
  - `reason`: `TEXT NOT NULL` (열람 신청 목적 및 사유)
  - `status`: `VARCHAR(16) NOT NULL DEFAULT 'pending'` (`pending` | `approved` | `rejected` | `revoked`)
  - `reviewed_by`: `VARCHAR(64) NULLABLE, FK(users.id ON DELETE SET NULL)`
  - `reviewed_at`: `DATETIME NULLABLE`
  - `review_comment`: `TEXT NULLABLE` (관리자 심사 의견/반려 사유)
  - `created_at`: `DATETIME DEFAULT CURRENT_TIMESTAMP`
  - `updated_at`: `DATETIME DEFAULT CURRENT_TIMESTAMP`

---

## 7.2 Pydantic DTO 계약 스펙 (Contract Schemas)

1. **`UserRegisterDTO`**: `username`, `password`, `name`, `department` (사내 회원가입 입력)
2. **`UserLoginDTO`**: `username`, `password` (로그인 입력)
3. **`TokenResponseDTO`**: `accessToken`, `tokenType: "Bearer"`, `expiresIn: 86400`, `user: UserDTO`
4. **`UserDTO`**: `id`, `username`, `name`, `department`, `role`, `level`, `isActive`, `createdAt` (비밀번호 제외)
5. **`PasswordChangeDTO`**: `oldPassword`, `newPassword`
6. **`AccessRequestCreateDTO`**: `conceptId`, `reason` (최소 5자 이상 상세 기술)
7. **`AccessRequestDTO`**: `id`, `userId`, `userName`, `userDepartment`, `conceptId`, `conceptTitle`, `reason`, `status`, `reviewedBy`, `reviewedAt`, `reviewComment`, `createdAt`
8. **`AccessReviewDTO`**: `comment` (승인/반려/회수 코멘트)
9. **`UserLevelUpdateDTO`**: `level: int` (1~4 유효성 검증)

---

## 7.3 Repository 계층 (Data Access Layer)

- **`UserRepository`**:
  - `get_by_id(user_id)` / `get_by_username(username)`
  - `create_user(user_entity)`
  - `list_users(role, level, search, limit, offset)`
  - `update_level(user_id, new_level)`
  - `soft_delete_user(user_id)`: `is_active = False` 처리
- **`AccessRequestRepository`**:
  - `create_request(request_entity)`
  - `get_by_id(request_id)`
  - `list_by_user(user_id)`: 본인 신청 내역
  - `list_for_admin(status_filter, limit, offset)`: 관리자 큐 조회
  - `find_pending_or_approved(user_id, concept_id)`: 중복 신청 및 기승인 여부 확인
  - `has_active_approval(user_id, concept_id)`: 현재 시점에 유효한 승인 티켓 존재 여부 (0.5ms 초고속 쿼리)

---

## 7.4 Service 계층 (Domain & Security Services)

1. **`PasswordSecurityService`**:
   - `hash_password(plain: str) -> str`: 솔트(32바이트) 생성 + `hashlib.pbkdf2_hmac` 암호화.
   - `verify_password(plain: str, hashed: str) -> bool`: 일정 시간 비교(`hmac.compare_digest`)로 타이밍 공격 방어.
2. **`TokenManagerService`**:
   - `create_access_token(user: UserModel, expires_delta: timedelta) -> str`: HMAC-SHA256 기반 JWT 서명.
   - `decode_access_token(token: str) -> Dict[str, Any]`: 위조 검사, 서명 확인, `exp` 만료 판정.
3. **`AuthService`**:
   - `register(dto)`: 중복 아이디 방어(`409 Conflict`), 기본 `level=2` 부여.
   - `authenticate(dto)`: 자격 증명 검증, 비활성화 계정 차단(`403`), 성공 시 토큰 발급.
   - `change_password(user, old_pw, new_pw)`: 기존 비밀번호 대조 후 신규 해시 갱신.
   - `deactivate_self(user)`: 본인 회원 탈퇴 (Soft Delete).
4. **`AccessControlService` (비인가 지식 권한 심사 총괄)**:
   - `create_access_request(user, dto)`: 중복 대기 방지(`409`), 기승인 차단(`400`).
   - `cancel_access_request(user, request_id)`: 대기(`pending`) 중인 본인 신청 자진 취소(`DELETE`).
   - `approve_request(admin_user, request_id, comment)`: 관리자 승인(`POST /approve`) ➔ 승인 상태 갱신.
   - `reject_request(admin_user, request_id, comment)`: 관리자 반려(`POST /reject`) ➔ 반려 사유 기록.
   - `revoke_approval(admin_user, request_id, comment)`: 기승인 권한 강제 회수(`POST /revoke`) ➔ `status='revoked'`.
   - **`can_view_confidential_l3(user: Optional[UserModel], concept_id: str) -> bool`**:
     - 1차: `user.level >= 3`이면 100% 열람 허가 (True).
     - 2차: `user.level < 3`이더라도 `has_active_approval(user.id, concept_id)`가 True이면 **L3 마스킹을 해제하고 실제 수치 반환 (True)**.
     - 3차: 비로그인 또는 미승인 상태면 마스킹 처리 (False).
5. **`UserAdminService`**:
   - `update_user_level(admin_user, target_user_id, new_level)`: 슈퍼 어드민 자기 자신 강등 방어(`400`), 대상 엔지니어 레벨 조정.
   - `deactivate_user_by_admin(admin_user, target_user_id)`: 관리자에 의한 퇴사자 계정 차단 (Soft Delete).

---

## 7.5 Router / Controller 계층 (`/api/v1/auth`)

모든 보안, 인증, 인가, 권한 열람 신청 엔드포인트는 단일 라우터(`/api/v1/auth`)로 통합된다.

| HTTP 메서드 | 엔드포인트 URL | 인가 가드레일 | 주요 동작 및 설명 |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/auth/register` | Public | 사내 자체 회원가입 (기본 Level 2 현장 엔지니어 부여) |
| **POST** | `/api/v1/auth/login` | Public | 자체 로그인 ➔ 24시간 유효 JWT 토큰 및 사용자 정보 반환 |
| **POST** | `/api/v1/auth/refresh` | Bearer Token | 만료 직전 토큰 무중단 갱신 (새 Access Token 발급) |
| **GET** | `/api/v1/auth/me` | Bearer Token | 내 프로필 및 권한 레벨(`level`) 조회 (SPA 새로고침 세션 복원) |
| **POST** | `/api/v1/auth/change-password` | Bearer Token | 비밀번호 변경 (기존 비밀번호 확인 ➔ 새 암호 해시 갱신) |
| **DELETE**| `/api/v1/auth/me` | Bearer Token | 본인 회원 탈퇴 (Soft Delete: `is_active=False`) |
| **POST** | `/api/v1/auth/access-requests` | Bearer Token | L3 비인가 지식 열람 권한 신청 (사유 제출 ➔ `pending` 티켓 생성) |
| **GET** | `/api/v1/auth/access-requests/my` | Bearer Token | 내가 신청한 열람 내역 및 승인 상태 확인 |
| **DELETE**| `/api/v1/auth/access-requests/{id}` | Bearer Token | 본인의 대기 중(`pending`)인 열람 신청 자진 취소 |
| **GET** | `/api/v1/auth/access-requests` | `level >= 3` | 관리자 전용: 미결 열람 신청 큐 목록 조회 |
| **POST** | `/api/v1/auth/access-requests/{id}/approve` | `level >= 3` | 관리자 승인 (승인 시 해당 유저에게 해당 개념 L3 마스킹 영구 해제) |
| **POST** | `/api/v1/auth/access-requests/{id}/reject` | `level >= 3` | 관리자 반려 (반려 사유 필수 요구) |
| **POST** | `/api/v1/auth/access-requests/{id}/revoke` | `level >= 3` | 관리자의 기승인 권한 강제 회수 (`status='revoked'`, 마스킹 재적용) |
| **GET** | `/api/v1/auth/users` | `level >= 4` | 시스템 관리자 전용: 전체 엔지니어 목록 및 level 현황 조회 |
| **PATCH** | `/api/v1/auth/users/{user_id}/level` | `level >= 4` | 시스템 관리자 전용: 특정 엔지니어 level(권한 등급) 승격/강등 |
| **DELETE**| `/api/v1/auth/users/{user_id}` | `level >= 4` | 시스템 관리자 전용: 퇴사자/비인가자 계정 강제 비활성화 (Soft Delete) |

---

## 7.6 토큰 만료 및 유효성 검사 아키텍처 (FastAPI 의존성 주입)

- **`get_current_active_user` 의존성**:
  - 보호된 모든 라우터는 라우터 내부에서 일일이 토큰을 검사하지 않고, FastAPI 의존성 `Depends(get_current_active_user)`를 통해 선제 검증된다.
  - 토큰 누락 시 `401 Unauthorized (MISSING_TOKEN)`
  - 토큰 만료 시 `401 Unauthorized (TOKEN_EXPIRED)`
  - 계정 비활성화 시 `403 Forbidden (USER_INACTIVE)`
- **`require_min_level(min_level: int)` 가드 데코레이터**:
  - `Depends(require_min_level(3))` 선언만으로 수석검토관 미달 시 `403 Forbidden` 자동 방어.

---

## 7.7 기존 라우터 및 서비스의 RBAC 실연동 전환 로드맵 (Migration Roadmap & TODO)

> **전환 원칙**: 사내 Auth & RBAC 핵심 인프라(Entity ➔ DTO ➔ Repository ➔ Service ➔ `/api/v1/auth` 라우터) 구현 및 검증이 완료된 즉시, 기존의 취약한 `X-User-Role` 임시 헤더 기반 로직을 아래 표준 가드레일로 전면 교체한다.

### 1. `backend/app/api/review_tickets.py`
- **`POST /api/v1/review-tickets/{ticket_id}/approve` & `reject`**:
  - `x_user_role` 임시 헤더 제거 ➔ `current_user: UserModel = Depends(require_min_level(3))` 주입.
  - WORM 감사로그(`audit_logs.actor`)에 임시 문자열 대신 실제 인증된 `current_user.id` 및 `current_user.name` 영구 기록.
- **`POST /api/v1/review-tickets` (새 문서/티켓 발의)**:
  - `current_user: UserModel = Depends(require_min_level(2))` 주입 (Level 1 게스트 발의 차단).
  - `proposer_id`에 실제 로그인된 `current_user.id` 자동 바인딩.
- **`POST /api/v1/review-tickets/{ticket_id}/directive` (보완 지시문)**:
  - `current_user: UserModel = Depends(require_min_level(2))` 주입.
- **`POST /api/v1/review-tickets/{ticket_id}/presence` (동시 편집 락)**:
  - 클라이언트 임의 `body.userId` 대신 실제 인증된 `current_user: UserModel = Depends(require_min_level(2))`의 ID로 락 홀더 바인딩.
- **`PUT /api/v1/review-tickets/{ticket_id}/human-edits` (전문가 직접 본문 편집 저장)**:
  - `current_user: UserModel = Depends(require_min_level(2))` 주입 (비인가자의 위키 본문 임의 덮어쓰기 방어).

### 2. `backend/app/api/concepts.py`
- **`GET /api/v1/concepts/{concept_id}` (위키 상세 본문 서빙)**:
  - `x_user_role` 임시 헤더 ➔ `current_user: Optional[UserModel] = Depends(get_current_user_optional)` 주입.
  - `can_view = await AccessControlService.can_view_confidential_l3(current_user, concept_id, db)` 호출.
  - `can_view == True`인 경우(Level >= 3 이거나 해당 공정에 대해 승인된 `access_requests` 티켓 보유 시) L3 절대 수치 원문 서빙, 그 외에는 `[🔒 대외비 마스킹]` 및 열람 신청 CTA 유지.

### 3. `backend/app/api/comparison.py` (Tab 2 비교 분석실)
- **`POST /api/v1/comparison-sessions` (신규 비교 세션 생성)**:
  - 클라이언트 임의 `body.userId` 조작 방지 ➔ `current_user: Optional[UserModel] = Depends(get_current_user_optional)`로 실제 로그인 세션 소유자 자동 매핑.
- **`POST /api/v1/comparison-sessions/{session_id}/export-review` & `/export-ticket` (검토 센터 티켓 발의)**:
  - `current_user: UserModel = Depends(require_min_level(2))` 주입 (공식 위키 개정 발의 권한 가드).
  - `ticket.author`에 실제 인증된 `current_user.name` 및 부서 바인딩.

### 4. `backend/app/api/research.py` (Tab 4 외부 문헌 조사실)
- **`POST /api/v1/research/candidates/{candidate_id}/export-ticket` (발굴 지식 검토 센터 티켓 발의)**:
  - `current_user: UserModel = Depends(require_min_level(2))` 주입.
  - `ticket.author`에 실제 인증된 `current_user.name` 및 부서 바인딩.

### 5. `backend/app/api/system.py`
- **`POST /api/v1/security/access-requests`**:
  - DB 미연동 Mock 엔드포인트 폐기 ➔ 정규화된 물리 테이블 연동 엔드포인트 `POST /api/v1/auth/access-requests`로 리다이렉트 또는 안내 메시지 반환.
- **`GET /api/v1/system/audit/verify-integrity` (WORM 감사 무결성 검증)**:
  - `current_user: UserModel = Depends(require_min_level(3))` 주입 (수석검토관 이상 전용 감사 검증 가드).





