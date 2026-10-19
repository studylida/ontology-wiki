# 🛠️ 반도체 인과 온톨로지 위키 백엔드 실서비스 안정화 및 계층화 점검 체크리스트

> **문서 목적**:  
> 백엔드 전반의 가짜 로직, 하드코딩 Mocking, 정적 폴백을 전면 제거하고,  
> 정통 **Controller(Router) ➔ Service ➔ Repository ➔ Entity** 아키텍처로 계층화하여 실제 DB(`ontology_wiki.db`) 데이터가 100% 흐르도록 보완하는 전수 점검표입니다.

---

## 🏛️ 아키텍처 계층 원칙

1. **Controller (Router)**: HTTP 요청 파싱, 권한 헤더(`X-User-Role`) 추출, DTO 유효성 검증, Service 호출, HTTP 상태 코드 반환만 담당 (DB 직접 쿼리 절대 금지).
2. **Service**: 순수 비즈니스 로직, AI 에이전트 인과 추론, 보안 마스킹 정책 적용, 트랜잭션 오케스트레이션.
3. **Repository**: SQLAlchemy 비동기 ORM(`AsyncSession`)을 통한 순수 DB 쿼리 전담. 데이터 부재 시 가짜 하드코딩 폴백 금지 (정직한 `None` 또는 빈 리스트 반환).
4. **Entity**: SQLite 물리 테이블과 1:1 매핑되는 SQLAlchemy ORM 모델.

---

## 📋 7대 도메인 41개 API 전수 점검 목록

### 1. 📖 온톨로지 개념 & 인과 그래프 (`Concepts & Causal Ontology`)
- **담당 엔티티**: `ConceptModel`, `PerspectiveCaseModel`, `CausalEdgeModel`
- **목표 레포지토리**: `backend/app/repositories/concept_repository.py`

| 상태 | 메서드 | 엔드포인트 경로 | 기능 요약 | 중점 보완 사항 |
| :---: | :---: | :--- | :--- | :--- |
| [ ] | `GET` | `/api/v1/concepts/tree` | 4축 계층 네비게이션 트리 조회 | 라우터 내 직접 쿼리 ➔ `ConceptRepository.get_tree_nodes()`로 이관 |
| [ ] | `GET` | `/api/v1/concepts/{concept_id}` | 개념 상세 본문, 원리/한계, 다도메인 관점 및 L3 마스킹 | DB Eager Loading 쿼리 분리, JSON `relations` 파편화 해소, 레벨별 보안 엔진 연결 |
| [ ] | `GET` | `/api/v1/concepts/{concept_id}/causal-subgraph` | 2-Hop 인과 서브그래프 및 보상 파라미터 | 라우터에 하드코딩된 Recursive CTE SQL ➔ `CausalRepository.get_2hop_subgraph()`로 분리 |
| [ ] | `GET` | `/api/v1/concepts/{concept_id}/contextual-explainer` | 용어 호버 시 0ms 인라인 문맥 해설 | 에이전트와 레포지토리 책임 분리, 인과 에지 기반 메커니즘 라벨 조회 표준화 |

---

### 2. 🤖 플로팅 엔지니어 챗봇 (`Floating Engineering Chatbot`)
- **담당 엔티티**: `ConceptModel`, `CausalEdgeModel`, `PerspectiveCaseModel`
- **목표 레포지토리**: `backend/app/repositories/causal_repository.py` / `chatbot_repository.py`
- **목표 서비스**: `backend/app/services/chatbot_service.py` (`clarifier_agent`)

| 상태 | 메서드 | 엔드포인트 경로 | 기능 요약 | 중점 보완 사항 |
| :---: | :---: | :--- | :--- | :--- |
| [ ] | `GET` | `/api/v1/chatbot/context` | 현재 열람 개념 기반 퀵 질문 칩 3종 서빙 | 라우터 내 `db.get` ➔ 레포지토리 메서드로 이관, ID 불일치 방어 |
| [ ] | `POST` | `/api/v1/chatbot/messages` | 지능형 3단 라우터 질의 (단답/인과역질문/화면이동) | **`clarifier_agent.py` L405 가짜 인과 노드 하드코딩 폴백 전면 제거**, 실제 DB 에지 기반 100% 동작 |
| [ ] | `POST` | `/api/v1/chatbot/messages/stream` | 실시간 SSE 토큰 스트리밍 | 토큰 스트림 제너레이터 내 DB 의존성 분리 및 안정화 |
| [ ] | `DELETE`| `/api/v1/chatbot/messages` | 챗봇 대화 이력 초기화 | 세션 초기화 로직 정돈 |

---

