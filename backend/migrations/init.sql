-- ==============================================================================
-- 반도체 공정·소자 인과 온톨로지 지식 위키 (Ontology Wiki)
-- PostgreSQL 16 물리 DDL 마이그레이션 스크립트
--
-- [설계 원칙 준수]
-- 1. 온톨로지 인과 그래프: causal_edges 테이블 + WITH RECURSIVE 초고속 탐색 단일화
-- 2. 도메인 필수 용어:
--    - 보상 파라미터 (Compensating Parameters) -> causal_edges.compensating_params
--    - 꼬리질문 -> comparison_sessions.snapshots 내 deep_dive_history
--    - 사유 / overrideReason -> review_tickets.override_reason (금지어: '전문가 사유' 엄금)
-- 3. 감사 로그: WORM(Write Once Read Many) 월별 파티셔닝 및 해시 무결성 보존
-- ==============================================================================

-- 0. 확장 기능 활성화 (UUID, pg_trgm 텍스트 검색 등)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ------------------------------------------------------------------------------
-- 1. 공인 출처 엔티티 (EvidenceSource)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evidence_sources (
    id VARCHAR(64) PRIMARY KEY,                             -- 출처 식별자 (예: 'E-01', 'E-2026-TGV-01')
    source_name VARCHAR(256) NOT NULL,                      -- 공인 출처 명칭 (예: 'Lam Research 극저온 공정 백서')
    source_type VARCHAR(32) NOT NULL,                       -- official_whitepaper, international_standard, academic_peer_reviewed, internal_approved
    publisher VARCHAR(64) NOT NULL,                         -- 발행 기관 (Samsung, SK hynix, ASML, Lam, Intel, SEMI, IEEE)
    published_date VARCHAR(32),                             -- 발행 연월 (예: '2026.01')
    quote TEXT NOT NULL,                                    -- 공인 규격/백서 원문 핵심 인용구 전문
    section_context TEXT,                                   -- 원문 상세 위치 (예: 'Section 4.2 Experimental Results, p.14')
    relevance_score NUMERIC(3, 2) DEFAULT 1.00,             -- 의미적 연관도 점수 (0.00 ~ 1.00)
    external_url TEXT NOT NULL,                             -- DOI 또는 공식 웹페이지 URL
    url_label VARCHAR(128) NOT NULL,                        -- 링크 버튼 라벨 (예: 'Lam Whitepaper 원문 ➔')
    credibility_tier VARCHAR(64) NOT NULL,                  -- Tier 1 (공식 제조사), Tier 2 (국제 표준), Tier 3 (공인 학술)
    referenced_concepts JSONB DEFAULT '[]'::jsonb,          -- 본 출처를 인용 중인 개념 목록 [{conceptId, name}]
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_publisher ON evidence_sources(publisher);
CREATE INDEX IF NOT EXISTS idx_evidence_tier ON evidence_sources(credibility_tier);

-- ------------------------------------------------------------------------------
-- 2. 온톨로지 핵심 개념 엔티티 (Concept)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS concepts (
    id VARCHAR(64) PRIMARY KEY,                             -- 불변 고유 식별자 (예: 'concept-tcb', 'concept-dry-etch')
    title VARCHAR(128) NOT NULL,                            -- 국문 공식 명칭 (예: '열압착 본딩')
    eng_name VARCHAR(128) NOT NULL,                         -- 영문 학술 명칭 (예: 'Thermal Compression Bonding')
    aliases TEXT[] DEFAULT '{}',                            -- 현장 약어 및 별칭 (예: ['TCB', '열압착'])
    domain_facet VARCHAR(32) NOT NULL,                      -- device, unit_process, operations, materials_infra
    process_category VARCHAR(64) NOT NULL,                  -- 단위 카테고리 (예: '첨단 패키징', '식각 공정')
    scale_level INTEGER NOT NULL CHECK (scale_level BETWEEN 1 AND 5), -- 1(<1nm) ~ 5(팹 인프라 1km)
    scale_name VARCHAR(64),                                 -- 물리 규모 표기명 (예: 'L3 단위 공정')
    version VARCHAR(16) NOT NULL DEFAULT 'v1.2',             -- 현재 공식 판본
    status VARCHAR(16) NOT NULL DEFAULT 'adopted'           -- adopted, in_review, deprecated
        CHECK (status IN ('adopted', 'in_review', 'deprecated')),
    last_reviewed_at TIMESTAMPTZ,                           -- 최종 승인 일시
    last_reviewed_by VARCHAR(64),                           -- 최종 승인 전문가 식별자
    summary TEXT NOT NULL,                                  -- [L1] 백과사전식 기본 정의
    purpose TEXT NOT NULL,                                  -- [L1] 도입 목적
    principles JSONB NOT NULL DEFAULT '[]'::jsonb,          -- [L2] 물리·화학적 메커니즘 단계 [{step, title, content, formula}]
    limitations JSONB NOT NULL DEFAULT '[]'::jsonb,         -- [L2] 물리 한계 및 트레이드오프 [{title, description, evidenceIds}]
    relations JSONB NOT NULL DEFAULT '{}'::jsonb,           -- 온톨로지 관계 캐시 {is_a: [], part_of: [], next_step: [], alternative_to: []}
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_concepts_domain ON concepts(domain_facet, process_category);
CREATE INDEX IF NOT EXISTS idx_concepts_scale ON concepts(scale_level);
CREATE INDEX IF NOT EXISTS idx_concepts_status ON concepts(status, version);
CREATE INDEX IF NOT EXISTS idx_concepts_title_trgm ON concepts USING gin (title gin_trgm_ops);

-- ------------------------------------------------------------------------------
-- 3. 온톨로지 인과 엣지 물리 테이블 (CausalEdge)
--    (Neo4j를 완전히 대체하여 1~2 hop WITH RECURSIVE 초고속 인과 탐색 전담)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS causal_edges (
    id BIGSERIAL PRIMARY KEY,
    source_concept_id VARCHAR(64) NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    target_concept_id VARCHAR(64) NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    relation_type VARCHAR(32) NOT NULL,                     -- causes, caused_by, trade_off, part_of, alternative_to, causes_defect
    polarity VARCHAR(16) DEFAULT '+',                       -- +, -, tradeoff
    weight NUMERIC(3, 2) DEFAULT 1.00,                      -- 인과 강도 (0.00 ~ 1.00)
    mechanism_label TEXT NOT NULL,                          -- 물리 메커니즘 해설 (예: '180N 초과 가압 시 NCF 수지 측방 유출 유발')
    compensating_params JSONB,                              -- 🌟 도메인 필수: 보상 파라미터 (Compensating Parameters)
                                                            -- 구조: { parameter: string, compensationFormula: string, tradeoffCost: string }
    evidence_id VARCHAR(64) REFERENCES evidence_sources(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_causal_edge UNIQUE (source_concept_id, target_concept_id, relation_type)
);

-- 1~2 hop 양방향 인과 탐색 최적화 복합 인덱스
CREATE INDEX IF NOT EXISTS idx_causal_edges_source ON causal_edges(source_concept_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_causal_edges_target ON causal_edges(target_concept_id, relation_type);

-- 🌟 보상 파라미터 JSONB 고속 검색용 GIN 인덱스
CREATE INDEX IF NOT EXISTS idx_causal_edges_gin_params ON causal_edges USING gin(compensating_params);

-- ------------------------------------------------------------------------------
-- 4. 적응형 Level 3 실무 사례 엔티티 (PerspectiveCase)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS perspective_cases (
    id VARCHAR(64) PRIMARY KEY,                             -- 실무 사례 고유 식별자 (예: 'case-tcb-hbm3e')
    concept_id VARCHAR(64) NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    perspective_id VARCHAR(32) NOT NULL,                    -- 관점 식별자 (예: 'hbm3e_advanced', 'dram_process')
    perspective_title VARCHAR(128) NOT NULL,                -- 실무 사례 표제 (예: 'A사 HBM3E 16단 TCB 본딩 양산 기준')
    perspective_badge VARCHAR(64) NOT NULL,                 -- UI 표시 배지 (예: '양산 적용 관점')
    management_code VARCHAR(64),                            -- 사내 관리 코드 (사내 레시피 ID, JEDEC 규격 등)
    context_narrative TEXT NOT NULL,                        -- 실무 적용 맥락 배경 서술 (2~3줄)
    specifications JSONB NOT NULL DEFAULT '[]'::jsonb,      -- 핵심 적용 기준 [{label, value, unit, criteria, role, evidenceId}]
    caution TEXT NOT NULL,                                  -- ⚠️ 현장 제약 및 트레이드오프 주의사항
    evidence_id VARCHAR(64) REFERENCES evidence_sources(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_concept_perspective UNIQUE (concept_id, perspective_id)
);

CREATE INDEX IF NOT EXISTS idx_perspective_concept ON perspective_cases(concept_id, perspective_id);

-- ------------------------------------------------------------------------------
-- 5. 기술 대안 비교 세션 엔티티 (ComparisonSession)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comparison_sessions (
    id VARCHAR(64) PRIMARY KEY,                             -- 세션 고유 ID (예: 'sess-20261016-001')
    user_id VARCHAR(64) NOT NULL,                           -- 소유 엔지니어 ID
    title VARCHAR(256) NOT NULL,                            -- 세션 제목
    is_pinned BOOLEAN DEFAULT FALSE,                        -- ⭐ 즐겨찾기 고정 여부
    folder_id VARCHAR(64),                                  -- 소속 프로젝트 폴더 ID
    query TEXT NOT NULL,                                    -- 초기 고민 질의
    context_params JSONB NOT NULL DEFAULT '{}'::jsonb,      -- {targetA, targetB, domain, releaseVersion, constraints: []}
    snapshots JSONB NOT NULL DEFAULT '[]'::jsonb,           -- 3-Step 스냅샷 (Step 1~3, 꼬리질문 이력 deep_dive_history,
                                                            -- 보상 파라미터 튜닝 상담 이력 tuning_history 영구 보존)
    exported_review_id VARCHAR(64),                         -- 검토 센터 이관 티켓 ID
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_comparison_user ON comparison_sessions(user_id, is_pinned);

-- ------------------------------------------------------------------------------
-- 6. 지식 거버넌스 및 검토·승인 티켓 엔티티 (ReviewTicket)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS review_tickets (
    id VARCHAR(64) PRIMARY KEY,                             -- 티켓 고유 ID (예: 'rev-20261016-001')
    concept_id VARCHAR(64) NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    concept_title VARCHAR(128) NOT NULL,                    -- 대상 개념명
    title VARCHAR(256) NOT NULL,                            -- 안건 제목
    review_type VARCHAR(32) NOT NULL,                       -- 신규 개념, 관점 추가, 파라미터 수정, 외부 문헌 발굴
    author VARCHAR(64) NOT NULL,                            -- 제출자 (엔지니어명 또는 AI 시스템)
    department VARCHAR(64),                                 -- 소속 부서
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(16) NOT NULL DEFAULT 'pending'           -- 🌟 pending(대기 중 탭) / approved(승인 완료 이력 탭) / rejected
        CHECK (status IN ('pending', 'approved', 'rejected')),
    source_session_id VARCHAR(64),                          -- 원본 비교/조사 세션 역링크
    origin_type VARCHAR(32),                                -- comparison_studio, literature_search, manual_expert
    current_version VARCHAR(16) NOT NULL,                   -- 기준 판본 (예: 'v1.2')
    target_version VARCHAR(16),                             -- 배포 예정 판본 (예: 'v1.3')
    current_content TEXT NOT NULL,                          -- 좌측 Pane 원문 본문
    ai_merged_draft TEXT NOT NULL,                          -- 우측 Pane AI 통합 반영 초안
    human_edits TEXT,                                       -- 전문가 편집기 수정문 (수정 시)
    structured_patches JSONB,                               -- 사양/관계 패치 페이로드 {specsPatch: [], relationsPatch: {}}
    integrity_report JSONB NOT NULL,                        -- 무결성 점검 {evidenceMatchRate, hasOntologyConflict, impactScopeCount, conflictDetails}
    directive_history JSONB NOT NULL DEFAULT '[]'::jsonb,   -- 에이전트 보완 지시 이력
    override_reason TEXT,                                   -- 🌟 도메인 필수: 사유 / overrideReason (금지어 '전문가 사유' 엄금)
    approved_at TIMESTAMPTZ,                                -- 승인 일시
    approved_by VARCHAR(64),                                -- 최종 승인자
    applied_concept_version VARCHAR(16),                    -- 발행된 최종 판본
    ticket_version INTEGER NOT NULL DEFAULT 1,              -- 낙관적 동시성 제어 버전 번호 (CAS 검증용)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_review_tickets_status ON review_tickets(status, submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_review_tickets_concept ON review_tickets(concept_id);

-- ------------------------------------------------------------------------------
-- 7. WORM(Write Once, Read Many) 불변 감사 로그 테이블 (AuditLogEntry)
--    (월별 파티셔닝 적용, UPDATE/DELETE 방지)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL,
    audit_id VARCHAR(64) NOT NULL,                          -- 감사 로그 식별자 (예: 'aud-20261019-tcb-001')
    ticket_id VARCHAR(64) NOT NULL,                         -- 승인 처리된 티켓 ID
    concept_id VARCHAR(64) NOT NULL,                        -- 대상 개념 ID
    action_type VARCHAR(32) NOT NULL,                       -- TICKET_APPROVED, TICKET_REJECTED, DIRECTIVE_OVERRIDE
    actor JSONB NOT NULL,                                   -- 행위자 정보 {userId, userName, department, ipAddress, role}
    governance_snapshot JSONB NOT NULL,                     -- 스냅샷 불변 정보 {previousVersion, publishedVersion, overrideReason, diffPatch}
    previous_log_hash VARCHAR(64) NOT NULL,                 -- 직전 로그 SHA-256 해시 (해시 체이닝)
    entry_hash VARCHAR(64) NOT NULL,                        -- 현재 레코드 머클 해시
    digital_signature TEXT,                                 -- 감사 서버 전자 서명
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- 월별 파티션 테이블 사전 생성 (2026년 10월, 11월, 12월 및 기본 파티션)
CREATE TABLE IF NOT EXISTS audit_logs_y2026m10 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-10-01 00:00:00+00') TO ('2026-11-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS audit_logs_y2026m11 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-11-01 00:00:00+00') TO ('2026-12-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS audit_logs_y2026m12 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-12-01 00:00:00+00') TO ('2027-01-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS audit_logs_default PARTITION OF audit_logs DEFAULT;

CREATE INDEX IF NOT EXISTS idx_audit_logs_ticket ON audit_logs(ticket_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_concept ON audit_logs(concept_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);

-- ------------------------------------------------------------------------------
-- 8. 갱신 일시(updated_at) 자동 갱신 트리거 함수
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_updated_at_concepts ON concepts;
CREATE TRIGGER set_updated_at_concepts
BEFORE UPDATE ON concepts
FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at_causal_edges ON causal_edges;
CREATE TRIGGER set_updated_at_causal_edges
BEFORE UPDATE ON causal_edges
FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at_perspective_cases ON perspective_cases;
CREATE TRIGGER set_updated_at_perspective_cases
BEFORE UPDATE ON perspective_cases
FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at_review_tickets ON review_tickets;
CREATE TRIGGER set_updated_at_review_tickets
BEFORE UPDATE ON review_tickets
FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
