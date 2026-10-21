"""SQLAlchemy 2.0 ORM Entity Models.

Corresponds 1:1 with PostgreSQL 16 physical schema defined in backend/migrations/init.sql.
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    BigInteger,
    UniqueConstraint,
    JSON
)
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class EvidenceSourceModel(Base):
    __tablename__ = "evidence_sources"

    id = Column(String(64), primary_key=True)
    source_name = Column(String(256), nullable=False)
    source_type = Column(String(32), nullable=False)
    publisher = Column(String(64), nullable=False)
    published_date = Column(String(32), nullable=True)
    quote = Column(Text, nullable=False)
    section_context = Column(Text, nullable=True)
    relevance_score = Column(Numeric(3, 2), default=1.00)
    external_url = Column(Text, nullable=False)
    url_label = Column(String(128), nullable=False)
    credibility_tier = Column(String(64), nullable=False)
    referenced_concepts = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class ConceptModel(Base):
    __tablename__ = "concepts"

    id = Column(String(64), primary_key=True)
    title = Column(String(128), nullable=False)
    eng_name = Column(String(128), nullable=False)
    aliases = Column(JSON, default=list)
    domain_facet = Column(String(32), nullable=False)
    process_category = Column(String(64), nullable=False)
    scale_level = Column(Integer, nullable=False)
    scale_name = Column(String(64), nullable=True)
    version = Column(String(16), default="v1.2", nullable=False)
    status = Column(String(16), default="adopted", nullable=False)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    last_reviewed_by = Column(String(64), nullable=True)
    summary = Column(Text, nullable=False)
    purpose = Column(Text, nullable=False)
    principles = Column(JSON, default=list, nullable=False)
    limitations = Column(JSON, default=list, nullable=False)
    relations = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    perspectives = relationship("PerspectiveCaseModel", back_populates="concept", cascade="all, delete-orphan")


class CausalEdgeModel(Base):
    """🌟 온톨로지 인과 엣지 물리 테이블 (Neo4j 대체 및 단일화)."""
    __tablename__ = "causal_edges"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    source_concept_id = Column(String(64), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    target_concept_id = Column(String(64), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(String(32), nullable=False)
    polarity = Column(String(16), default="+")
    weight = Column(Numeric(3, 2), default=1.00)
    mechanism_label = Column(Text, nullable=False)
    
    # 🌟 도메인 필수 용어: 보상 파라미터 (Compensating Parameters)
    compensating_params = Column(JSON, nullable=True)
    
    evidence_id = Column(String(64), ForeignKey("evidence_sources.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("source_concept_id", "target_concept_id", "relation_type", name="uq_causal_edge"),
    )


class PerspectiveCaseModel(Base):
    __tablename__ = "perspective_cases"

    id = Column(String(64), primary_key=True)
    concept_id = Column(String(64), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    perspective_id = Column(String(32), nullable=False)
    perspective_title = Column(String(128), nullable=False)
    perspective_badge = Column(String(64), nullable=False)
    management_code = Column(String(64), nullable=True)
    context_narrative = Column(Text, nullable=False)
    specifications = Column(JSON, default=list, nullable=False)
    caution = Column(Text, nullable=False)
    evidence_id = Column(String(64), ForeignKey("evidence_sources.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    concept = relationship("ConceptModel", back_populates="perspectives")

    __table_args__ = (
        UniqueConstraint("concept_id", "perspective_id", name="uq_concept_perspective"),
    )


class ComparisonSessionModel(Base):
    __tablename__ = "comparison_sessions"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), nullable=False)
    title = Column(String(256), nullable=False)
    is_pinned = Column(Boolean, default=False)
    folder_id = Column(String(64), nullable=True)
    query = Column(Text, nullable=False)
    context_params = Column(JSON, default=dict, nullable=False)
    # 🌟 3-Step 스냅샷 내 deep_dive_history (꼬리질문) 및 tuning_history (보상 파라미터 튜닝) 영구 보존
    snapshots = Column(JSON, default=list, nullable=False)
    exported_review_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class ReviewTicketModel(Base):
    __tablename__ = "review_tickets"

    id = Column(String(64), primary_key=True)
    concept_id = Column(String(64), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    concept_title = Column(String(128), nullable=False)
    title = Column(String(256), nullable=False)
    review_type = Column(String(32), nullable=False)
    author = Column(String(64), nullable=False)
    department = Column(String(64), nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    status = Column(String(16), default="pending", nullable=False)
    source_session_id = Column(String(64), nullable=True)
    origin_type = Column(String(32), nullable=True)
    current_version = Column(String(16), default="v1.2", nullable=False)
    target_version = Column(String(16), default="v1.3", nullable=True)
    current_content = Column(Text, nullable=False)
    ai_merged_draft = Column(Text, nullable=False)
    human_edits = Column(Text, nullable=True)
    structured_patches = Column(JSON, nullable=True)
    integrity_report = Column(JSON, nullable=False)
    directive_history = Column(JSON, default=list, nullable=False)
    
    # 사유 / overrideReason
    override_reason = Column(Text, nullable=True)
    
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(64), nullable=True)
    applied_concept_version = Column(String(16), nullable=True)
    ticket_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    audit_id = Column(String(64), nullable=False)
    ticket_id = Column(String(64), nullable=False)
    concept_id = Column(String(64), nullable=False)
    action_type = Column(String(32), nullable=False)
    actor = Column(JSON, nullable=False)
    governance_snapshot = Column(JSON, nullable=False)
    previous_log_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False)
    digital_signature = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)


class ResearchSessionModel(Base):
    __tablename__ = "research_sessions"

    id = Column(String(64), primary_key=True)
    search_topic = Column(String(256), nullable=False)
    trust_pool_notice = Column(Text, nullable=True)
    scope_filters = Column(JSON, default=list, nullable=False)
    target_institutions = Column(JSON, default=list, nullable=False)
    evidence_feed = Column(JSON, default=list, nullable=False)
    synthesis_report = Column(JSON, default=dict, nullable=False)
    candidates = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# Section 7: Security Governance & RBAC Entities (사내 계정 및 L3 열람 신청)
# ---------------------------------------------------------------------------

class UserModel(Base):
    """사내 반도체 엔지니어 계정 마스터 테이블 (Section 7.1)."""
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)  # 사번 또는 고유식별자 (예: EMP-2026-001)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    name = Column(String(64), nullable=False)
    department = Column(String(64), nullable=False)
    role = Column(String(32), nullable=False, default="line_engineer")  # guest | line_engineer | chief_reviewer | admin
    level = Column(Integer, nullable=False, default=2)  # 1: guest, 2: line_engineer, 3: chief_reviewer, 4: admin
    is_active = Column(Boolean, nullable=False, default=True)  # Soft Delete 플래그 (WORM 감사 무결성 보존)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # 1:N 열람 신청 관계
    access_requests = relationship("AccessRequestModel", foreign_keys="AccessRequestModel.user_id", back_populates="user", cascade="all, delete-orphan")


class AccessRequestModel(Base):
    """Tier 3 대외비/L3 비인가 지식 열람 권한 신청 및 심사 테이블 (Section 7.1)."""
    __tablename__ = "access_requests"

    id = Column(String(64), primary_key=True)  # req-YYYYMMDD-xxxx
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id = Column(String(64), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_title = Column(String(128), nullable=False)  # WORM 감사 및 1ms 조회용 경량 역정규화
    reason = Column(Text, nullable=False)  # 열람 목적 상세 사유
    status = Column(String(16), nullable=False, default="pending", index=True)  # pending | approved | rejected | revoked
    reviewed_by = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_comment = Column(Text, nullable=True)  # 관리자 심사 의견/반려 사유
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # N:1 관계
    user = relationship("UserModel", foreign_keys=[user_id], back_populates="access_requests")
    reviewer = relationship("UserModel", foreign_keys=[reviewed_by])


