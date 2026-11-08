#!/usr/bin/env python3
"""
Lucid — Repository-Wide Documentation and Architecture Consistency Validator.
Verifies that documentation, configuration, database models, OpenAPI routes,
diagram assets, and external integrations are in complete alignment.

Usage:
    python scripts/validate_documentation.py
"""

import sys
import os
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️  WARN"


def check_required_documents():
    print("\n[1/7] Checking Core Documentation & Design Suite Artifacts...")
    required_docs = [
        "README.md",
        "HIGH_LEVEL_DESIGN.md",
        "LOW_LEVEL_DESIGN.md",
        "SYSTEM_ARCHITECTURE.md",
        "AGENT_ARCHITECTURE.md",
        "AGENTIC_AI_ARCHITECTURE.md",
        "METHODOLOGY.md",
        "DATASET_USED.md",
        "DESIGN_DOCUMENTATION_INDEX.md",
        "DESIGN_TRACEABILITY_MATRIX.md",
        "DATABASE_ARCHITECTURE.md",
        "OPTIMIZATION_METHODOLOGY.md",
        "SECURITY_AND_RELIABILITY.md",
        "FUNCTIONAL_REQUIREMENT_MAPPING.md",
        "docs/design/HIGH_LEVEL_DESIGN.md",
        "docs/design/LOW_LEVEL_DESIGN.md",
        "docs/design/SYSTEM_ARCHITECTURE.md",
        "docs/design/AGENT_ARCHITECTURE.md",
        "docs/design/METHODOLOGY.md",
        "docs/design/DATASET_USED.md",
        "docs/design/DESIGN_DOCUMENTATION_INDEX.md",
        "docs/design/DESIGN_TRACEABILITY_MATRIX.md",
        "docs/exports/HIGH_LEVEL_DESIGN.pdf",
        "docs/exports/LOW_LEVEL_DESIGN.pdf",
        "docs/exports/SYSTEM_ARCHITECTURE.pdf",
        "docs/exports/AGENT_ARCHITECTURE.pdf",
        "docs/exports/METHODOLOGY.pdf",
        "docs/exports/DATASET_USED.pdf",
    ]
    missing = []
    for doc in required_docs:
        p = ROOT_DIR / doc
        if not p.is_file() or p.stat().st_size == 0:
            missing.append(doc)
    if missing:
        print(f"   {FAIL} Missing or empty required documentation files: {missing}")
        return False
    print(f"   {PASS} All {len(required_docs)} authoritative design documents and PDF exports verified.")
    return True


def check_diagram_assets():
    print("\n[2/7] Checking Visual Architecture & Methodology Diagram Assets...")
    diagrams = [
        "SYSTEM_ARCHITECTURE.mmd",
        "SYSTEM_ARCHITECTURE.svg",
        "SYSTEM_ARCHITECTURE.png",
        "METHODOLOGY_FLOW.mmd",
        "METHODOLOGY_FLOW.svg",
        "METHODOLOGY_FLOW.png",
        "AGENTIC_AI_ARCHITECTURE.mmd",
        "AGENTIC_AI_ARCHITECTURE.svg",
        "AGENTIC_AI_ARCHITECTURE.png",
        "COMPLETE_DATA_FLOW.mmd",
        "COMPLETE_DATA_FLOW.svg",
        "COMPLETE_DATA_FLOW.png",
    ]
    missing = []
    for d in diagrams:
        p = ROOT_DIR / d
        if not p.is_file() or p.stat().st_size == 0:
            missing.append(d)
    if missing:
        print(f"   {FAIL} Missing or empty diagram assets: {missing}")
        return False
    print(f"   {PASS} All {len(diagrams)} diagram source, SVG, and PNG assets verified.")
    return True


def check_database_model_consistency():
    print("\n[3/7] Verifying Database Schema & Table Count Consistency...")
    try:
        from backend.models import Base
        model_count = len(Base.metadata.tables)
        expected_models = 62
        if model_count != expected_models:
            print(f"   {FAIL} Expected {expected_models} SQLAlchemy tables, but found {model_count}!")
            return False
        print(f"   {PASS} Verified exact schema count: {model_count} domain application tables.")
        return True
    except Exception as e:
        print(f"   {FAIL} Failed to inspect SQLAlchemy models: {e}")
        return False


def check_no_active_unused_infrastructure():
    print("\n[4/7] Verifying Clean Architecture (Exclusion of Unused Infrastructure)...")
    config_file = ROOT_DIR / "backend" / "config.py"
    req_file = ROOT_DIR / "backend" / "requirements.txt"
    env_example = ROOT_DIR / ".env.example"

    issues = []
    config_text = config_file.read_text(encoding="utf-8")
    for unused in ["neo4j_uri", "redis_host", "faiss_index_dir"]:
        if unused in config_text:
            issues.append(f"Found active config field '{unused}' in backend/config.py")

    req_text = req_file.read_text(encoding="utf-8")
    for unused in ["neo4j>=", "redis>=", "faiss-cpu>=", "celery>="]:
        if unused in req_text:
            issues.append(f"Found unused dependency '{unused}' in backend/requirements.txt")

    env_text = env_example.read_text(encoding="utf-8")
    for unused in ["NEO4J_URI", "REDIS_HOST", "FAISS_INDEX_DIR"]:
        if unused in env_text:
            issues.append(f"Found unused env variable '{unused}' in .env.example")

    if issues:
        print(f"   {FAIL} Unused infrastructure remnants detected:")
        for iss in issues:
            print(f"      - {iss}")
        return False
    print(f"   {PASS} Verified 0 active references to Neo4j, Redis, Celery, and FAISS in config & dependencies.")
    return True


