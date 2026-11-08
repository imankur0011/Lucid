"""
Investor Profile API endpoints (GET, PATCH) with full historical versioning.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Security, Response
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid

try:
    from backend.database import get_db
    from backend.models import AppUser, UserProfile, UserProfileVersion
    from backend.auth.dependencies import get_current_user, security_bearer
    from backend.schemas import (
        UserProfileRead,
        UserProfileUpdate,
        UserProfileVersionRead,
        NaturalLanguageProfileRequest,
        NaturalLanguageProfileResponse,
    )
    from backend.portfolio_engine.nlp_profile_extractor import extract_investor_profile_nlp
    from backend.services.account_deletion_service import (
        export_user_account_data,
        delete_user_account,
    )
except ImportError:
    from database import get_db
    from models import AppUser, UserProfile, UserProfileVersion
    from auth.dependencies import get_current_user, security_bearer
    from schemas import (
        UserProfileRead,
        UserProfileUpdate,
        UserProfileVersionRead,
        NaturalLanguageProfileRequest,
        NaturalLanguageProfileResponse,
    )
    from portfolio_engine.nlp_profile_extractor import extract_investor_profile_nlp
    from services.account_deletion_service import (
        export_user_account_data,
        delete_user_account,
    )

router = APIRouter(prefix="/profile", tags=["Investor Profile"])


@router.get("", response_model=UserProfileRead)
async def get_profile(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve the authenticated investor's profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.user_id).first()
    if not profile:
        # Create a default profile if none exists
        profile = UserProfile(
            user_id=current_user.user_id,
            version_number=1,
            display_name=current_user.email.split("@")[0] if current_user.email else "Investor",
            country_code="IN",
            preferred_currency="INR",
            investment_experience="beginner",
            investment_knowledge_level="basic",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.patch("", response_model=UserProfileRead)
async def update_profile(
    payload: UserProfileUpdate,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update profile fields for the authenticated investor.
    5.7 Automatically versions the prior profile state into UserProfileVersion
    before applying changes, preserving full audit and change history.
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.user_id).first()
    if not profile:
        profile = UserProfile(
            user_id=current_user.user_id,
            version_number=1,
            country_code="IN",
            preferred_currency="INR",
        )
        db.add(profile)
        db.flush()

    update_data = payload.model_dump(exclude_unset=True)
    if "mobile_number" in update_data:
        current_user.mobile_number = update_data.pop("mobile_number")
        current_user.updated_at = datetime.now(timezone.utc)
        db.add(current_user)

    if update_data:
        # Archive prior profile snapshot to history
        current_ver = getattr(profile, "version_number", 1) or 1
        snapshot = UserProfileVersion(
            profile_version_id=uuid.uuid4(),
            user_id=profile.user_id,
            version_number=current_ver,
            display_name=profile.display_name,
            country_code=profile.country_code,
            preferred_currency=profile.preferred_currency,
            investment_experience=profile.investment_experience,
            investment_knowledge_level=profile.investment_knowledge_level,
            change_summary=f"Updated attributes: {', '.join(update_data.keys())}",
            created_at=profile.updated_at or datetime.now(timezone.utc),
        )
        db.add(snapshot)

        # Apply update and increment version number
        for field, val in update_data.items():
            if val is not None:
                setattr(profile, field, val)

        profile.version_number = current_ver + 1
        profile.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(profile)

    return profile


@router.get("/versions", response_model=List[UserProfileVersionRead])
async def get_profile_version_history(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    5.7 Returns the complete version history of profile updates for the investor.
    Enables tracking of risk appetite and preference evolution over time.
    """
    versions = (
        db.query(UserProfileVersion)
        .filter(UserProfileVersion.user_id == current_user.user_id)
        .order_by(UserProfileVersion.version_number.desc())
        .all()
    )
    return versions


