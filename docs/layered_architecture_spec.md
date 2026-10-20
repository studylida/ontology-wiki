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
  - `get_ticket_list(status, concept_id, limit, offset)`: 기본값 `status="pending"`으로 대기열 서빙, `count_by_status()`를 병렬 호출하여 `tabCounts`를 번들 조립.
  - `get_ticket_detail(ticket_id)`: 원본 본문(`current_content`), 최신 단일 초안(`working_draft`), 3대 정합성 보고서, 지시문 대화 이력, 현재 동시 접속자 락 상태를 2-Pane DTO로 합성.

### ② `PresenceLockService` (비차단 분산 편집 락 전담 엔진)
- **책임**:
  - `acquire_lock(ticket_id, user_id, ttl=30)`: Redis 또는 인메모리 락 매니저를 통해 점유자 확인. 미점유 시 획득 성공, 타인 점유 시 읽기 전용 상태 안내.
  - `renew_lock(ticket_id, user_id, ttl=30)`: 본인 락 유지 시간 연장.
  - `release_lock(ticket_id, user_id)`: 탭 퇴장 또는 승인/반려 시 안전하게 락 즉시 반납.

### ③ `ReviewDirectiveService` (전문가 AI 보완 지시문 실행 엔진)
- **책임**:
  - 엔지니어의 자연어 지시문 수신 ➔ `directive_agent` 호출.
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
  - **3. 단일 원자적 DB 트랜잭션 (Atomic Decomposition)**:
    - `working_draft`에 포함된 섹션별 패치를 분해(Decomposition)하여, 공용 위키의 각 정규화 물리 테이블에 반영:
      - `concepts`: `version` 판본 승계 (예: `v1.2` ➔ `v1.3`), `summary` 갱신.
      - `concept_principles`: 수정/추가된 작동 원리 단계 UPDATE/INSERT.
      - `concept_limitations`: 갱신된 공정 한계 및 보상 파라미터 UPDATE/INSERT.
      - `perspective_specifications`: 변경된 공정 관점별 물리 수치 UPDATE/INSERT.
  - **4. WORM 머클 감사 체인 확정**:
    - 직전 `entry_hash`를 조회하여 현재 승인 스냅샷과 결합한 새 SHA-256 해시를 생성하고 HMAC 전자 서명과 함께 `audit_logs`에 INSERT.
  - **5. 위키 캐시 즉시 무효화 (0ms 전사 공표)**:
    - `concept:detail:{id}`, `concept:subgraph:{id}:*` 캐시를 즉시 제거하여 모든 사용자가 새로 승인된 위키를 0ms 지연으로 열람 가능하도록 보장.

---

# 4. 📑 [Tab 4] 외부 문헌·백서 조사 계층 설계 (작성 예정)

*(사용자님과 다음 대화에서 Tab 4 Entity/DTO/Repository/Service 설계 후 통합 수록)*

---

# 5. 🤖 [F-01] 플로팅 챗봇 & 공통 계층 설계 (작성 예정)

*(사용자님과 다음 대화에서 챗봇/공통 Entity/DTO/Repository/Service 설계 후 통합 수록)*