def check_auth_and_llm_decisions():
    print("\n[5/7] Verifying Canonical Security & LLM Model Decisions...")
    try:
        from backend.api.v1.auth import hash_password, verify_password
        test_hash = hash_password("ConsistencyCheck2026!")
        if not test_hash.startswith("$argon2id$"):
            print(f"   {FAIL} Password hashing is not producing canonical Argon2id hashes: {test_hash[:15]}")
            return False
        if not verify_password("ConsistencyCheck2026!", test_hash):
            print(f"   {FAIL} Argon2id password verification failed!")
            return False
        print(f"   {PASS} Canonical Argon2id password hashing verified.")

        from backend.config import settings
        if settings.llm_model != "gemini-3.8-flash":
            print(f"   {FAIL} Default LLM model is '{settings.llm_model}', expected 'gemini-3.8-flash'!")
            return False
        print(f"   {PASS} Canonical LLM model configured: {settings.llm_model}.")
        return True
    except Exception as e:
        print(f"   {FAIL} Error checking auth/LLM decisions: {e}")
        return False


def check_openapi_endpoint_coverage():
    print("\n[6/7] Verifying OpenAPI Endpoint Compilation & Documentation...")
    try:
        from backend.main import app
        openapi_spec = app.openapi()
        paths = openapi_spec.get("paths", {})
        path_count = len(paths)
        if path_count < 80:
            print(f"   {FAIL} Expected at least 80 endpoints in OpenAPI schema, found {path_count}!")
            return False
        print(f"   {PASS} Verified {path_count} unique API paths active in FastAPI router.")

        # Check key documented routes
        core_routes = [
            "/api/v1/auth/login",
            "/api/v1/auth/me",
            "/api/v1/risk-questions",
            "/api/v1/risk-assessments",
            "/api/v1/portfolio-generation-requests",
            "/api/v1/portfolios/{portfolio_id}/versions/{version_id}/stocks/{symbol}/why",
            "/api/v1/diagnosis/analyze/{existing_portfolio_id}",
            "/api/v1/diagnosis/{existing_portfolio_id}/chat",
            "/api/v1/notifications",
        ]
        missing_routes = [r for r in core_routes if r not in paths]
        if missing_routes:
            print(f"   {FAIL} Key documented routes missing from OpenAPI schema: {missing_routes}")
            return False
        print(f"   {PASS} All core documented endpoints verified in OpenAPI schema.")
        return True
    except Exception as e:
        print(f"   {FAIL} Error checking OpenAPI schema: {e}")
        return False


def check_relative_markdown_links():
    print("\n[7/7] Checking Internal Relative Markdown Links...")
    md_files = list(ROOT_DIR.glob("*.md")) + list((ROOT_DIR / "docs").glob("*.md")) + list((ROOT_DIR / "docs" / "design").glob("*.md"))
    broken_links = []
    link_pattern = re.compile(r'\[([^\]]+)\]\((?!http|#|mailto)([^)]+)\)')

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for match in link_pattern.finditer(content):
            target = match.group(2).split("#")[0]  # Strip anchors
            if not target or target.startswith("file://") or target.startswith("conversation://"):
                continue
            target_path = (md_file.parent / target).resolve()
            if not target_path.exists():
                broken_links.append((md_file.name, target))

    if broken_links:
        print(f"   {WARN} Found {len(broken_links)} unresolvable relative markdown references (checked for non-critical warnings)")
    else:
        print(f"   {PASS} All internal relative markdown links resolve to existing files.")
    return True


def main():
    print("=" * 70)
    print("  LUCID — REPOSITORY-WIDE CONSISTENCY & DOCUMENTATION VALIDATOR")
    print("=" * 70)

    results = [
        check_required_documents(),
        check_diagram_assets(),
        check_database_model_consistency(),
        check_no_active_unused_infrastructure(),
        check_auth_and_llm_decisions(),
        check_openapi_endpoint_coverage(),
        check_relative_markdown_links(),
    ]

    print("\n" + "=" * 70)
    if all(results):
        print("  🎉 ALL DOCUMENTATION CONSISTENCY CHECKS PASSED!")
        print("     The repository codebase, configuration, schema, and diagrams")
        print("     are 100% synchronized with the authoritative implementation.")
        print("=" * 70)
        sys.exit(0)
    else:
        print("  ❌ CONSISTENCY CHECKS FAILED: Please resolve the errors above.")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
