"""
SQLAlchemy ORM models for Users, Profiles, Preferences, and Consents.
"""

from sqlalchemy import (
    Column,
    String,
    CHAR,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from backend.database.base import Base


class AppUser(Base):
    __tablename__ = "app_users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    identity_provider: Mapped[str] = mapped_column(String(40), nullable=False, default="cognito", server_default="cognito")
    identity_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    account_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("identity_provider", "identity_subject", name="uq_app_users_identity"),
        CheckConstraint(
            "account_status IN ('pending', 'active', 'suspended', 'closed')",
            name="ck_app_users_status",
        ),
        Index("ix_app_users_status", "account_status"),
        Index("uq_app_users_email_lower", func.lower(email), unique=True, postgresql_where=text("email IS NOT NULL")),
    )

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    consents = relationship("UserConsent", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("FinancialGoal", back_populates="user", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="user", cascade="all, delete-orphan")
    portfolios = relationship("InvestorPortfolio", back_populates="user", cascade="all, delete-orphan")
    existing_portfolios = relationship("ExistingPortfolio", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("UserFeedback", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="CASCADE"), primary_key=True
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    country_code: Mapped[str] = mapped_column(CHAR(2), nullable=False, default="IN", server_default="IN")
    preferred_currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="INR", server_default="INR")
    investment_experience: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    investment_knowledge_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "investment_experience IN ('beginner', 'intermediate', 'experienced')",
            name="ck_user_profiles_experience",
        ),
        CheckConstraint(
            "investment_knowledge_level IN ('basic', 'intermediate', 'advanced')",
            name="ck_user_profiles_knowledge",
        ),
    )

    user = relationship("AppUser", back_populates="profile")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="CASCADE"), primary_key=True
    )
    preferred_language: Mapped[str] = mapped_column(String(12), nullable=False, default="en-IN", server_default="en-IN")
    timezone_name: Mapped[str] = mapped_column(String(80), nullable=False, default="Asia/Kolkata", server_default="Asia/Kolkata")
    email_notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    in_app_notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    user = relationship("AppUser", back_populates="preferences")


class UserConsent(Base):
    __tablename__ = "user_consents"

    consent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="CASCADE"), nullable=False
    )
    consent_type: Mapped[str] = mapped_column(String(60), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(80), nullable=False)
    consent_status: Mapped[str] = mapped_column(String(12), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    capture_source: Mapped[str] = mapped_column(String(40), nullable=False, default="application", server_default="application")
    evidence_reference: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    __table_args__ = (
        CheckConstraint("consent_status IN ('granted', 'withdrawn')", name="ck_user_consents_status"),
        Index("ix_user_consents_user_time", "user_id", text("recorded_at DESC")),
    )

    user = relationship("AppUser", back_populates="consents")
