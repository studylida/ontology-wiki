# ⚖️ 기술 대안 비교분석 도메인 재설계 및 계층별 아키텍처 명세서

> **문서 목적**:  
> 기술 대안 비교분석(Perspective Studio)의 복잡도를 낮추고 사용자 경험(UX)을 극대화하기 위해,  
> 탐색형(초보자)과 목적형(숙련자)을 모두 만족시키는 듀얼 트랙 입력 체계와  
> 세션 관리 및 목적별 AI 에이전트 계층화 구조를 정립하기 위한 기준 문서입니다.

---

## 1. [화면 2-A: 조사·분석 요청실] UI/UX 개편 및 듀얼 트랙(Dual Track) 설계

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

## 2. 도메인 컨트롤러 & 서비스 계층 정의

사용자님의 통찰대로 **에이전트를 호출하더라도 기대하는 입력과 출력(DTO), 그리고 화면 맥락이 완전히 다르므로 컨트롤러 단에서 목적별로 명확히 분리**합니다.

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

## 3. 에이전트 호출을 컨트롤러 단에서 분리해야 하는 3대 공학적 근거

사용자님께서 판단하신 **"에이전트를 호출하더라도 컨트롤러 단에서 나눠놓는 게 맞다"**는 결정은 다음 3가지 이유로 완벽한 정답입니다:

1. **DTO 타입 계약(Type Safety)의 엄격성**:
   - `질문 구체화(분기 카드 반환)`와 `파라미터 튜닝(보상안 수치 반환)`, `꼬리질문(인과 체인 반환)`은 Request와 Response의 형태가 완전히 다릅니다.
   - 하나의 컨트롤러로 뭉뚱그리면 DTO가 온갖 Optional 필드로 뒤범벅된 거대 잡탕 스키마가 되어 프론트엔드 연동 시 타입 에러를 양산합니다.
2. **RESTful 리소스 지향성**:
   - 세션 내부의 하위 리소스(`/matrix`, `/tune-advisor`, `/deep-dive`)로 분리되어 URL만 보아도 어떤 결과물을 기대하는지 명확합니다.
3. **독립적 장애 격리**:
   - 파라미터 튜닝 상담에 일시적인 LLM 타임아웃이 발생해도, 기본 비교 매트릭스 조회나 세션 목록 조회 등 다른 기능은 100% 정상 작동합니다.
