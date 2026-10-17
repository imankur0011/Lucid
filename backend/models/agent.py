"""
SQLAlchemy ORM models for Agent Definitions, Agent Runs, Knowledge Documents, Feedback, Notifications, and Audit Events.
"""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    BigInteger,
    SmallInteger,
    Text,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from backend.database.base import Base


class AgentDefinition(Base):
    __tablename__ = "agent_definitions"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    agent_code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    agent_name: Mapped[str] = mapped_column(String(160), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    versions = relationship("AgentVersion", back_populates="agent")


class AgentVersion(Base):
    __tablename__ = "agent_versions"

    agent_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_definitions.agent_id", ondelete="RESTRICT"), nullable=False
    )
    version_label: Mapped[str] = mapped_column(String(80), nullable=False)
    llm_provider: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    prompt_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    structured_output_schema_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("agent_id", "version_label", name="uq_agent_version"),
    )

    agent = relationship("AgentDefinition", back_populates="versions")
    execution_runs = relationship("AgentExecutionRun", back_populates="agent_version")


class AgentExecutionRun(Base):
    __tablename__ = "agent_execution_runs"

    agent_execution_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    generation_request_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_generation_requests.generation_request_id", ondelete="RESTRICT"), nullable=True
    )
    portfolio_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_versions.portfolio_version_id", ondelete="RESTRICT"), nullable=True
    )
    agent_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_versions.agent_version_id", ondelete="RESTRICT"), nullable=False
    )
    execution_status: Mapped[str] = mapped_column(String(20), nullable=False)
    input_fingerprint: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    output_summary: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    input_token_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    output_token_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "execution_status IN ('queued', 'running', 'succeeded', 'failed', 'skipped')",
            name="ck_agent_runs_status",
        ),
        CheckConstraint("input_token_count IS NULL OR input_token_count >= 0", name="ck_agent_runs_in_tokens"),
        CheckConstraint("output_token_count IS NULL OR output_token_count >= 0", name="ck_agent_runs_out_tokens"),
        CheckConstraint("latency_ms IS NULL OR latency_ms >= 0", name="ck_agent_runs_latency"),
        CheckConstraint("completed_at IS NULL OR completed_at >= started_at", name="ck_agent_runs_dates"),
        Index("ix_agent_runs_request", "generation_request_id", text("started_at DESC")),
        Index("ix_agent_runs_version", "portfolio_version_id", text("started_at DESC")),
        Index("ix_agent_runs_status_time", "execution_status", text("started_at DESC")),
    )

    agent_version = relationship("AgentVersion", back_populates="execution_runs")
    generation_request = relationship("PortfolioGenerationRequest")
    portfolio_version = relationship("PortfolioVersion")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    knowledge_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    data_source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.data_source_id", ondelete="RESTRICT"), nullable=True
    )
    external_document_id: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    document_title: Mapped[str] = mapped_column(String(300), nullable=False)
    document_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    object_storage_uri: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding_model: Mapped[str] = mapped_column(String(160), nullable=False)
    vector_index_reference: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    index_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("content_hash", "embedding_model", name="uq_knowledge_document_embedding"),
        CheckConstraint("index_status IN ('pending', 'indexed', 'failed', 'retired')", name="ck_knowledge_docs_status"),
        Index("ix_knowledge_documents_status", "index_status", text("created_at DESC")),
    )

    data_source = relationship("DataSource")


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    user_feedback_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="CASCADE"), nullable=False
    )
    portfolio_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_versions.portfolio_version_id", ondelete="RESTRICT"), nullable=True
    )
    feedback_type: Mapped[str] = mapped_column(String(30), nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "feedback_type IN ('recommendation', 'explanation', 'application', 'other')",
            name="ck_user_feedback_type",
        ),
        CheckConstraint("rating IS NULL OR rating BETWEEN 1 AND 5", name="ck_user_feedback_rating"),
        Index("ix_user_feedback_user_time", "user_id", text("created_at DESC")),
    )

    user = relationship("AppUser", back_populates="feedback")
    portfolio_version = relationship("PortfolioVersion")


class Notification(Base):
    __tablename__ = "notifications"

    notification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="CASCADE"), nullable=False
    )
    notification_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    delivery_channel: Mapped[str] = mapped_column(
        String(20), nullable=False, default="in_app", server_default="in_app"
    )
    delivery_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    __table_args__ = (
        CheckConstraint("delivery_channel IN ('in_app', 'email', 'sms', 'push')", name="ck_notifications_channel"),
        CheckConstraint("delivery_status IN ('pending', 'sent', 'failed')", name="ck_notifications_status"),
        CheckConstraint("sent_at IS NULL OR sent_at >= created_at", name="ck_notifications_sent_dates"),
        CheckConstraint("read_at IS NULL OR read_at >= created_at", name="ck_notifications_read_dates"),
        CheckConstraint("dismissed_at IS NULL OR dismissed_at >= created_at", name="ck_notifications_dismiss_dates"),
        Index("ix_notifications_user_status_time", "user_id", "delivery_status", text("created_at DESC")),
    )

    user = relationship("AppUser", back_populates="notifications")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    audit_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="SET NULL"), nullable=True
    )
    action_code: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    outcome: Mapped[str] = mapped_column(
        String(20), nullable=False, default="success", server_default="success"
    )
    request_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("outcome IN ('success', 'failure', 'denied')", name="ck_audit_events_outcome"),
        Index("ix_audit_resource_time", "resource_type", "resource_id", text("created_at DESC")),
        Index("ix_audit_actor_time", "actor_user_id", text("created_at DESC")),
    )

    actor_user = relationship("AppUser")
