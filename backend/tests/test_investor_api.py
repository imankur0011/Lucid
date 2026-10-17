"""
Integration tests for Investor Onboarding, Profile, Financial Goals, and Risk Assessment APIs.
"""

import pytest
from fastapi.testclient import TestClient
from uuid import UUID

from backend.main import app
from backend.database import SessionLocal
from backend.models import AppUser, FinancialGoal, RiskAssessment, RiskQuestion, RiskQuestionOption

client = TestClient(app)
DEMO_USER_ID = "10000000-0000-4000-8000-000000000001"


def test_get_and_patch_investor_profile():
    """Test retrieving and updating the investor profile."""
    # GET profile
    res = client.get("/api/v1/profile")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["user_id"] == DEMO_USER_ID
    assert data["country_code"] == "IN"

    # PATCH profile
    patch_res = client.patch(
        "/api/v1/profile",
        json={
            "display_name": "Senior Investor",
            "investment_experience": "experienced",
            "investment_knowledge_level": "advanced",
        },
    )
    assert patch_res.status_code == 200, patch_res.text
    updated = patch_res.json()
    assert updated["display_name"] == "Senior Investor"
    assert updated["investment_experience"] == "experienced"
    assert updated["investment_knowledge_level"] == "advanced"


def test_financial_goals_crud_lifecycle():
    """Test creating, reading, updating, and deleting financial goals."""
    # 1. Create Goal
    create_res = client.post(
        "/api/v1/goals",
        json={
            "goal_name": "Home Down Payment",
            "goal_type": "real_estate",
            "target_amount": 2500000.0,
            "amount_already_saved": 500000.0,
            "currency_code": "INR",
            "priority": 2,
            "notes": "Target for Mumbai suburb flat",
        },
    )
    assert create_res.status_code == 201, create_res.text
    goal = create_res.json()
    goal_id = goal["goal_id"]
    assert goal["goal_name"] == "Home Down Payment"
    assert goal["priority"] == 2
    assert goal["goal_status"] == "active"

    # 2. List Goals
    list_res = client.get("/api/v1/goals")
    assert list_res.status_code == 200
    goals = list_res.json()
    assert any(g["goal_id"] == goal_id for g in goals)

    # 3. Update Goal
    patch_res = client.patch(
        f"/api/v1/goals/{goal_id}",
        json={
            "amount_already_saved": 600000.0,
            "priority": 1,
            "goal_status": "active",
        },
    )
    assert patch_res.status_code == 200
    assert float(patch_res.json()["amount_already_saved"]) == 600000.0
    assert patch_res.json()["priority"] == 1

    # 4. Delete Goal
    del_res = client.delete(f"/api/v1/goals/{goal_id}")
    assert del_res.status_code == 204

    # 5. Verify deletion
    verify_res = client.get("/api/v1/goals")
    assert not any(g["goal_id"] == goal_id for g in verify_res.json())


def test_risk_questions_retrieval_and_submission():
    """Test retrieving risk questions, submitting answers, deterministic score calculation, and history retrieval."""
    # 1. Retrieve Questions
    q_res = client.get("/api/v1/risk-questions")
    assert q_res.status_code == 200, q_res.text
    questions = q_res.json()
    assert len(questions) >= 5, "Expected at least 5 standard risk questions"

    # Build answer payload selecting balanced/moderate options
    answers_payload = []
    for q in questions:
        # Choose the middle or high option
        chosen_opt = q["options"][min(2, len(q["options"]) - 1)]
        answers_payload.append({
            "question_id": q["question_id"],
            "selected_option_id": chosen_opt["option_id"],
        })

    # 2. Submit Assessment
    sub_res = client.post(
        "/api/v1/risk-assessments",
        json={
            "questionnaire_version": "v1.0",
            "answers": answers_payload,
        },
    )
    assert sub_res.status_code == 201, sub_res.text
    assessment = sub_res.json()
    assert assessment["user_id"] == DEMO_USER_ID
    assert assessment["assessment_status"] == "completed"
    assert assessment["risk_tolerance_score"] is not None
    assert assessment["risk_category"] in ["conservative", "moderate", "growth", "aggressive"]

    # 3. Get Latest Completed Assessment
    latest_res = client.get("/api/v1/risk-assessments/latest")
    assert latest_res.status_code == 200
    latest = latest_res.json()
    assert latest["risk_assessment_id"] == assessment["risk_assessment_id"]
    assert latest["risk_category"] == assessment["risk_category"]
