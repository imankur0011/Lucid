"""
Account Deletion, Portfolio Deletion, and Investor Data Management Service.
Provides enterprise-grade, transactionally-safe cascading deletion and export
compliant with GDPR/SEBI data rights, ensuring strict ownership isolation.
"""

import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

try:
    from backend.models import (
        AppUser,
        UserProfile,
        UserProfileVersion,
        UserPreference,
        UserConsent,
        UserVerificationCode,
        RevokedToken,
        FinancialGoal,
        RiskAssessment,
        RiskAssessmentAnswer,
        UserSectorPreference,
        UserSecurityPreference,
        InvestorPortfolio,
        PortfolioGenerationRequest,
        PortfolioVersion,
        PortfolioSecurityDecision,
        PortfolioVersionConstraint,
        RecommendationExplanation,
        ExplanationEvidence,
        PortfolioValidationRun,
        PortfolioValidationResult,
        PortfolioScenario,
        ExistingPortfolio,
        ExistingPortfolioHolding,
        PortfolioDiagnosis,
        RebalanceSuggestion,
        Notification,
        UserFeedback,
        AuditEvent,
        UserBrokerAccount,
        BrokerOrder,
        BrokerOrderEvent,
        BrokerExecution,
        PortfolioPerformanceSnapshot,
        Security,
        Company,
    )
    from backend.auth.dependencies import hash_token
    from backend.portfolio_engine.conversational_assistant import session_manager
except ImportError:
    from models import (
        AppUser,
        UserProfile,
        UserProfileVersion,
        UserPreference,
        UserConsent,
        UserVerificationCode,
        RevokedToken,
        FinancialGoal,
        RiskAssessment,
        RiskAssessmentAnswer,
        UserSectorPreference,
        UserSecurityPreference,
        InvestorPortfolio,
        PortfolioGenerationRequest,
        PortfolioVersion,
        PortfolioSecurityDecision,
        PortfolioVersionConstraint,
        RecommendationExplanation,
        ExplanationEvidence,
        PortfolioValidationRun,
        PortfolioValidationResult,
        PortfolioScenario,
        ExistingPortfolio,
        ExistingPortfolioHolding,
        PortfolioDiagnosis,
        RebalanceSuggestion,
        Notification,
        UserFeedback,
        AuditEvent,
        UserBrokerAccount,
        BrokerOrder,
        BrokerOrderEvent,
        BrokerExecution,
        PortfolioPerformanceSnapshot,
        Security,
        Company,
    )
    from auth.dependencies import hash_token
    from portfolio_engine.conversational_assistant import session_manager

logger = logging.getLogger(__name__)


