"""
API v1 Master Router.
Aggregates profile, goals, risk assessments, market data, and portfolio routers.
"""

from fastapi import APIRouter

try:
    from backend.api.v1.profile import router as profile_router
    from backend.api.v1.goals import router as goals_router
    from backend.api.v1.risk_assessments import router as risk_router
    from backend.api.v1.market_data import router as market_router
    from backend.api.v1.portfolios import router as portfolios_router
except ImportError:
    from api.v1.profile import router as profile_router
    from api.v1.goals import router as goals_router
    from api.v1.risk_assessments import router as risk_router
    from api.v1.market_data import router as market_router
    from api.v1.portfolios import router as portfolios_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(profile_router)
api_v1_router.include_router(goals_router)
api_v1_router.include_router(risk_router)
api_v1_router.include_router(market_router)
api_v1_router.include_router(portfolios_router)
