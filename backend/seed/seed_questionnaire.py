"""
Seed standard risk assessment questions and scoring options into the database.
Idempotent: updates or inserts without creating duplicates.
"""

import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

try:
    from backend.database import SessionLocal
    from backend.models import RiskQuestion, RiskQuestionOption
except ImportError:
    from database import SessionLocal
    from models import RiskQuestion, RiskQuestionOption

QUESTIONNAIRE_VERSION = 1

QUESTIONS_DATA = [
    {
        "code": "INVESTMENT_HORIZON",
        "text": "What is your planned investment time horizon for this portfolio?",
        "answer_type": "single_choice",
        "display_order": 1,
        "scoring_config": {"weight": 0.20, "category": "capacity"},
        "options": [
            {"code": "HORIZON_LESS_1YR", "label": "Less than 1 year (Short term)", "score": 20.0, "order": 1},
            {"code": "HORIZON_1_3YR", "label": "1 to 3 years (Medium term)", "score": 40.0, "order": 2},
            {"code": "HORIZON_3_5YR", "label": "3 to 5 years (Long term)", "score": 70.0, "order": 3},
            {"code": "HORIZON_5PLUS", "label": "More than 5 years (Very long term)", "score": 100.0, "order": 4},
        ],
    },
    {
        "code": "PRIMARY_OBJECTIVE",
        "text": "What is the primary financial objective for these invested funds?",
        "answer_type": "single_choice",
        "display_order": 2,
        "scoring_config": {"weight": 0.25, "category": "tolerance"},
        "options": [
            {"code": "OBJ_CAPITAL_PRESERVATION", "label": "Capital preservation - protect capital with minimal risk", "score": 20.0, "order": 1},
            {"code": "OBJ_INCOME", "label": "Regular income with low capital fluctuation", "score": 40.0, "order": 2},
            {"code": "OBJ_BALANCED_GROWTH", "label": "Balanced growth - moderate capital appreciation with some risk", "score": 65.0, "order": 3},
            {"code": "OBJ_MAX_APPRECIATION", "label": "Aggressive capital growth - seeking highest returns over the long run", "score": 95.0, "order": 4},
        ],
    },
    {
        "code": "MARKET_DOWNTURN_REACTION",
        "text": "If the stock market falls 20% over 3 months, what would you most likely do?",
        "answer_type": "single_choice",
        "display_order": 3,
        "scoring_config": {"weight": 0.25, "category": "tolerance"},
        "options": [
            {"code": "REACT_SELL_ALL", "label": "Sell all investments immediately to avoid further losses", "score": 10.0, "order": 1},
            {"code": "REACT_SELL_SOME", "label": "Sell some investments and switch to safer fixed-income instruments", "score": 35.0, "order": 2},
            {"code": "REACT_HOLD", "label": "Do nothing and hold through the market cycle", "score": 70.0, "order": 3},
            {"code": "REACT_BUY_MORE", "label": "Invest additional funds to take advantage of lower valuations", "score": 100.0, "order": 4},
        ],
    },
    {
        "code": "INVESTMENT_KNOWLEDGE",
        "text": "How would you describe your familiarity with equity markets and portfolio investments?",
        "answer_type": "single_choice",
        "display_order": 4,
        "scoring_config": {"weight": 0.15, "category": "knowledge"},
        "options": [
            {"code": "EXP_NONE", "label": "Beginner - primary experience is bank deposits / FDs", "score": 25.0, "order": 1},
            {"code": "EXP_MUTUAL_FUNDS", "label": "Intermediate - familiar with mutual funds and SIPs", "score": 60.0, "order": 2},
            {"code": "EXP_DIRECT_EQUITY", "label": "Experienced - actively analyze and invest in direct equities", "score": 90.0, "order": 3},
        ],
    },
    {
        "code": "EMERGENCY_FUND_BUFFER",
        "text": "Do you have a dedicated emergency fund covering at least 6 months of living expenses?",
        "answer_type": "single_choice",
        "display_order": 5,
        "scoring_config": {"weight": 0.15, "category": "capacity"},
        "options": [
            {"code": "EMERGENCY_NO", "label": "No emergency reserve set aside", "score": 20.0, "order": 1},
            {"code": "EMERGENCY_PARTIAL", "label": "Partial emergency fund (2 to 4 months)", "score": 55.0, "order": 2},
            {"code": "EMERGENCY_FULL", "label": "Full emergency fund (6+ months safely invested in liquid assets)", "score": 95.0, "order": 3},
        ],
    },
]


def seed_risk_questions(db: Session) -> int:
    """Seeds or updates the risk assessment questionnaire."""
    total_seeded = 0
    for q_data in QUESTIONS_DATA:
        # Check if question exists
        question = (
            db.query(RiskQuestion)
            .filter_by(question_code=q_data["code"], question_version=QUESTIONNAIRE_VERSION)
            .first()
        )
        if not question:
            question = RiskQuestion(
                question_id=uuid.uuid4(),
                question_code=q_data["code"],
                question_version=QUESTIONNAIRE_VERSION,
                question_text=q_data["text"],
                answer_type=q_data["answer_type"],
                is_required=True,
                is_active=True,
                display_order=q_data["display_order"],
                scoring_config=q_data["scoring_config"],
            )
            db.add(question)
            db.flush()
            total_seeded += 1
        else:
            question.question_text = q_data["text"]
            question.display_order = q_data["display_order"]
            question.scoring_config = q_data["scoring_config"]

        # Seed options
        for opt in q_data["options"]:
            option = (
                db.query(RiskQuestionOption)
                .filter_by(question_id=question.question_id, option_code=opt["code"])
                .first()
            )
            if not option:
                option = RiskQuestionOption(
                    option_id=uuid.uuid4(),
                    question_id=question.question_id,
                    option_code=opt["code"],
                    option_label=opt["label"],
                    score=opt["score"],
                    display_order=opt["order"],
                )
                db.add(option)
            else:
                option.option_label = opt["label"]
                option.score = opt["score"]
                option.display_order = opt["order"]

    db.commit()
    return total_seeded


if __name__ == "__main__":
    db = SessionLocal()
    try:
        count = seed_risk_questions(db)
        print(f"✅ Successfully seeded {count} risk questions with options.")
    finally:
        db.close()