@router.post("/extract-from-text", response_model=NaturalLanguageProfileResponse)
async def extract_profile_from_natural_language(
    payload: NaturalLanguageProfileRequest,
    db: Session = Depends(get_db),
):
    """
    Extracts structured financial parameters, goals, horizons, and risk suitability
    from unformatted natural language text using Gemini 3.8 Flash (with deterministic fallback).
    """
    try:
        profile = extract_investor_profile_nlp(payload.text, db=db)

        # Merge with existing profile if provided
        if payload.existing_profile:
            from backend.portfolio_engine.nlp_profile_extractor import merge_profile_with_extracted_data
            profile = merge_profile_with_extracted_data(payload.existing_profile, profile)

        summary_parts = []
        if profile.capital.initial_lump_sum:
            summary_parts.append(f"₹{profile.capital.initial_lump_sum:,.0f} lump sum")
        elif profile.capital.monthly_contribution:
            summary_parts.append(f"₹{profile.capital.monthly_contribution:,.0f}/month SIP")
        if profile.horizon_months:
            summary_parts.append(f"over {round(profile.horizon_months/12, 1)} years")
        summary_parts.append(f"with {profile.risk.assessed_risk_category.value.capitalize()} risk")

        calc_amount = (
            profile.capital.initial_lump_sum
            if profile.capital.initial_lump_sum is not None
            else (profile.capital.monthly_contribution * 12 if profile.capital.monthly_contribution else 250_000.0)
        )
        calc_horizon = profile.horizon_months or 60

        prefilled = {
            "portfolioName": profile.portfolio_name,
            "investmentAmount": calc_amount,
            "horizonMonths": calc_horizon,
            "riskCategory": profile.risk.assessed_risk_category.value,
            "experience": profile.experience.experience_level,
            "knowledge": profile.experience.knowledge_level,
            "excludedSectors": profile.preferences.excluded_sectors,
            "preferredSectors": profile.preferences.preferred_sectors,
            "answers": {a.question_id: a.selected_option_id for a in profile.mapped_questionnaire_answers},
        }

        extracted_dict = {
            "portfolio_name": profile.portfolio_name,
            "investment_amount": float(calc_amount),
            "horizon_months": int(calc_horizon),
            "risk_category": profile.risk.assessed_risk_category.value,
            "experience_level": profile.experience.experience_level,
            "knowledge_level": profile.experience.knowledge_level,
            "emergency_fund_status": profile.risk.emergency_fund_status,
            "loss_capacity_emergency_months": profile.risk.loss_capacity_emergency_months,
            "goal_type": profile.goals[0].goal_type if profile.goals else "wealth_creation",
            "goal_name": profile.goals[0].goal_name if profile.goals else "Long-Term Wealth Creation",
            "target_corpus": float(calc_amount) * 2.5,
            "preferred_sectors": profile.preferences.preferred_sectors,
            "excluded_sectors": profile.preferences.excluded_sectors,
            "preferred_securities": [p.model_dump() for p in profile.preferences.preferred_securities],
            "sector_constraints": [sc.model_dump() for sc in profile.preferences.sector_constraints],
            "existing_holdings": [h.model_dump() for h in profile.existing_holdings],
            "user_prompt": profile.cleaned_user_prompt,
        }

        resolved_list = [
            {
                "question_id": a.question_id,
                "question_code": a.question_code,
                "question_text": a.question_text,
                "selected_option_id": a.selected_option_id,
                "selected_option_code": a.selected_option_code,
                "selected_option_label": a.selected_option_label,
                "score": a.score,
            }
            for a in profile.mapped_questionnaire_answers
        ]

        mapped_codes = {a.question_code: a.selected_option_code for a in profile.mapped_questionnaire_answers}

        return NaturalLanguageProfileResponse(
            profile=profile,
            summary_text="Lucid parsed: " + ", ".join(summary_parts),
            prefilled_questionnaire=prefilled,
            extracted_profile=extracted_dict,
            mapped_option_codes=mapped_codes,
            fiduciary_notes=profile.fiduciary_audit_notes,
            confidence_score=profile.confidence_score,
            extraction_method=profile.extraction_method,
            resolved_questionnaire_answers=resolved_list,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process natural language profile: {str(e)}",
        )


class DeleteAccountRequest(BaseModel):
    password: Optional[str] = Field(None, description="Current password for verification (required for password accounts)")
    confirmation_phrase: str = Field(..., description="Must exactly match 'DELETE MY ACCOUNT'")


@router.get("/export")
async def export_investor_data(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Exports all investor profile, preferences, financial goals, risk assessments,
    portfolios, holdings, and diagnoses as structured JSON (GDPR / SEBI data portability).
    """
    return export_user_account_data(db=db, user=current_user)


@router.post("/delete-account")
@router.delete("")
async def delete_account(
    payload: DeleteAccountRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permanently deletes the investor account and initiates complete deletion or
    anonymization of all associated personal information, portfolios, goals,
    risk profiles, and session credentials.
    """
    token = credentials.credentials if credentials else None
    return delete_user_account(
        db=db,
        user=current_user,
        password=payload.password,
        confirmation_phrase=payload.confirmation_phrase,
        current_token=token,
    )
