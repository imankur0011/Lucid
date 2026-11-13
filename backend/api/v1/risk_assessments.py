"""
Risk Assessment Questionnaire and Submission API endpoints.
Implements deterministic scoring rules and persistent versioned assessment history.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime, timezone

try:
    from backend.database import get_db
    from backend.models import (
        AppUser,
        RiskQuestion,
        RiskQuestionOption,
        RiskAssessment,
        RiskAssessmentAnswer,
    )
    from backend.auth.dependencies import get_current_user
    from backend.schemas import (
        RiskQuestionRead,
        RiskAssessmentSubmit,
        RiskAssessmentRead,
    )
except ImportError:
    from database import get_db
    from models import (
        AppUser,
        RiskQuestion,
        RiskQuestionOption,
        RiskAssessment,
        RiskAssessmentAnswer,
    )
    from auth.dependencies import get_current_user
    from schemas import (
        RiskQuestionRead,
        RiskAssessmentSubmit,
        RiskAssessmentRead,
    )

router = APIRouter(prefix="", tags=["Risk Assessment"])


def calculate_risk_scores(db: Session, answers: list) -> tuple[float, float, str]:
    """
    Deterministically computes risk tolerance, risk capacity, and overall risk category.
    Returns: (tolerance_score, capacity_score, risk_category)
    """
    total_weighted_score = 0.0
    total_weight = 0.0

    tolerance_sum = 0.0
    tolerance_weight = 0.0
    capacity_sum = 0.0
    capacity_weight = 0.0

    zero_emergency_fund = False
    short_horizon = False
    beginner_knowledge = False

    for ans in answers:
        if not ans.selected_option_id:
            continue
        opt = db.query(RiskQuestionOption).filter(RiskQuestionOption.option_id == ans.selected_option_id).first()
        if not opt or opt.score is None:
            continue

        q = db.query(RiskQuestion).filter(RiskQuestion.question_id == ans.question_id).first()
        if not q:
            continue

        scoring_cfg = q.scoring_config or {}
        weight = scoring_cfg.get("weight", 0.2)
        category = scoring_cfg.get("category", "tolerance")
        score = float(opt.score)

        q_code = (q.question_code or "").upper()
        if "EMERGENCY" in q_code and score <= 25.0:
            zero_emergency_fund = True
        if "HORIZON" in q_code and score <= 25.0:
            short_horizon = True
        if "KNOWLEDGE" in q_code and score <= 25.0:
            beginner_knowledge = True

        total_weighted_score += score * weight
        total_weight += weight

        if category == "capacity":
            capacity_sum += score * weight
            capacity_weight += weight
        else:
            tolerance_sum += score * weight
            tolerance_weight += weight

    overall_score = (total_weighted_score / total_weight) if total_weight > 0 else 50.0
    tolerance_score = (tolerance_sum / tolerance_weight) if tolerance_weight > 0 else overall_score
    capacity_score = (capacity_sum / capacity_weight) if capacity_weight > 0 else overall_score

    # Deterministic mapping to canonical 5-tier classification
    def _score_to_category(score: float) -> str:
        if score < 35.0:
            return "very_conservative"
        elif score < 50.0:
            return "conservative"
        elif score < 70.0:
            return "moderate"
        elif score < 85.0:
            return "growth"
        else:
            return "aggressive"

    tolerance_category = _score_to_category(tolerance_score)
    capacity_category = _score_to_category(capacity_score)

    CATEGORY_RANKS = {
        "very_conservative": 1,
        "conservative": 2,
        "moderate": 3,
        "growth": 4,
        "aggressive": 5,
    }
    RANK_TO_CATEGORY = {v: k for k, v in CATEGORY_RANKS.items()}

    # Fiduciary Suitability Policy (SEBI IA Master Circular Principle):
    # An investor's actionable risk posture cannot exceed their financial loss capacity.
    # final_category = min(tolerance_category, capacity_category)
    tol_rank = CATEGORY_RANKS[tolerance_category]
    cap_rank = CATEGORY_RANKS[capacity_category]

    # SEBI Fiduciary Constraint 1: Zero emergency fund strictly caps loss capacity to Conservative (Rank 2)
    if zero_emergency_fund:
        cap_rank = min(cap_rank, 2)
    # SEBI Fiduciary Constraint 2: Investment horizon < 1 year strictly caps loss capacity to Conservative (Rank 2)
    if short_horizon:
        cap_rank = min(cap_rank, 2)
    # SEBI Fiduciary Constraint 3: Beginner with no equity knowledge cannot be Aggressive (caps tolerance at Moderate, Rank 3)
    if beginner_knowledge:
        tol_rank = min(tol_rank, 3)

    final_rank = min(tol_rank, cap_rank)
    risk_category = RANK_TO_CATEGORY[final_rank]

    return round(tolerance_score, 2), round(capacity_score, 2), risk_category


@router.get("/risk-questions", response_model=List[RiskQuestionRead])
async def get_risk_questions(db: Session = Depends(get_db)):
    """Retrieve active risk questionnaire questions and options."""
    questions = (
        db.query(RiskQuestion)
        .filter(RiskQuestion.is_active == True)
        .order_by(RiskQuestion.display_order.asc())
        .all()
    )
    for q in questions:
        q.options.sort(key=lambda opt: opt.display_order)
    return questions


@router.post("/risk-assessments", response_model=RiskAssessmentRead, status_code=status.HTTP_201_CREATED)
async def submit_risk_assessment(
    payload: RiskAssessmentSubmit,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submits completed risk questionnaire answers, deterministically calculates
    risk scores & category, and persists the immutable assessment.
    """
    # Validate all questions belong to active questionnaire
    active_questions = {q.question_id: q for q in db.query(RiskQuestion).filter(RiskQuestion.is_active == True).all()}
    if not active_questions:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Risk questionnaire not configured in database",
        )

    for ans in payload.answers:
        if ans.question_id not in active_questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Question {ans.question_id} is not part of the active questionnaire",
            )
        if ans.selected_option_id:
            opt = (
                db.query(RiskQuestionOption)
                .filter(
                    RiskQuestionOption.option_id == ans.selected_option_id,
                    RiskQuestionOption.question_id == ans.question_id,
                )
                .first()
            )
            if not opt:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Option {ans.selected_option_id} does not belong to question {ans.question_id}",
                )

    # Compute scores deterministically
    tol_score, cap_score, category = calculate_risk_scores(db, payload.answers)
    now = datetime.now(timezone.utc)

    assessment = RiskAssessment(
        risk_assessment_id=uuid.uuid4(),
        user_id=current_user.user_id,
        questionnaire_version=payload.questionnaire_version or "demo-questionnaire-v1",
        assessment_status="completed",
        risk_tolerance_score=tol_score,
        risk_capacity_score=cap_score,
        risk_category=category,
        started_at=now,
        completed_at=now,
    )
    db.add(assessment)
    db.flush()

    # Save individual answers
    for ans in payload.answers:
        answer_rec = RiskAssessmentAnswer(
            answer_id=uuid.uuid4(),
            risk_assessment_id=assessment.risk_assessment_id,
            question_id=ans.question_id,
            selected_option_id=ans.selected_option_id,
            answer_text=ans.answer_text,
            answer_numeric=ans.answer_numeric,
            answer_boolean=ans.answer_boolean,
        )
        db.add(answer_rec)

    try:
        db.commit()
        db.refresh(assessment)
    except Exception:
        db.rollback()
        raise
    return assessment


@router.get("/risk-assessments/latest", response_model=Optional[RiskAssessmentRead])
async def get_latest_risk_assessment(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve the most recent completed risk assessment for the authenticated investor."""
    assessment = (
        db.query(RiskAssessment)
        .filter(
            RiskAssessment.user_id == current_user.user_id,
            RiskAssessment.assessment_status == "completed",
        )
        .order_by(RiskAssessment.completed_at.desc())
        .first()
    )
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed risk assessment found for this investor",
        )
    return assessment