### 3. ✍️ 지식 거버넌스 & 검토 센터 (`Review & Governance`)
- **담당 엔티티**: `ReviewTicketModel`, `AuditLogModel`
- **목표 레포지토리**: `backend/app/repositories/review_repository.py`
- **목표 서비스**: `backend/app/services/review_service.py`

| 상태 | 메서드 | 엔드포인트 경로 | 기능 요약 | 중점 보완 사항 |
| :---: | :---: | :--- | :--- | :--- |
| [ ] | `GET` | `/api/v1/review-tickets` | 거버넌스 티켓 큐 목록 조회 | 라우터 직접 쿼리 ➔ 레포지토리 이관, 상태/도메인 필터 분리 |
| [ ] | `POST` | `/api/v1/review-tickets` | 위키 본문 간이 제안을 통한 티켓 신규 발행 | 티켓 발급 및 초기 머클 해시 생성 비즈니스 로직 분리 |
| [ ] | `GET` | `/api/v1/review-tickets/{ticket_id}` | 티켓 상세 (2분할 대조 편집 데이터) | 단건 조회 및 diff 모델 매핑 서비스화 |
| [ ] | `PUT` | `/api/v1/review-tickets/{ticket_id}/human-edits` | 전문가 직접 편집 실시간 저장 | 레포지토리 내 부분 업데이트(Partial Update) 메서드로 격리 |
| [ ] | `POST` | `/api/v1/review-tickets/{ticket_id}/directive` | 전문가 지시문 반영 AI 초안 재작성 | `directive_agent` 호출 및 중간 diff 갱신 |
| [ ] | `POST` | `/api/v1/review-tickets/{ticket_id}/presence` | 동시 편집 충돌 방지 Presence Lock | 60초 만료 락 관리 로직 캡슐화 |
| [ ] | `POST` | `/api/v1/review-tickets/{ticket_id}/approve` | 수석검토관 승인 집행 및 온톨로지 배포 | **고정된 `v1.3` 문자열 제거, 실제 온톨로지 배포 버전 동적 증가(`v1.4`, `v1.5`) 구현** |
| [ ] | `POST` | `/api/v1/review-tickets/{ticket_id}/reject` | 티켓 반려 처리 | 반려 사유 기록 및 상태 변경 트랜잭션 처리 |
| [ ] | `GET` | `/api/v1/review-tickets/{ticket_id}/wiki-preview` | 승인 전 반영될 위키 페이지 실시간 미리보기 | DB 원본과 수정본 가상 패치(Virtual Patch) 생성 |
| [ ] | `GET` | `/api/v1/review-tickets/{ticket_id}/audit-logs` | WORM 머클 감사 체인 이력 조회 | 감사 체인 전용 쿼리 레포지토리로 분리 |

---

### 4. ⚖️ 기술 대안 비교 분석 스튜디오 (`Comparison Studio`)
- **담당 엔티티**: `ComparisonSessionModel`, `ConceptModel`, `CausalEdgeModel`
- **목표 레포지토리**: `backend/app/repositories/comparison_repository.py`
- **목표 서비스**: `backend/app/services/comparison_service.py`

| 상태 | 메서드 | 엔드포인트 경로 | 기능 요약 | 중점 보완 사항 |
| :---: | :---: | :--- | :--- | :--- |
| [ ] | `POST` | `/api/v1/comparison/clarify` | 비교 질문 구체화 & 3대 분기 카드 도출 | `clarifier_agent` 질의어 매칭 로직과 DB 개념 조회 분리 |
| [ ] | `GET` | `/api/v1/comparison-sessions` | 비교 세션 목록 조회 | 인메모리/DB 혼재 정리 및 지속성(Persistence) 보장 |
| [ ] | `POST` | `/api/v1/comparison-sessions` | 신규 비교 세션 생성 | 세션 초기화 및 기본 비교 매트릭스 도출 분리 |
| [ ] | `GET` | `/api/v1/comparison-sessions/{session_id}` | 비교 세션 상세 조회 | 다차원 지표 매트릭스 및 꼬리질문 이력 조회 |
| [ ] | `PATCH` | `/api/v1/comparison-sessions/{session_id}` | 비교 세션 메타(제목, 핀, 폴더) 수정 | 레포지토리 업데이트 로직 정돈 |
| [ ] | `POST` | `/api/v1/comparison-sessions/{session_id}/matrix` | 매트릭스 필터링 및 동적 축 추가 | `comparison_agent` 다차원 매트릭스 계산 서비스화 |
| [ ] | `POST` | `/api/v1/comparison-sessions/{session_id}/deep-dive` | 꼬리질문 등록 및 4단계 인과 체인 기록 | 인과 그래프 탐색 및 체인 기록 로직 레포지토리 연계 |
| [ ] | `POST` | `/api/v1/comparison-sessions/{session_id}/tune-advisor` | AI 파라미터 튜닝 및 보상안 역제안 | `advisor_agent` 안전 마진/보상 파라미터 DB 연계 |
| [ ] | `POST` | `/api/v1/comparison-sessions/{session_id}/export-review`| 비교 결과 ➔ 검토 센터 티켓 발송 | 세션 데이터 기반 ReviewTicket 레포지토리 호출 |

