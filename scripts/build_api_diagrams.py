#!/usr/bin/env python3
"""
Generates Mermaid sequence diagrams for API workflows under docs/diagrams/api/
and renders them to SVG and PNG.
"""

import subprocess
from pathlib import Path

ROOT_DIR = Path('/Users/ankur/Documents/MajorProject/app')
API_DIAGRAMS_DIR = ROOT_DIR / "docs" / "diagrams" / "api"
API_DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)

diagrams = {
    "API_AUTH_FLOW": """sequenceDiagram
    autonumber
    actor User as Investor
    participant UI as Next.js React UI (AuthView.tsx)
    participant API as FastAPI Router (/auth)
    participant AuthSvc as AuthService (Argon2id)
    participant DB as PostgreSQL 16 (app_users, revoked_tokens)

    User->>UI: Enter email & password
    UI->>API: POST /api/v1/auth/login
    API->>AuthSvc: verify_password(password, user.password_hash)
    AuthSvc->>DB: Query user by email
    AuthSvc->>AuthSvc: Argon2id verification ($m=65536, t=3, p=4)
    AuthSvc-->>API: Authentication success
    API->>API: create_access_token(user_id, email)
    API-->>UI: 200 OK (access_token, token_type: bearer, expires_in: 86400)
    UI->>UI: Store token in localStorage

    opt Token Revocation / Logout
        User->>UI: Click Logout
        UI->>API: POST /api/v1/auth/logout (Bearer Token)
        API->>DB: INSERT into revoked_tokens (token_hash, revoked_at)
        API-->>UI: 200 OK (detail: 'Successfully logged out')
        UI->>UI: Clear localStorage & redirect to login
    end
""",
    "API_PORTFOLIO_GENERATION_FLOW": """sequenceDiagram
    autonumber
    actor User as Investor
    participant UI as Next.js UI (PortfolioGenerator.tsx)
    participant API as FastAPI Router (/portfolios)
    participant Engine as PortfolioEngine
    participant LG as LangGraph Orchestrator (13 Nodes)
    participant Optimizer as SciPy SLSQP Optimizer
    participant DB as PostgreSQL 16

    User->>UI: Specify ₹5,00,000, 36 Months, BALANCED
    UI->>API: POST /api/v1/portfolio-generation-requests
    API->>DB: INSERT into portfolio_generation_requests (RUNNING)
    API->>Engine: start_portfolio_generation()
    Engine->>LG: create_portfolio_graph(db).invoke(state)
    
    rect rgb(240, 248, 255)
        Note over LG: Multi-Agent Analysis & Critic Loop
        LG->>LG: manager -> suitability -> macro -> market -> fundamental -> news -> strategist
        LG->>LG: critic (Independent Risk Audit: single-stock <=20%, sector <=30%)
    end

    LG->>Optimizer: deterministic_optimizer_node
    Optimizer->>Optimizer: SLSQP Quadratic Optimization & Discrete Integer Lot Sizing
    LG->>LG: critic_final_validation -> moderator (Two-Level Stock-Why)
    LG->>DB: persistence_node (Atomic ACID Commit: PortfolioVersion, Holdings)
    
    API-->>UI: 201 Created (request_id, portfolio_id, version_id, positions, cash)
    UI->>UI: Render HoldingsView, AllocationVisualizer, and Stock-Why buttons
""",
    "API_MONITORING_REBALANCE_FLOW": """sequenceDiagram
    autonumber
    participant Daemon as BackgroundMonitoringScheduler (300s)
    participant API as FastAPI Router (/portfolios)
    participant Svc as PortfolioMonitoringService
    participant RebSvc as RebalancingService
    participant DB as PostgreSQL 16
    actor User as Investor (RebalancePreviewModal.tsx)

    Daemon->>Svc: Timer tick: evaluate active portfolios
    Svc->>DB: SELECT holdings and target weights
    Svc->>Svc: Compute NAV, Asset Drift (|w_cur - w_tgt|), Sector Drift
    
    alt Drift > 5.0% (Single Asset) OR Total Drift > 15.0%
        Svc->>DB: INSERT into notifications (DRIFT_WARNING)
        Svc->>DB: INSERT into rebalance_suggestions (PENDING)
    end

    User->>API: GET /api/v1/portfolios/{id}/rebalance-preview
    API->>RebSvc: generate_rebalance_preview(portfolio_id)
    RebSvc->>RebSvc: Calculate delta shares & Indian statutory friction (STT, GST)
    API-->>User: 200 OK (proposed BUY/SELL orders, transaction costs)

    User->>API: POST /api/v1/portfolios/{id}/apply-rebalance
    API->>DB: INSERT new PortfolioVersion (incremented version_number)
    API-->>User: 200 OK (Updated portfolio active)
""",
    "API_DIAGNOSIS_FLOW": """sequenceDiagram
    autonumber
    actor User as Investor
    participant UI as Next.js UI (DiagnosisView.tsx)
    participant API as FastAPI Router (/diagnosis)
    participant DiagSvc as PortfolioDiagnosisService
    participant Resolver as CompanyResolutionService
    participant DB as PostgreSQL 16
    participant Copilot as DiagnosisCopilotService (Gemini)

    User->>UI: Upload Demat Statement CSV (Zerodha/Groww)
    UI->>API: POST /api/v1/diagnosis/upload-csv
    API->>DiagSvc: parse_holdings_csv(file)
    DiagSvc->>Resolver: resolve_company_to_isin(symbol, company_name)
    Resolver-->>DiagSvc: Canonical ISINs & normalized symbols
    DiagSvc->>DB: INSERT into existing_portfolios & existing_portfolio_holdings
    API-->>UI: 200 OK (existing_portfolio_id, normalized_holdings)

    User->>UI: Click 'Analyze Demat Portfolio'
    UI->>API: POST /api/v1/diagnosis/analyze/{existing_portfolio_id}
    API->>DiagSvc: analyze_portfolio_concentration(existing_portfolio_id)
    DiagSvc->>DiagSvc: Calculate Herfindahl-Hirschman Index (HHI) & Sector Caps
    DiagSvc->>DB: INSERT into portfolio_diagnoses (health_score, hhi)
    API-->>UI: 200 OK (health_score, hhi_index, concentration_warnings)

    opt Interactive Copilot Chat
        User->>UI: Ask: "Why is my IT allocation too high?"
        UI->>API: POST /api/v1/diagnosis/{id}/chat
        API->>Copilot: chat_diagnosis(query, diagnosis_data)
        Copilot-->>API: Structured explanation of sector concentration
        API-->>UI: 200 OK (response_text)
    end
"""
}

def main():
    print("Writing Mermaid diagram sources to docs/diagrams/api/...")
    for name, content in diagrams.items():
        mmd_path = API_DIAGRAMS_DIR / f"{name}.mmd"
        svg_path = API_DIAGRAMS_DIR / f"{name}.svg"
        png_path = API_DIAGRAMS_DIR / f"{name}.png"

        mmd_path.write_text(content, encoding="utf-8")
        print(f"  Written {name}.mmd")

        # Render SVG
        subprocess.run(
            ["npx", "--yes", "@mermaid-js/mermaid-cli", "-i", str(mmd_path), "-o", str(svg_path)],
            check=True
        )
        print(f"  Rendered {name}.svg")

        # Render PNG
        subprocess.run(
            ["npx", "--yes", "@mermaid-js/mermaid-cli", "-i", str(mmd_path), "-o", str(png_path), "-b", "white", "-s", "2"],
            check=True
        )
        print(f"  Rendered {name}.png")

    print("All API workflow diagrams successfully generated!")

if __name__ == "__main__":
    main()
