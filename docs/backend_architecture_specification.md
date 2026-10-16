# 반도체 공정·소자 인과 온톨로지 위키: 백엔드 아키텍처 및 지원 규격서

> **[문서 목적]**: 확정된 프론트엔드 화면 명세서(`docs/frontend_screens_specification.md`)의 모든 기능(적응형 Level 3 실무 카드, 2단계 비교분석 및 파라미터 튜닝 상담자, 2-Segment 검토 센터, 2단계 외부 문헌 조사 등)을 기술적으로 뒷받침하기 위한 백엔드 데이터 모델, AI 인과 추론 파이프라인, REST API 규격, 비기능 아키텍처를 정의하는 공식 기술 문서입니다.

---

## 목차

1. [백엔드 설계 원칙 및 시스템 개요](#1-백엔드-설계-원칙-및-시스템-개요)
2. [1단계: 온톨로지 코어 데이터 모델 & 엔티티 스키마](#2-1단계-온톨로지-코어-데이터-모델--엔티티-스키마)
   - 2.1 `Concept` (온톨로지 핵심 개념 엔티티)
   - 2.2 `PerspectiveCase` (적응형 Level 3 실무 사례 엔티티)
   - 2.3 `ComparisonSession` (기술 대안 비교 세션 엔티티)
   - 2.4 `ReviewTicket` (검토·승인 거버넌스 티켓 엔티티)
   - 2.5 `EvidenceSource` (공식 출처 및 원문 근거 엔티티)
   - 2.6 [아키텍처 당위성] 풍부한 도메인 모델(Aggregate)을 채택한 설계 이유
3. [2단계: AI 에이전트 & 인과 추론 파이프라인 아키텍처](#3-2단계-ai-에이전트--인과-추론-파이프라인-아키텍처)
   - 3.1 대화형 질문 구체화 파이프라인 (Clarifier Engine)
   - 3.2 다차원 기술 대안 비교 매트릭스 생성기 (Comparison Engine)
   - 3.3 AI 파라미터 튜닝 상담 파이프라인 (Advisor Engine)
   - 3.4 지식 무결성 검증 및 초안 재작성 파이프라인 (Directive Engine)
   - 3.5 공인 문헌 교차 분석 및 초안 합성기 (Deep Research Engine)
4. [3단계: 화면별 REST API 엔드포인트 명세 (작성 예정)](#4-3단계-화면별-rest-api-엔드포인트-명세)
5. [4단계: 실시간 동기화, 캐시 및 보안 아키텍처 (작성 예정)](#5-4단계-실시간-동기화-캐시-및-보안-아키텍처)

---

## 1. 백엔드 설계 원칙 및 시스템 개요

1. **무결성과 할루시네이션(환각) 제로**:
   - 일반 챗봇의 자유로운 환각 생성을 엄격히 배제하며, 모든 추론은 공인 출처(`EvidenceSource`)와 인과 온톨로지 그래프 관계를 선행 조건으로 삼는다.
2. **엔지니어링 실험 재현성 (Reproducibility)**:
   - 비교분석 및 파라미터 튜닝 결과는 스냅샷 불변 보존 원칙을 통해 1년 뒤에 조회해도 완전히 동일한 수치와 매트릭스로 복원된다.
3. **지식 거버넌스 감사 추적 (Audit Immutability)**:
   - 검토·승인 티켓은 승인 시점의 원문, AI 초안, 전문가 지시문, 무결성 점검 지표를 스냅샷으로 영구 보존하여 법적·기술적 감사 신뢰성을 확보한다.

---

## 2. 1단계: 온톨로지 코어 데이터 모델 & 엔티티 스키마

### 2.1 `Concept` (온톨로지 핵심 개념 엔티티)
- **역할**: [Tab 1] 위키 본문의 메인 지식이자 온톨로지 인과 그래프의 핵심 노드.

```typescript
interface Concept {
  id: string;                     // 불변 고유 식별자 (예: "concept-dry-etch-001")
  title: string;                  // 국문 공식 명칭 (예: "플라즈마 건식 식각")
  engName: string;                // 영문 학술 명칭 (예: "Plasma Dry Etching")
  aliases: string[];              // 현장 약어 및 별칭 (예: ["RIE", "건식 식각"])
  
  // 🏛️ 업무 분야 4축 & 📐 물리 규모 5단계 매핑
  domainFacet: "device" | "unit_process" | "operations" | "materials_infra";
  processCategory: string;        // 단위 카테고리 (예: "식각 공정", "3D 적층", "FDC 이상감지")
  scaleLevel: 1 | 2 | 3 | 4 | 5;  // 1(<1nm) ~ 5(팹 인프라 1km)
  
  // 버전 및 상태 거버넌스
  version: string;                // 현재 공식 판본 (예: "v1.2")
  status: "adopted" | "in_review" | "deprecated"; // 채택됨 / 검토중 / 폐기됨
  lastReviewedAt: string;         // 최종 승인 일자 (ISO-8601)
  lastReviewedBy: string;         // 최종 승인 전문가 식별자 (예: "K팀장")
  
  // 5대 표준 섹션 콘텐츠
  summary: string;                // [L1] 백과사전식 기본 정의
  purpose: string;                // [L1] 공정/소자 도입 목적
  principles: string[];           // [L2] 물리·화학적 메커니즘 리스트 (아코디언)
  limitations: string[];          // [L2] 미세화 물리 한계 및 결함 위험 리스트
  
  // 온톨로지 관계 그래프 (Graph Edges)
  relations: {
    is_a: Array<{ id: string; name: string }>;       // 상위 개념 (예: 식각 공정)
    part_of: Array<{ id: string; name: string }>;    // 하위 장비/부품 (예: RF 제너레이터)
    next_step: Array<{ id: string; name: string }>;  // 후속 단위 공정 (예: PR 애싱)
    
    // 🌟 [추가 1: 3.1 Clarifier 지원] 경쟁 대안 기술 경로 (Competing / Alternative Technologies)
    alternative_to?: Array<{
      targetId: string;       // 경쟁 대안 개념 ID (예: "tc-ncf")
      targetName: string;     // 대안 명칭 (예: "마이크론 TC-NCF")
      commonGoal: string;     // 공통 공학 과제 (예: "고단 HBM 방열 및 휨 제어")
      tensionNote: string;    // 인과적 대립축 (예: "액상 일괄 몰딩 vs 박형 필름 열압착")
    }>;

    // 🌟 [추가 2: 3.3 Advisor 지원] 극성(Polarity) 기반 인과 엣지 (Causal Relations)
    causalEdges?: Array<{
      targetId: string;       // 대상 물리량/결함/지표 ID (예: "micro-void", "fab-tat", "etch-rate")
      targetName: string;     // 대상 명칭
      polarity: "+" | "-";    // '+' = 원인 증가 시 결과 증가(비례), '-' = 원인 증가 시 결과 감소(반비례)
      relationType: "causes" | "caused_by" | "trade_off";
      mechanism?: string;     // 지배 물리·화학 메커니즘 공식/설명
    }>;
  };
  
  evidenceIds: string[];          // 귀속된 공인 출처 ID 목록 (["E-01", "E-02"])
}
```

---

### 2.2 `PerspectiveCase` (적응형 Level 3 실무 사례 엔티티)
- **역할**: [Tab 1] 위키 본문의 3번 섹션. 챔버 레시피, Q-Time, 소자 신뢰성, 패키징 물성 등 반도체 전 영역의 실무 조건을 유연하게 담아내는 도메인 독립적 카드 데이터.

```typescript
interface PerspectiveCase {
  id: string;                     // 관점 식별자 (예: "company-a-hbm", "domain-memory")
  conceptId: string;              // 소속 개념 ID
  label: string;                  // 탭 표시명 (예: "A사 HBM3E P-Line")
  description: string;            // 관점 배경 설명 (스티키 바 하단 노출)
  
  // 🌟 도메인 독립적 적응형 실무 카드 (Adaptive Level 3 Block)
  appliedCase: {
    caseTitle: string;            // 실무 사례 표제 (예: "HBM TSV HARC 식각 중 바닥 보이드 대응")
    code?: string;                // 관리 코드 (예: "ET-HARC-04", "JESD92", "QTIME-01" - 없으면 null)
    narrative: string;            // 실무 적용 맥락 설명 (왜 이 규칙/조건이 필요한지 2~3줄)
    
    // 핵심 적용 사양/기준 (유연한 Key-Value & 인라인 출처 연동)
    specifications: Array<{
      label: string;              // 항목명 (예: "본딩 가압력", "RF 소스 파워", "보이드율")
      value: string;              // 수치/조건 (예: "250N", "800W", "0.05%")
      
      // 🌟 [추가 1: 3.3 Advisor 지원] 반도체 제어공학 표준 인과 역할
      role?: "control_knob"       // 🎛️ 조작 변수(Manipulated Variable): 엔지니어가 직접 조절하는 공정 인자 (압력, 온도, 가스 유량 등)
           | "kpi_target"         // 🎯 제어/목표 변수(Controlled Variable): 무너지면 안 되는 품질 지표 (보이드율, 식각선택비, TAT 등)
           | "ambient_limit";     // 🛑 외란/제약 변수(Disturbance/Limit): 장비/팹 환경 불변 한계 (최대 파워, 배기압 등)
      
      // 🌟 [추가 2: 3.2 Comparison 지원] 다차원 비교 축 카테고리 매핑
      category?: "thermal" | "defects" | "fab" | "custom"; // 비교 축 분류 코드
      categoryLabel?: string;                               // 표기용 라벨 (예: "🔬 열·물성")
      
      evidenceId?: string;        // 특정 항목별 근거 출처 연동 (예: "E-03")
    }>;
    
    caution: string;              // ⚠️ 현장 제약 및 트레이드오프 주의사항
    evidenceId?: string;          // 대표 공인 출처 ID
  } | null;                       // default(공통 기본 지식) 관점일 경우 null
}
```

---

### 2.3 `ComparisonSession` (기술 대안 비교 세션 엔티티)
- **역할**: [Tab 2] 기술 대안 비교분석의 2단계 독립 화면, 세션 폴더/즐겨찾기, 3-Step 스냅샷 및 AI 파라미터 튜닝 상담 이력 보존.

```typescript
interface ComparisonSession {
  id: string;                     // 세션 고유 ID (예: "sess-20261016-001")
  userId: string;                 // 세션 소유 엔지니어 ID
  title: string;                  // 세션 제목 (예: "HBM3E 방열 대안: SK하이닉스 vs 마이크론")
  isPinned: boolean;              // ⭐ 즐겨찾기 고정 여부
  folderId?: string;              // 📁 소속 프로젝트 폴더 ID (미분류 시 null)
  
  // 조사 요청 전제 파라미터 (화면 2-A)
  query: string;                  // 초기 고민 질의 (예: "HBM 열 문제")
  contextParams: {
    targetA: string;              // 기준 대상 A (예: "SK하이닉스 (MR-MUF)")
    targetB: string;              // 대조 대상 B (예: "마이크론 (TC-NCF)")
    domain: string;               // 평가 도메인 (예: "첨단 패키징")
    releaseVersion: string;       // 기준 온톨로지 판본 (예: "2026.10")
    
    // 🌟 [추가 1: 3.1 Clarifier 지원] 현장 엔지니어의 라인 제약 조건 (초기 감지 또는 설정)
    constraints?: Array<{
      param: string;              // 제약 파라미터명 (예: "본딩 가압력", "RF 파워")
      operator: "<=" | ">=" | "==";
      limitValue: string;         // 한계 수치 (예: "150N", "600W")
      source: "user_prompt" | "fab_profile"; // 자연어 질의에서 추출되었는지 팹 프로필 기본값인지
    }>;
  };
  
  // 3-Step 스냅샷 타임라인 데이터 (화면 2-B)
  snapshots: [
    { step: 1; title: "공학 질문 확정"; branchData: any },
    { 
      step: 2; 
      title: "양산 조건 매핑"; 
      conditions: Record<string, any>;
      
      // 🌟 [추가 2: 3.2 Comparison 지원] 기준 레시피와 현장 제약 간 괴리 자동 감지
      constraintGaps?: Array<{
        param: string;            // 괴리 파라미터명 (예: "본딩 가압력")
        standardValue: string;    // 기준 레시피 수치 (예: "250N")
        constraintValue: string;  // 현장 한계 수치 (예: "150N")
        riskNote: string;         // 위험 요약 (예: "접촉 면적 부족으로 보이드 증가 위험")
      }>;

      // 🌟 [추가 3: 3.3 Advisor 지원] 인과 보상 튜닝 상담 이력
      tuningHistory?: Array<{
        userPrompt: string;       // "장비 한계로 가압력을 150N 이상 못 줄 때 어떻게 하지?"
        advisorRecommendation: {
          compensationA: any;     // 추천안 A (초음파 시간 보상 + TAT 트레이드오프)
          compensationB: any;     // 추천안 B (온도 보상 + Warpage 트레이드오프)
        };
      }>;
    },
    { 
      step: 3; 
      title: "다차원 비교 분석 완료"; 
      
      // 🌟 [추가 4: 3.2 Comparison 지원] 축 카테고리, 공인 출처, 지식 갭 영구 보존 매트릭스
      matrix: Array<{
        axis: string;             // 축 명칭 (예: "16단 고단 적층 시 휨 및 보이드")
        axisCategory?: "thermal" | "defects" | "fab" | "custom";
        categoryLabel?: string;   // 표기 라벨 (예: "⚠️ 결함·신뢰성")
        valA: string;             // 기준 대상 A 실측치
        valB: string;             // 대조 대상 B 실측치
        evidenceA?: string;       // 복원용 공인 출처 ID (예: "E-11")
        evidenceB?: string;       // 복원용 공인 출처 ID (예: "E-12")
        isGap?: boolean;          // 🌟 갭 여부 영구 보존 (true 시 ⚠️ 공인 데이터 미등록 태그 렌더링)
      }>;
      
      aiCausalNote: string;       // AI 종합 인과 분석 코멘트
      
      // 🌟 [추가 5: 3.2 Comparison 지원] 인과 체인 딥다이브 질의 이력 영구 보존
      deepDiveHistory?: Array<{
        query: string;            // 사용자가 던진 꼬리물기 질문
        causalPath: string[];     // ["가압력 누적", "CTE 미스매치", "전단응력", "다이 휨"]
        explanation: string;      // 물리 메커니즘 심층 해설
        timestamp: string;
      }>;
    }
  ];
  
  exportedReviewId?: string;      // 3번 검토 센터로 이관된 티켓 ID (연동 시)
  updatedAt: string;
}
```

---

### 2.4 `ReviewTicket` (검토·승인 거버넌스 티켓 엔티티)
- **역할**: [Tab 3] 검토·승인 센터의 2-Segment 탭(`대기 중` ⟷ `승인 완료 이력`), 2-Pane Diff 및 에디터, AI 보완 지시 이력 및 감사 불변성 보장.

```typescript
interface ReviewTicket {
  id: string;                     // 티켓 ID (예: "rev-20261016-001")
  conceptId: string;              // 대상 개념 ID
  conceptTitle: string;           // 대상 개념명
  reviewType: "신규 개념" | "관점 추가" | "파라미터 수정" | "외부 문헌 발굴";
  author: string;                 // 작성자 (엔지니어명 또는 "AI Contextual Studio", "조사 에이전트")
  status: "pending" | "approved" | "rejected"; // 🌟 pending ➔ 대기 중 탭, approved ➔ 승인 완료 이력 탭
  
  // 🌟 [추가 6: 거버넌스 역링크 지원] 출처 세션 및 유입 경로
  sourceSessionId?: string;       // 역링크용 비교 세션 ID (예: "sess-20261016-001")
  originType?: "comparison_studio" | "literature_search" | "manual_expert"; // 유입 경로
  
  // 2-Pane Diff 대조 데이터
  currentVersion: string;         // 기준 위키 판본 (예: "v1.2")
  currentContent: string;         // 좌측 Pane: 현재 위키 본문
  aiMergedDraft: string;          // 우측 Pane: AI 통합 반영 초안
  humanEdits?: string;            // 전문가가 직접 편집기로 수정한 텍스트 (저장 시)
  // 🌟 [추가 7: 3.4 Directive 지원] 정형 사양 및 온톨로지 관계 패치 페이로드
  structuredPatches?: {
    specsPatch?: Array<{ label: string; oldValue: string; newValue: string; role?: string }>;
    relationsPatch?: {
      addedEdges?: Array<{ targetId: string; relationType: string; polarity?: "+" | "-" }>;
      removedEdges?: string[];
    };
  };

  // 실시간 자동 무결성 점검 리포트
  integrityReport: {
    evidenceMatchRate: number;    // 출처 일치도 (예: 1.0 = 100%)
    hasOntologyConflict: boolean; // 온톨로지 충돌 여부 (false)
    impactScopeCount: number;     // 영향받는 연관 개념 수 (예: 1)
    validationDetails: string;
  };
  
  // 에이전트 초안 보완 지시 이력
  directiveHistory: Array<{
    directiveText: string;        // 사용자의 지시문
    targetLayer?: "prose" | "specs" | "relations" | "hybrid"; // 🌟 지시 대상 계층
    previousDraft: string;
    revisedDraft: string;
    timestamp: string;
  }>;
  
  approvedAt?: string;            // 승인 완료 일시 (ISO-8601)
  approvedBy?: string;            // 최종 승인자 ID
  publishedVersion?: string;      // 발행된 신규 판본 (예: "v1.3")
}
```

---

### 2.5 `EvidenceSource` (공식 출처 및 원문 근거 엔티티)
- **역할**: `[D-01]` 근거 드로어 및 [Tab 4] 외부 문헌 조사에서 공인 출처 신뢰성을 보증.

```typescript
interface EvidenceSource {
  id: string;                     // 출처 ID (예: "E-01", "src-intel-glass-2026")
  sourceName: string;             // 출처 명칭 (예: "Lam Research 극저온 공정 백서")
  sourceType: "official_whitepaper" | "standard" | "academic_tier3" | "internal_approved";
  publisher: string;              // 발행 기관 (Samsung, SK hynix, ASML, Lam, Intel, SEMI, IEEE 등)
  publishedDate: string;          // 발행 연월 (예: "2026.01")
  quote: string;                  // 공인 규격/백서 원문 인용문 전문
  externalUrl: string;            // DOI 또는 공식 웹페이지 URL
  urlLabel: string;               // 링크 버튼 라벨
  credibilityTier: "Tier 1 (공식 제조사)" | "Tier 2 (국제 표준)" | "Tier 3 (공인 학술)";
}
```

---

### 2.6 [아키텍처 당위성] 풍부한 도메인 모델(Aggregate)을 채택한 설계 이유

1. **RDB 3NF 대신 문서-그래프 모델을 택한 이유**:
   - 15~20개로 쪼개진 테이블의 복잡한 JOIN을 방지하여 LLM 프롬프트 조립 지연(Latency)을 0ms 수준으로 단축.
   - [정의 + 물리 메커니즘 + 한계 + 출처]가 하나의 일관된 덩어리(Cohesive Chunk)로 LLM에 공급되어 할루시네이션(환각)을 원천 차단.
2. **`PerspectiveCase`를 분리한 이유**:
   - 업계 공용 지식(`Concept`)과 프로젝트별 기밀/양산 조건(`PerspectiveCase`)의 수명 주기 및 보안 권한을 분리하여 불필요한 네트워크 트래픽 절감.
3. **`ComparisonSession`에 스냅샷 1~3을 통째로 보존하는 이유**:
   - 엔지니어링 분석의 **완벽한 재현성(Reproducibility)** 확보. AI의 비결정성(Non-deterministic)으로 인해 과거 분석 수치가 달라지는 치명적 문제 방지.
4. **`ReviewTicket`에 본문/초안/Diff를 불변 박제하는 이유**:
   - 반도체 지식 거버넌스의 **감사 추적(Audit Trail) 무결성** 보장. 향후 위키가 v1.4, v1.5로 판올림되더라도 과거 v1.2 승인 당시의 심사 배경과 Diff가 절대 깨지지 않음.

---

## 3. 2단계: AI 에이전트 & 인과 추론 파이프라인 아키텍처

### 3.1 대화형 질문 구체화 파이프라인 (Clarifier Engine)
- **동작 화면**: [Tab 2] 기술 대안 비교분석의 첫 화면 (화면 2-A: 조사·분석 요청실)
- **해결 목적**: 현장 엔지니어의 모호하고 현상 중심인 질의(예: "HBM 열 문제 어떻게 잡지?")를 온톨로지 인과 그래프를 기반으로 분석하여, 실제 엔지니어링 의사결정이 가능한 3대 공학 비교 분기 카드(Causal Tension Branches)로 구체화.
- **상세 처리 단계 (End-to-End)**:
  1. **온톨로지 엔티티 매핑 (Entity Extraction & Traversal)**:
     - `text-embedding-005`와 도메인 사전을 통해 사용자 질의에서 온톨로지 핵심 노드(예: HBM3E, 열저항, 본딩 방식) 추출 및 매핑.
     - **사용자 현장 제약 조건 파싱**: 초기 질문에 장비/라인 제약(예: "600W 이하 조건에서", "150N 제한")이 포함되어 있을 경우 이를 감지하여 `ComparisonSession.contextParams.constraints`에 즉시 구조화 바인딩.
  2. **경쟁 대안 엣지 및 인과적 긴장(Causal Tension) 분석**:
     - `Concept.relations.alternative_to` 엣지를 1차 조회하여 공통 목표(`commonGoal`)를 공유하는 검증된 대안 기술 쌍을 도출.
     - 매핑된 노드를 중심으로 그래프의 `causes`, `caused_by`, `trade_off` 관계 엣지를 2-hop까지 순회하여 상충하는 3대 기술 경로 도출.
  3. **구조화된 3대 분기 카드 JSON 생성**:
     - `recognizedIntent`, `branches[3]` (`branchId`, `title`, `description`, `targetA`, `targetB`, `domain`)의 고정 스키마 JSON 생성.
  4. **프론트엔드 자동 바인딩 및 화면 전환**:
     - 엔지니어가 분기 카드 클릭 시 `targetA`, `targetB`, `domain`, `constraints`가 세션에 자동 주입되며 즉시 [화면 2-B] 비교 결과 리포트로 전환.
- **예외 처리 및 가드레일 (Fallback)**:
  - 온톨로지 범위를 벗어난 질의(유사도 < 0.65): 도메인 특화 안내 메시지 반환.
  - 신공정 등 온톨로지 편측 결손: [Tab 4] Deep Research Engine과 연계하여 외부 공인 백서에서 대조군 후보 실시간 발굴.

### 3.2 다차원 기술 대안 비교 매트릭스 생성기 (Comparison Engine)
- **동작 화면**: [Tab 2] 화면 2-B (비교 결과 리포트)
- **해결 목적**: 대상 A와 B의 공통점과 차이점을 편향이나 추정치 없이 온톨로지 인과 그래프와 공인 출처에 기반해 대조하며, 고정된 축 대신 도메인/스케일에 맞는 **동적 적응형 비교 축(Dynamic Adaptive Axes)**을 제공하고, 출처 없는 데이터는 **환각 없이 지식 갭(Gap)으로 정직하게 격리**하며, 엔지니어의 **인과 체인 딥다이브(Causal Deep-Dive)** 꼬리물기 질의를 지원.
- **상세 처리 단계 (End-to-End)**:
  1. **서브그래프 정렬 및 동적 비교 축(Dynamic Adaptive Axes) 도출**:
     - 대상 A와 B의 `domainFacet`(소자, 공정, 운영, 소재) 및 `scaleLevel`(1~5)을 분석.
     - `PerspectiveCase.appliedCase.specifications`의 `category` 및 `role` 속성을 분석하여 해당 기술의 차별성을 가장 극명하게 가르는 3~5대 핵심 축을 동적으로 선택.
     - 엔지니어가 현장에서 주입한 사용자 정의 축(Custom Axis) 동적 추가 지원.
  2. **현장 제약 괴리(Constraint Gap) 자동 감지**:
     - 스냅샷 2(양산 조건 매핑) 로드 시, 기준 레시피와 세션 제약(`contextParams.constraints`)을 자동 대조하여 차이 발생 시 `ComparisonSession.snapshots[1].constraintGaps`에 기록하고 UI에 괴리 경고 배너 출력.
  3. **무환각 지식 갭 격리 및 스냅샷 불변 보존 (Zero-Hallucination Gap Isolation)**:
     - 매트릭스 셀 매핑 시 공인 출처(`evidenceId`)가 매핑되지 않은 항목은 **절대 임의의 숫자를 지어내지 않고(Zero-Fabrication) `isGap: true` 태그를 부착하여 공백 처리**.
     - 누락 항목 발생 시 상단에 **지식 갭 경고 배너**를 생성하고, [Tab 4] Deep Research Engine과 연동되는 탐색 쿼리(`query: "대상B + 누락항목"`)를 자동 생성하여 공인 백서 수집을 유도.
     - 최종 결과는 `ComparisonSession.snapshots[2].matrix`에 `evidenceA`, `evidenceB`, `isGap`, `axisCategory`를 포함하여 영구 보존.
  4. **AI 종합 인과 분석 코멘트 합성 (Causal Synthesis Note)**:
     - 온톨로지 상충 엣지(`trade_off`, `causes`)를 기반으로 한쪽 기술을 택했을 때의 이점과 물리적 한계 비용(트레이드오프 방정식)을 정밀 요약.
  5. **인과 체인 딥다이브 서브 파이프라인 (Causal Deep-Dive Sub-Engine)**:
     - 엔지니어가 결과 코멘트를 보고 "왜 16단에서 휨(Warpage)이 급증하나?" 같은 꼬리물기 질의 입력 시,
     - 온톨로지 인과 그래프의 3-hop 역방향/정방향 인과 경로(`가압력 누적 ➔ 열팽창계수 미스매치 ➔ 계면 전단응력 집중 ➔ 다이 휨 & 보이드`)를 그래프 순회로 추적.
     - 구조화된 `causalPath: string[]` 다이어그램 노드와 물리 화학적 메커니즘 해설을 즉시 스트리밍 반환하며, 이 질의 이력은 `ComparisonSession.snapshots[2].deepDiveHistory`에 자동 영구 보존.
  6. **거버넌스 연동 역링크 보장**:
     - 3번 검토 센터로 지식 제안 이관 시, 생성되는 `ReviewTicket`에 현재 `sourceSessionId: session.id`와 `originType: "comparison_studio"`를 주입하여 심사관의 원천 비교 맥락 역추적을 보장.

### 3.3 🌟 AI 파라미터 튜닝 상담 파이프라인 (Advisor Engine: 범용 인과 제약 보상 엔진)
- **동작 화면**: [Tab 2] 기술 대안 비교분석의 [스냅샷 2: 양산 조건 매핑] 및 `[M-04]` 파라미터 수정 모달
- **해결 목적**: 특정 공정에 국한되지 않고, 반도체 전 영역(단위공정, 설비, 팹 인프라, FDC 운영 등)에서 엔지니어가 겪는 장비·라인·환경의 물리적 제약($X \downarrow$)이 발생했을 때, 온톨로지 인과 엣지를 역방향으로 순회하여 **위험 노드($Y$)를 자동 감지하고, 이를 방어할 수 있는 보상 파라미터($Z$, Compensating Parameters)와 반작용(Trade-off)을 수식·인과 기반으로 역제안**.
- **인과 그래프 연산 메커니즘 (Causal Math & Traversal)**:
  $$\text{현장 제약 변수}(X \downarrow) \implies \text{위험 노드 감지}(Y \text{ 악화}) \implies \text{보상 파라미터 탐색}(\{Z_1, Z_2\} \text{ 보상}) \implies \text{트레이드오프 도출}(W_1, W_2)$$
  1. **현장 제약 변수($X$) 및 목표 지표($Y$) 파싱**:
     - 엔지니어의 자연어 질의 또는 1단계(Clarifier)에서 인계된 제약 컨텍스트(`sessionConstraints`)로부터 조작 불가 한계 변수($X \le \text{Limit}$)와 반드시 지켜야 할 품질 목표($Y_{\text{kpi}}$) 분리.
  2. **위험 노드 자동 감지 (Risk Node Detection)**:
     - 제약 변수 $X$에서 뻗어나가는 인과 엣지(`causalEdges`) 중 극성(Polarity)이 반비례(`'-'`)인 노드 자동 추적.
     - *예: 가압력($P \downarrow$) ➔ 보이드($\text{Void} \uparrow$), RF파워($W \downarrow$) ➔ 식각률($\text{ER} \downarrow$), 샘플링속도($f \downarrow$) ➔ 아킹미감지($\text{Miss} \uparrow$).*
  3. **보상 파라미터 탐색 (Compensating Parameters Finding)**:
     - 위험 노드 $Y$로 유입되는 다른 인과 엣지($Z \rightarrow Y$) 중 엔지니어가 조작 가능한 변수(`role: "control_knob"`) 역방향 탐색.
     - *예: 보이드를 낮추는 보상 파라미터 ➔ 초음파 시간($Z_1$), 스테이지 온도($Z_2$); 식각률을 올리는 보상 파라미터 ➔ $O_2$ 가스비율($Z_1$), 공정시간($Z_2$).*
  4. **트레이드오프(부작용) 도출 및 2~3대 레시피 세트 생성**:
     - 보상 파라미터($Z$)에서 뻗어나가는 2차 엣지($Z \xrightarrow{+} W$)를 추적하여 감수해야 할 공학적 비용 명시.
     - **[추천안 A]**: 제1 보상 파라미터 조정 + *TAT 또는 원가 트레이드오프 명시*.
     - **[추천안 B]**: 제2 보상 파라미터 조정 + *물리적 스트레스(Warpage, 로딩 등) 트레이드오프 명시*.
  5. **원클릭 자동 주입 및 스냅샷 3 매트릭스 재계산**:
     - 추천안 클릭 시 전제 수치 폼 자동 기입 및 0.8초 이내 비교 매트릭스 재추론 완료.
- **예외 처리 및 안전 가드레일 (Safety Margin & Physics Limits)**:
  - **공정 안전 마진(Process Window) 이탈 차단**: 온톨로지의 `ambient_limit` 및 `limitations` 임계치를 대조하여, 파괴선(예: 300℃ 초과 솔더 재용융, 플라즈마 아킹 한계 전압)을 벗어나는 보상값은 거절하고 `⚠️ 공정 안전 마진 위반` 경고와 함께 안전 범위 내로 바운딩(Bounding).

### 3.4 지식 무결성 검증 및 초안 재작성 파이프라인 (Directive Engine: 다중 계층 거버넌스 엔진)
- **동작 화면**: [Tab 3] 검토·승인 센터의 2-Pane Diff 화면 및 하단 보완 지시 바
- **해결 목적**: 전문가의 자연어 보완 지시(Directive)를 충실히 반영하되, 기존 공인 출처 원문 인용구와 온톨로지 무결성 가드레일을 100% 보존하고, 단순 비정형 텍스트뿐만 아니라 **정형 사양(Key-Value Specs)** 및 **온톨로지 관계망(Graph Relations)**까지 다중 계층(Multi-Target)으로 정밀 패치하며 실시간 3대 무결성 지표를 산출.
- **상세 처리 단계 (End-to-End)**:
  1. **지시 의도 분류 및 타깃 라우팅 (Directive Intent Classification)**:
     - 전문가 지시문을 분석하여 처리 계층을 4가지로 자동 라우팅:
       - `prose`: 본문 설명, 원리, 한계 등 Markdown 줄글 수정
       - `specs`: `PerspectiveCase.specifications`의 특정 파라미터 수치, 단위, 역할(`role`) 수정
       - `relations`: `Concept.relations`의 상하위(`is_a`), 경쟁 대안(`alternative_to`), 인과 엣지(`causalEdges`) 수정
       - `hybrid`: 본문과 정형 사양을 동시에 수정하는 복합 지시
  2. **불변 제약 앵커링 (Immutability Anchoring & Masking)**:
     - 현재 초안에 귀속된 공인 출처(`EvidenceSource.quote`)와 온톨로지 핵심 엣지를 '불변 블록'으로 마스킹(Lock).
     - 시스템 가드레일 프롬프트를 통해 출처 원문의 임의 왜곡·누락(Knowledge Drift)을 원천 차단.
  3. **다중 계층 제약 패치 생성 (Multi-Target Constrained Patching)**:
     - 줄글 수정 시에는 2-Pane 우측 초안(`aiMergedDraft`)을 정밀 패치.
     - 정형 데이터 수정 시에는 `ReviewTicket.structuredPatches` (`specsPatch`, `relationsPatch`)를 함께 생성하여 테이블과 그래프의 정합성을 동시 갱신.
  4. **3대 실시간 무결성 감사 지표 산출 (3-Pillar Integrity Audit)**:
     - **출처 일치도 (Evidence Match Rate)**: 신규 문장의 기술적 주장(Assertion)과 `EvidenceSource.quote` 간 NLI(함의/모순 검사) 수행 (100% 달성 목표).
     - **온톨로지 충돌 여부 (Ontology Conflict)**: 상하위 위계 및 인과 극성(`causalEdges`)과의 물리 법칙 모순 발생 여부 검사 (`충돌 없음`).
     - **영향 범위 (Impact Scope)**: 본 수정으로 인해 영향을 받는 downstream 온톨로지 개념 개수 산출 (`연관 개념 N건`).
  5. **2-Pane Git Diff 재계산 및 감사 이력 보존**:
     - 좌측(현재 위키 v1.2) vs 우측(AI 재작성 초안) 간 단어 단위 Git Diff 산출 및 시각적 하이라이트.
     - 지시문, 수정 전/후 초안, 타깃 계층을 `ReviewTicket.directiveHistory`에 영구 보존하여 완벽한 감사 추적(Audit Trail) 보장.
- **예외 처리 및 충돌 가드레일 (Conflict Guardrail)**:
  - **공인 출처 정면 충돌 감지**: 전문가 지시 내용이 공인 백서 실측치와 충돌할 경우, 출처 일치도를 강등하고 `⚠️ 경고: 입력하신 지시 내용이 공인 백서의 실측치와 정면 충돌합니다. 강제 반영하시려면 전문가 사유를 입력해야 합니다.` 확인 모달을 띄워 전문가가 사유를 반드시 남기도록 강제.

### 3.5 공인 문헌 교차 분석 및 초안 합성기 (Deep Research Engine)
- **동작 화면**: [Tab 4] 외부 문헌·백서 조사
- **로직 흐름**:
  1. 비공인 웹을 배제하고 5대 선도사 백서, SEMI 표준, IEEE 논문 풀 스캔.
  2. 핵심 실측 인용구 추출(화면 4-A) ➔ 종합 기술 브리핑 및 온톨로지 지식 후보 2~3건 카드 합성(화면 4-B).
  3. 원클릭으로 3번 검토 센터 큐에 등록.