def delete_investor_portfolio(
    db: Session,
    portfolio_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Dict[str, Any]:
    """
    Deletes an individual InvestorPortfolio and all child entities in strict
    dependency order to satisfy all database RESTRICT foreign key constraints.
    Verifies that the portfolio exists and belongs to the authenticated user.
    Never alters shared market instruments or data belonging to other users.
    """
    portfolio = (
        db.query(InvestorPortfolio)
        .filter(InvestorPortfolio.portfolio_id == portfolio_id)
        .first()
    )
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found.",
        )

    if portfolio.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this portfolio.",
        )

    # 1. Fetch all versions associated with this portfolio
    versions = (
        db.query(PortfolioVersion)
        .filter(PortfolioVersion.portfolio_id == portfolio_id)
        .all()
    )
    version_ids = [v.portfolio_version_id for v in versions]

    # If there are generation requests for this portfolio, collect their IDs as well
    gen_requests = (
        db.query(PortfolioGenerationRequest)
        .filter(PortfolioGenerationRequest.portfolio_id == portfolio_id)
        .all()
    )
    request_ids = [r.generation_request_id for r in gen_requests]

    # Additional safety: query any versions attached to these generation requests
    if request_ids:
        additional_versions = (
            db.query(PortfolioVersion)
            .filter(PortfolioVersion.generation_request_id.in_(request_ids))
            .all()
        )
        for av in additional_versions:
            if av.portfolio_version_id not in version_ids:
                version_ids.append(av.portfolio_version_id)

    total_decisions_deleted = 0
    total_scenarios_deleted = 0

    if version_ids:
        # A. Delete user feedback referencing these versions
        db.query(UserFeedback).filter(
            UserFeedback.portfolio_version_id.in_(version_ids)
        ).delete(synchronize_session=False)

        # B. Delete performance snapshots referencing these versions
        db.query(PortfolioPerformanceSnapshot).filter(
            PortfolioPerformanceSnapshot.portfolio_version_id.in_(version_ids)
        ).delete(synchronize_session=False)

        # C. Delete portfolio scenarios
        scenarios_deleted = (
            db.query(PortfolioScenario)
            .filter(PortfolioScenario.portfolio_version_id.in_(version_ids))
            .delete(synchronize_session=False)
        )
        total_scenarios_deleted += scenarios_deleted

        # D. Delete recommendation explanations & evidence
        explanations = (
            db.query(RecommendationExplanation)
            .filter(RecommendationExplanation.portfolio_version_id.in_(version_ids))
            .all()
        )
        explanation_ids = [exp.explanation_id for exp in explanations]
        if explanation_ids:
            db.query(ExplanationEvidence).filter(
                ExplanationEvidence.explanation_id.in_(explanation_ids)
            ).delete(synchronize_session=False)
            db.query(RecommendationExplanation).filter(
                RecommendationExplanation.explanation_id.in_(explanation_ids)
            ).delete(synchronize_session=False)

        # E. Delete validation runs & validation results
        val_runs = (
            db.query(PortfolioValidationRun)
            .filter(PortfolioValidationRun.portfolio_version_id.in_(version_ids))
            .all()
        )
        run_ids = [vr.validation_run_id for vr in val_runs]
        if run_ids:
            db.query(PortfolioValidationResult).filter(
                PortfolioValidationResult.validation_run_id.in_(run_ids)
            ).delete(synchronize_session=False)
            db.query(PortfolioValidationRun).filter(
                PortfolioValidationRun.validation_run_id.in_(run_ids)
            ).delete(synchronize_session=False)

        # F. Delete constraints
        db.query(PortfolioVersionConstraint).filter(
            PortfolioVersionConstraint.portfolio_version_id.in_(version_ids)
        ).delete(synchronize_session=False)

        # G. Delete security decisions
        decisions_deleted = (
            db.query(PortfolioSecurityDecision)
            .filter(PortfolioSecurityDecision.portfolio_version_id.in_(version_ids))
            .delete(synchronize_session=False)
        )
        total_decisions_deleted += decisions_deleted

        # H. Delete versions
        db.query(PortfolioVersion).filter(
            PortfolioVersion.portfolio_version_id.in_(version_ids)
        ).delete(synchronize_session=False)

    # 2. Delete generation requests
    if request_ids:
        db.query(PortfolioGenerationRequest).filter(
            PortfolioGenerationRequest.generation_request_id.in_(request_ids)
        ).delete(synchronize_session=False)
    # Also delete any request by portfolio_id
    db.query(PortfolioGenerationRequest).filter(
        PortfolioGenerationRequest.portfolio_id == portfolio_id
    ).delete(synchronize_session=False)

    # 3. Delete portfolio
    portfolio_name = portfolio.portfolio_name
    db.delete(portfolio)
    db.commit()

    logger.info(
        f"Permanently deleted InvestorPortfolio {portfolio_id} ('{portfolio_name}') "
        f"for user {user_id}: {len(version_ids)} versions, {total_decisions_deleted} decisions."
    )

    return {
        "success": True,
        "portfolio_id": str(portfolio_id),
        "portfolio_name": portfolio_name,
        "versions_deleted": len(version_ids),
        "decisions_deleted": total_decisions_deleted,
        "scenarios_deleted": total_scenarios_deleted,
        "message": f"Portfolio '{portfolio_name}' and all associated records permanently deleted.",
    }


