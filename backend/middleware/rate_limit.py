"""
In-Memory Rate Limiting Middleware for FastAPI.
Provides rate-limiting safeguards against brute-force authentication attempts
and protects expensive AI / optimization endpoints from resource exhaustion.
"""

import time
from typing import Dict, List, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

try:
    from backend.config import settings
except ImportError:
    from config import settings


class InMemoryRateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter using timestamp buckets per client IP.
    Protects sensitive auth endpoints and resource-intensive AI generation routes.
    """
    _instance = None

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        # ip -> path -> list of request timestamps
        self._history: Dict[str, Dict[str, List[float]]] = {}
        InMemoryRateLimiterMiddleware._instance = self

        # Path rules: (path_prefix, max_requests, window_seconds)
        self.rules: List[Tuple[str, str, int, int]] = [
            ("POST", "/api/v1/auth/token", 20, 60),
            ("POST", "/api/v1/portfolios/generate", 15, 60),
            ("POST", "/api/v1/market-data/ingest", 10, 60),
        ]

    @classmethod
    def reset(cls):
        """Clears request history for testing."""
        if cls._instance:
            cls._instance._history.clear()

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enabled:
            return await call_next(request)

        # Allow test suites or dev bypass via header
        if request.headers.get("x-test-rate-limit-bypass") == "true":
            return await call_next(request)

        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (request.client.host if request.client else "127.0.0.1")
        )
        now = time.time()
        path = request.url.path
        method = request.method.upper()

        for rule_method, rule_path, max_req, window_sec in self.rules:
            if method == rule_method and path.startswith(rule_path):
                client_records = self._history.setdefault(client_ip, {})
                timestamps = client_records.setdefault(rule_path, [])

                # Evict timestamps outside sliding window
                cutoff = now - window_sec
                timestamps = [t for t in timestamps if t > cutoff]
                client_records[rule_path] = timestamps

                if len(timestamps) >= max_req:
                    return JSONResponse(
                        status_code=429,
                        headers={"Retry-After": str(window_sec)},
                        content={
                            "detail": f"Rate limit exceeded. Maximum {max_req} requests per {window_sec}s allowed for {rule_path}."
                        },
                    )

                timestamps.append(now)
                break

        return await call_next(request)
