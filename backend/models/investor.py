"""
SQLAlchemy ORM models for Investor Profiles, Goals, and Risk Assessment Questionnaires.
"""

from sqlalchemy import (
    Column,
    String,
    CHAR,
    Boolean,
    Integer,
    SmallInteger,
    Numeric,
    Text,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    ForeignKeyConstraint,
    Index,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, Dict, Any, List
from datetime import datetime, date
import uuid

from backend.database.base import Base


class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    goal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="CASCADE"), nullable=False
    )
    goal_name: Mapped[str] = mapped_column(String(120), nullable=False)
    goal_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_amount: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    amount_already_saved: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False, default=0, server_default="0")
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="INR", server_default="INR")
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=3, server_default="3")
    goal_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", server_default="active")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("goal_id", "user_id", name="uq_financial_goals_id_user"),
        CheckConstraint("target_amount > 0", name="ck_financial_goals_target_amount"),
        CheckConstraint("amount_already_saved >= 0", name="ck_financial_goals_amount_saved"),
        CheckConstraint("priority BETWEEN 1 AND 5", name="ck_financial_goals_priority"),
        CheckConstraint(
            "goal_status IN ('active', 'paused', 'completed', 'cancelled')",
            name="ck_financial_goals_status",
        ),
        Index("ix_financial_goals_user_status", "user_id", "goal_status"),
    )

    user = relationship("AppUser", back_populates="goals")


class RiskQuestion(Base):
    __tablename__ = "risk_questions"

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    question_code: Mapped[str] = mapped_column(String(80), nullable=False)
    question_version: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_type: Mapped[str] = mapped_column(String(20), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    scoring_config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("question_version > 0", name="ck_risk_questions_version"),
        CheckConstraint(
            "answer_type IN ('single_choice', 'text', 'numeric', 'boolean')",
            name="ck_risk_questions_answer_type",
        ),
        UniqueConstraint("question_code", "question_version", name="uq_risk_question_version"),
        UniqueConstraint("question_id", "question_code", "question_version", name="uq_risk_question_id_code_version"),
    )

    options = relationship("RiskQuestionOption", back_populates="question", cascade="all, delete-orphan")
    answers = relationship("RiskAssessmentAnswer", back_populates="question")


class RiskQuestionOption(Base):
    __tablename__ = "risk_question_options"

    option_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risk_questions.question_id", ondelete="RESTRICT"), nullable=False
    )
    option_code: Mapped[str] = mapped_column(String(60), nullable=False)
    option_label: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Numeric(8, 3), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    __table_args__ = (
        UniqueConstraint("question_id", "option_code", name="uq_risk_option_code"),
        UniqueConstraint("option_id", "question_id", name="uq_risk_option_question"),
    )

    question = relationship("RiskQuestion", back_populates="options")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    risk_assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="CASCADE"), nullable=False
    )
    questionnaire_version: Mapped[str] = mapped_column(String(80), nullable=False)
    assessment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="in_progress", server_default="in_progress"
    )
    risk_tolerance_score: Mapped[Optional[float]] = mapped_column(Numeric(8, 3), nullable=True)
    risk_capacity_score: Mapped[Optional[float]] = mapped_column(Numeric(8, 3), nullable=True)
    risk_category: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("risk_assessment_id", "user_id", name="uq_risk_assessment_id_user"),
        CheckConstraint(
            "assessment_status IN ('in_progress', 'completed', 'superseded', 'cancelled')",
            name="ck_risk_assessment_status",
        ),
        CheckConstraint(
            "risk_category IS NULL OR risk_category IN ('very_conservative', 'conservative', 'moderate', 'growth', 'aggressive')",
            name="ck_risk_assessment_category",
        ),
        CheckConstraint("completed_at IS NULL OR completed_at >= started_at", name="ck_risk_assessment_dates"),
        CheckConstraint(
            "assessment_status <> 'completed' OR completed_at IS NOT NULL",
            name="ck_risk_assessment_completed",
        ),
        Index("ix_risk_assessments_user_date", "user_id", text("started_at DESC")),
        Index("ix_risk_assessments_status", "assessment_status"),
    )

    user = relationship("AppUser", back_populates="risk_assessments")
    answers = relationship("RiskAssessmentAnswer", back_populates="assessment", cascade="all, delete-orphan")


class RiskAssessmentAnswer(Base):
    __tablename__ = "risk_assessment_answers"

    answer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    risk_assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risk_assessments.risk_assessment_id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("risk_questions.question_id", ondelete="RESTRICT"), nullable=False
    )
    selected_option_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    answer_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    answer_numeric: Mapped[Optional[float]] = mapped_column(Numeric(18, 6), nullable=True)
    answer_boolean: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("risk_assessment_id", "question_id", name="uq_risk_answer_per_question"),
        ForeignKeyConstraint(
            ["selected_option_id", "question_id"],
            ["risk_question_options.option_id", "risk_question_options.question_id"],
            ondelete="RESTRICT",
            name="fk_risk_answer_option_question",
        ),
        Index("ix_risk_answers_assessment", "risk_assessment_id"),
    )

    assessment = relationship("RiskAssessment", back_populates="answers")
    question = relationship("RiskQuestion", back_populates="answers")
    selected_option = relationship(
        "RiskQuestionOption",
        foreign_keys=[selected_option_id],
        primaryjoin="RiskAssessmentAnswer.selected_option_id == RiskQuestionOption.option_id",
    )