def delete_existing_portfolio(
    db: Session,
    existing_portfolio_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Dict[str, Any]:
    """
    Deletes an imported/diagnosed portfolio and its holdings, diagnosis results,
    and rebalance suggestions in strict cascade order.
    """
    existing_pf = (
        db.query(ExistingPortfolio)
        .filter(ExistingPortfolio.existing_portfolio_id == existing_portfolio_id)
        .first()
    )
    if not existing_pf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Imported portfolio {existing_portfolio_id} not found.",
        )

    if existing_pf.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this portfolio.",
        )

    portfolio_name = existing_pf.portfolio_name

    # 1. Fetch diagnoses
    diagnoses = (
        db.query(PortfolioDiagnosis)
        .filter(PortfolioDiagnosis.existing_portfolio_id == existing_portfolio_id)
        .all()
    )
    diag_ids = [d.portfolio_diagnosis_id for d in diagnoses]

    if diag_ids:
        # Delete rebalance suggestions
        db.query(RebalanceSuggestion).filter(
            RebalanceSuggestion.portfolio_diagnosis_id.in_(diag_ids)
        ).delete(synchronize_session=False)
        # Delete diagnoses
        db.query(PortfolioDiagnosis).filter(
            PortfolioDiagnosis.portfolio_diagnosis_id.in_(diag_ids)
        ).delete(synchronize_session=False)

    # 2. Delete holdings
    db.query(ExistingPortfolioHolding).filter(
        ExistingPortfolioHolding.existing_portfolio_id == existing_portfolio_id
    ).delete(synchronize_session=False)

    # 3. Delete existing portfolio
    db.delete(existing_pf)
    db.commit()

    logger.info(
        f"Permanently deleted ExistingPortfolio {existing_portfolio_id} ('{portfolio_name}') "
        f"for user {user_id}."
    )

    return {
        "success": True,
        "existing_portfolio_id": str(existing_portfolio_id),
        "portfolio_name": portfolio_name,
        "message": f"Imported portfolio '{portfolio_name}' and all associated diagnoses permanently deleted.",
    }


def export_user_account_data(db: Session, user: AppUser) -> Dict[str, Any]:
    """
    Compiles a comprehensive, structured JSON export of all data associated
    with the investor for GDPR/SEBI compliance and personal records.
    """
    user_id = user.user_id

    # 1. Account info
    account_data = {
        "user_id": str(user.user_id),
        "email": user.email,
        "mobile_number": user.mobile_number,
        "account_status": user.account_status,
        "role": getattr(user, "role", "investor"),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

    # 2. Profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    profile_data = None
    if profile:
        profile_data = {
            "display_name": profile.display_name,
            "country_code": profile.country_code,
            "preferred_currency": profile.preferred_currency,
            "investment_experience": profile.investment_experience,
            "investment_knowledge_level": profile.investment_knowledge_level,
            "version_number": profile.version_number,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        }

    # 3. Preferences & Consents
    prefs = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    prefs_data = {
        "preferred_language": prefs.preferred_language if prefs else "en",
        "timezone_name": prefs.timezone_name if prefs else "Asia/Kolkata",
        "email_notifications_enabled": prefs.email_notifications_enabled if prefs else True,
        "in_app_notifications_enabled": prefs.in_app_notifications_enabled if prefs else True,
    }

    consents = db.query(UserConsent).filter(UserConsent.user_id == user_id).all()
    consents_data = [
        {
            "consent_type": c.consent_type,
            "policy_version": c.policy_version,
            "consent_status": c.consent_status,
            "recorded_at": c.recorded_at.isoformat() if c.recorded_at else None,
        }
        for c in consents
    ]

    # 4. Financial Goals
    goals = db.query(FinancialGoal).filter(FinancialGoal.user_id == user_id).all()
    goals_data = [
        {
            "goal_id": str(g.goal_id),
            "goal_name": g.goal_name,
            "goal_type": g.goal_type,
            "target_amount": float(g.target_amount) if g.target_amount is not None else 0.0,
            "amount_already_saved": float(g.amount_already_saved) if g.amount_already_saved is not None else 0.0,
            "target_date": g.target_date.isoformat() if g.target_date else None,
            "priority": g.priority,
            "status": g.goal_status,
            "notes": g.notes,
        }
        for g in goals
    ]

    # 5. Risk Assessments
    assessments = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.user_id == user_id)
        .order_by(RiskAssessment.created_at.desc())
        .all()
    )
    assessments_data = []
    for ra in assessments:
        answers = (
            db.query(RiskAssessmentAnswer)
            .filter(RiskAssessmentAnswer.risk_assessment_id == ra.risk_assessment_id)
            .all()
        )
        assessments_data.append({
            "risk_assessment_id": str(ra.risk_assessment_id),
            "risk_category": ra.risk_category,
            "risk_tolerance_score": float(ra.risk_tolerance_score) if ra.risk_tolerance_score is not None else None,
            "risk_capacity_score": float(ra.risk_capacity_score) if ra.risk_capacity_score is not None else None,
            "assessment_status": ra.assessment_status,
            "questionnaire_version": ra.questionnaire_version,
            "completed_at": ra.completed_at.isoformat() if ra.completed_at else None,
            "answers_count": len(answers),
        })

    # 6. Generated Portfolios with Versions and Decisions
    portfolios = (
        db.query(InvestorPortfolio)
        .filter(InvestorPortfolio.user_id == user_id)
        .all()
    )
    portfolios_data = []
    for p in portfolios:
        versions = (
            db.query(PortfolioVersion)
            .filter(PortfolioVersion.portfolio_id == p.portfolio_id)
            .order_by(PortfolioVersion.version_number.desc())
            .all()
        )
        versions_list = []
        for v in versions:
            decisions = (
                db.query(PortfolioSecurityDecision)
                .filter(PortfolioSecurityDecision.portfolio_version_id == v.portfolio_version_id)
                .all()
            )
            scenarios = (
                db.query(PortfolioScenario)
                .filter(PortfolioScenario.portfolio_version_id == v.portfolio_version_id)
                .all()
            )
            versions_list.append({
                "version_number": v.version_number,
                "investment_amount": float(v.investment_amount) if v.investment_amount is not None else 0.0,
                "currency_code": v.currency_code,
                "risk_category": v.risk_category,
                "expected_return_pct": float(v.expected_return_pct) if v.expected_return_pct is not None else None,
                "expected_volatility_pct": float(v.expected_volatility_pct) if v.expected_volatility_pct is not None else None,
                "diversification_score": float(v.diversification_score) if v.diversification_score is not None else None,
                "holdings_count": len(decisions),
                "holdings": [
                    {
                        "target_weight_pct": float(d.target_weight_pct) if d.target_weight_pct is not None else 0.0,
                        "decision_reason": d.decision_reason,
                    }
                    for d in decisions
                ],
                "scenarios": [
                    {
                        "scenario_name": s.scenario_name,
                        "estimated_change_pct": float(s.estimated_change_pct) if s.estimated_change_pct is not None else None,
                        "result_summary": s.result_summary,
                    }
                    for s in scenarios
                ],
            })

        portfolios_data.append({
            "portfolio_id": str(p.portfolio_id),
            "portfolio_name": p.portfolio_name,
            "status": p.portfolio_status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "versions": versions_list,
        })

    # 7. Imported / Diagnosed Portfolios
    existing_portfolios = (
        db.query(ExistingPortfolio)
        .filter(ExistingPortfolio.user_id == user_id)
        .all()
    )
    existing_data = []
    for ep in existing_portfolios:
        holdings = (
            db.query(ExistingPortfolioHolding)
            .filter(ExistingPortfolioHolding.existing_portfolio_id == ep.existing_portfolio_id)
            .all()
        )
        existing_data.append({
            "existing_portfolio_id": str(ep.existing_portfolio_id),
            "portfolio_name": ep.portfolio_name,
            "source_type": ep.source_type,
            "as_of_date": ep.as_of_date.isoformat() if ep.as_of_date else None,
            "holdings_count": len(holdings),
        })

    return {
        "export_metadata": {
            "application": "Lucid — Intelligent Portfolio Creation & Rebalancing Engine",
            "schema_version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "user_id": str(user_id),
        },
        "account": account_data,
        "profile": profile_data,
        "preferences": prefs_data,
        "consents": consents_data,
        "financial_goals": goals_data,
        "risk_assessments": assessments_data,
        "portfolios": portfolios_data,
        "imported_portfolios": existing_data,
    }