---

### 5. 📑 외부 문헌 심층 조사 (`Deep Research`)
- **담당 엔티티**: `ResearchSessionModel`, `EvidenceSourceModel`
- **목표 레포지토리**: `backend/app/repositories/research_repository.py`
- **목표 서비스**: `backend/app/services/research_service.py`

| 상태 | 메서드 | 엔드포인트 경로 | 기능 요약 | 중점 보완 사항 |
| :---: | :---: | :--- | :--- | :--- |
| [ ] | `POST` | `/api/v1/research/clarify` | 문헌 조사 주제 구체화 | 범위(Scope) 필터 및 추천 질문 생성 분리 |
| [ ] | `POST` | `/api/v1/research/discover` | 공인 문헌 발굴 피드 생성 | Tier 1/2 공인 출처 DB 쿼리 및 발굴 결과 생성 |
| [ ] | `GET` | `/api/v1/research/sessions` | 과거 문헌 조사 로그 목록 조회 | 조사 세션 목록 조회 분리 |
| [ ] | `GET` | `/api/v1/research/sessions/{session_id}` | 조사 세션 상세 및 리포트 조회 | 단건 세션 상세 조회 분리 |
| [ ] | `POST` | `/api/v1/research/sessions/{session_id}/synthesize` | 발굴 문헌 종합 분석 리포트 생성 | AI 다중 출처 교차 분석 및 지식 후보 생성 |
| [ ] | `POST` | `/api/v1/research/candidates/{candidate_id}/export-ticket`| 지식 후보 ➔ 검토 센터 티켓 발송 | 지식 후보 기반 ReviewTicket 발행 연계 |

---

### 6. 🔍 검색 및 공인 출처 (`Search & Evidences`)
- **담당 엔티티**: `ConceptModel`, `EvidenceSourceModel`
- **목표 레포지토리**: `backend/app/repositories/search_repository.py`, `evidence_repository.py`

| 상태 | 메서드 | 엔드포인트 경로 | 기능 요약 | 중점 보완 사항 |
| :---: | :---: | :--- | :--- | :--- |
| [ ] | `GET` | `/api/v1/search/spotlight` | 전역 Cmd+K Spotlight 다축 검색 | 개념명, 영문명, 관리코드 DB 검색 쿼리 분리 |
| [ ] | `GET` | `/api/v1/evidences/{evidence_id}` | 공인 출처 원문 및 인용구 상세 조회 | `evidence_sources` 테이블 단건 조회 레포지토리 이관 |

---

### 7. ⚙️ 시스템 및 보안 거버넌스 (`System & Security`)
- **담당 엔티티**: `AuditLogModel`, `SystemVersionModel`
- **목표 레포지토리**: `backend/app/repositories/system_repository.py`

| 상태 | 메서드 | 엔드포인트 경로 | 기능 요약 | 중점 보완 사항 |
| :---: | :---: | :--- | :--- | :--- |
| [ ] | `GET` | `/api/v1/system/health` | 시스템 상태 및 DB/캐시 헬스체크 | DB 핑 및 Redis/인메모리 캐시 검증 분리 |
| [ ] | `GET` | `/api/v1/system/version` | 활성 온톨로지 엔진 버전 조회 | DB에 기록된 실시간 배포 버전 조회 |
| [ ] | `GET` | `/api/v1/system/audit/verify-integrity` | WORM 머클 트리 무결성 감사 | 전체 감사 체인의 SHA-256 머클 루트 검증 |
| [ ] | `POST` | `/api/v1/security/access-requests` | L3 절대 수치 열람 권한 신청 | 권한 요청 기록 처리 |
| [ ] | `GET` | `/api/v1/events/stream` | 실시간 배포 알림 SSE 스트림 | 전역 브로드캐스트 이벤트 스트림 |
| [ ] | `GET` | `/healthz` | K8s 루트 Liveness Probe | 루트 상태 체크 |

---

## 📈 작업 진행 현황판

- **전체 엔드포인트 수**: 41개
- **완료된 엔드포인트 수**: 0개
- **진행률**: 0.0%
- **현재 착수 목표**: **1단계 - 온톨로지 개념 & 인과 그래프 (4개)**
