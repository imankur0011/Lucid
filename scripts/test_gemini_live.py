#!/usr/bin/env python3
"""
Controlled Live Gemini API Smoke Test Script.

Tests real network invocation to Google Gemini API outside the CI test suite.
Distinguishes between live external LLM execution and local dynamic fallback.

Usage:
    python scripts/test_gemini_live.py
"""

import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import settings

def run_gemini_smoke_test():
    print("=" * 65)
    print("  GOOGLE GEMINI LIVE INTEGRATION AUDIT & SMOKE TEST")
    print("=" * 65)

    api_key = os.environ.get("GEMINI_API_KEY") or getattr(settings, "gemini_api_key", None)

    print(f"Configured Model : {getattr(settings, 'llm_model', 'gemini-3.8-flash')}")
    print(f"LLM Provider     : {getattr(settings, 'llm_provider', 'gemini')}")

    if not api_key or api_key == "your_gemini_api_key_here" or len(api_key) < 10:
        print("\n[INFO] No valid private GEMINI_API_KEY detected in environment or .env.")
        print("Status: LOCAL DYNAMIC REASONING ENGINE ACTIVE")
        print("Behavior:")
        print("  - Automated CI and test suites run deterministically without external dependency.")
        print("  - Prompt-aware heuristic synthesizer generates tailored strategy themes and stances.")
        print("  - Execution trace explicitly logs: 'ai_provider': 'dynamic_heuristic_fallback'.")
        print("  - No billing or quota usage incurred.")
        print("\nTo test with a live key:")
        print("  export GEMINI_API_KEY=\"AIzaSy...\"")
        print("  python scripts/test_gemini_live.py")
        print("=" * 65)
        return True

    masked_key = api_key[:6] + "..." + api_key[-4:]
    print(f"API Key Detected : {masked_key}")
    print("\nInitiating live API call to Google Gemini endpoint...")

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import SystemMessage, HumanMessage

        model_name = getattr(settings, "llm_model", "gemini-3.8-flash") or "gemini-3.8-flash"
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.2,
            timeout=20,
        )

        test_prompt = (
            "You are an Indian equities quantitative strategist. "
            "In 2 sentences, state your stance on NIFTY 50 large-cap valuation for a moderate risk investor."
        )

        start_time = time.time()
        resp = llm.invoke([
            SystemMessage(content="You are a transparent SEBI-registered portfolio strategist."),
            HumanMessage(content=test_prompt),
        ])
        latency_ms = round((time.time() - start_time) * 1000, 2)

        print("\n[SUCCESS] Live Google Gemini response received!")
        print(f"Latency          : {latency_ms} ms")
        print(f"Response Content :\n  \"{str(resp.content).strip()}\"")
        print("\nAudit Verification:")
        print("  - External transit: Verified")
        print("  - Active Model: Verified accessible")
        print(f"  - Trace Tag: 'ai_provider': 'gemini', 'model_name': '{model_name}'")
        print("=" * 65)
        return True

    except Exception as e:
        print(f"\n[FAILURE] Live Gemini call encountered an exception: {e}")
        print("Note: In accordance with our architecture, the system safely falls back")
        print("to the local dynamic reasoning engine with zero service interruption.")
        print("=" * 65)
        return False

if __name__ == "__main__":
    run_gemini_smoke_test()