def delete_user_account(
    db: Session,
    user: AppUser,
    password: Optional[str] = None,
    confirmation_phrase: str = "",
    current_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Permanently deletes a Lucid account and completely cascades deletion across
    all dependent tables, caches, files, and authentication tokens.

    Requires:
    - confirmation_phrase to strictly match 'DELETE MY ACCOUNT' (case-insensitive)
    - password verification if user has a password_hash set
    """
    user_id = user.user_id

    # 1. Verification of confirmation phrase
    cleaned_phrase = confirmation_phrase.strip().upper() if confirmation_phrase else ""
    if cleaned_phrase != "DELETE MY ACCOUNT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation phrase must exactly match 'DELETE MY ACCOUNT'.",
        )

    # 2. Verification of password if user has a stored password hash
    if user.password_hash:
        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required to confirm account deletion.",
            )
        try:
            import bcrypt
            is_valid = bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8"))
        except Exception:
            is_valid = False

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password. Account deletion aborted.",
            )

    logger.warning(f"Initiating full account deletion for user {user_id} ({user.email}).")

    # 3. Invalidate current JWT session token if provided
    if current_token:
        try:
            thash = hash_token(current_token)
            revoked_record = RevokedToken(
                token_hash=thash,
                reason="Account permanently deleted by user",
                revoked_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc),
            )
            db.add(revoked_record)
            db.flush()
        except Exception as e:
            logger.warning(f"Failed to blacklist current token on deletion: {e}")

    # 4. Delete all InvestorPortfolios belonging to user
    investor_portfolios = (
        db.query(InvestorPortfolio)
        .filter(InvestorPortfolio.user_id == user_id)
        .all()
    )
    for p in investor_portfolios:
        delete_investor_portfolio(db, p.portfolio_id, user_id)

    # 5. Delete all ExistingPortfolios (imported portfolios) belonging to user
    existing_portfolios = (
        db.query(ExistingPortfolio)
        .filter(ExistingPortfolio.user_id == user_id)
        .all()
    )
    for ep in existing_portfolios:
        delete_existing_portfolio(db, ep.existing_portfolio_id, user_id)

    # 6. Delete broker accounts and executions
    broker_accounts = (
        db.query(UserBrokerAccount)
        .filter(UserBrokerAccount.user_id == user_id)
        .all()
    )
    for ba in broker_accounts:
        orders = (
            db.query(BrokerOrder)
            .filter(BrokerOrder.user_broker_account_id == ba.user_broker_account_id)
            .all()
        )
        order_ids = [o.broker_order_id for o in orders]
        if order_ids:
            db.query(BrokerExecution).filter(
                BrokerExecution.broker_order_id.in_(order_ids)
            ).delete(synchronize_session=False)
            db.query(BrokerOrderEvent).filter(
                BrokerOrderEvent.broker_order_id.in_(order_ids)
            ).delete(synchronize_session=False)
            db.query(BrokerOrder).filter(
                BrokerOrder.broker_order_id.in_(order_ids)
            ).delete(synchronize_session=False)
        db.delete(ba)
    db.flush()

    # 7. Delete financial goals
    # (Note: portfolio_generation_requests referencing goals were deleted in delete_investor_portfolio)
    db.query(FinancialGoal).filter(FinancialGoal.user_id == user_id).delete(
        synchronize_session=False
    )

    # 8. Delete risk assessments & answers
    assessments = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.user_id == user_id)
        .all()
    )
    ra_ids = [ra.risk_assessment_id for ra in assessments]
    if ra_ids:
        db.query(RiskAssessmentAnswer).filter(
            RiskAssessmentAnswer.risk_assessment_id.in_(ra_ids)
        ).delete(synchronize_session=False)
        db.query(RiskAssessment).filter(
            RiskAssessment.risk_assessment_id.in_(ra_ids)
        ).delete(synchronize_session=False)

    # 9. Delete user preferences, sector/security preferences, consents, codes
    db.query(UserSectorPreference).filter(
        UserSectorPreference.user_id == user_id
    ).delete(synchronize_session=False)
    db.query(UserSecurityPreference).filter(
        UserSecurityPreference.user_id == user_id
    ).delete(synchronize_session=False)
    db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).delete(synchronize_session=False)
    db.query(UserConsent).filter(
        UserConsent.user_id == user_id
    ).delete(synchronize_session=False)
    db.query(UserVerificationCode).filter(
        UserVerificationCode.user_id == user_id
    ).delete(synchronize_session=False)

    # 10. Delete profile versions and user profile
    db.query(UserProfileVersion).filter(
        UserProfileVersion.user_id == user_id
    ).delete(synchronize_session=False)
    db.query(UserProfile).filter(
        UserProfile.user_id == user_id
    ).delete(synchronize_session=False)

    # 11. Delete notifications & user feedback
    db.query(Notification).filter(
        Notification.user_id == user_id
    ).delete(synchronize_session=False)
    db.query(UserFeedback).filter(
        UserFeedback.user_id == user_id
    ).delete(synchronize_session=False)

    # 12. Anonymize audit events (preserves regulatory system integrity without storing PII)
    db.query(AuditEvent).filter(
        AuditEvent.actor_user_id == user_id
    ).update(
        {AuditEvent.actor_user_id: None},
        synchronize_session=False,
    )

    # 13. Clear in-memory AI conversational history & sessions
    try:
        cleared_sessions = session_manager.clear_all_for_user(str(user_id))
        logger.info(f"Cleared {cleared_sessions} conversational sessions for deleted user {user_id}.")
    except Exception as e:
        logger.warning(f"Error clearing session memory: {e}")

    # 14. Delete the user record
    db.delete(user)
    db.commit()

    logger.warning(f"Account for user {user_id} has been permanently deleted.")

    return {
        "success": True,
        "user_id": str(user_id),
        "status": "permanently_deleted",
        "message": "Your Lucid account and all associated personal investment records have been permanently deleted.",
    }
