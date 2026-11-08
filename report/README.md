# Lucid — Final Major Project Report (IT898)
## Master of Technology in Information Technology, NITK Surathkal

**Candidate:** Ankur Patel (Roll No. 252IT004)  
**Supervisor:** Dr. Biju R Mohan  
**Department:** Department of Information Technology, National Institute of Technology Karnataka, Surathkal  
**Academic Year:** 2026–2027  
**Compiled Document:** `Final_Major_Project_Report.pdf` (130 Pages, Publication-Grade PDF, concludes at References)

---

## 1. Directory Structure

```text
report/
├── main.tex                           # Master LaTeX document defining NITK layout, geometry, front matter
├── references.bib                     # Academic BibTeX citations (Markowitz, Sharpe, Fama-French, etc.)
├── Final_Major_Project_Report.pdf     # Primary compiled thesis document (130 pages, ends at References)
├── chapters/                          # 12 Core Academic Chapters
│   ├── ch1_introduction.tex           # Introduction, retail dilemma, motivation, contributions
│   ├── ch2_market_survey.tex          # Literature review & competitive analysis (7 platforms)
│   ├── ch3_hld.tex                    # High-Level Design (7 subsystems, 6 user journeys)
│   ├── ch4_lld.tex                    # Low-Level Design (Frontend, backend, 13-node LangGraph)
│   ├── ch5_database_design.tex        # 63 PostgreSQL tables across 8 domains + ER diagrams
│   ├── ch6_system_architecture.tex    # 8-layer system architecture & technical stack
│   ├── ch7_methodology.tex            # Mathematical methodology, SLSQP, integer lots, HHI
│   ├── ch8_dataset.tex                # Ingested datasets, NSE/BSE feeds, multi-agent payloads
│   ├── ch9_api_contract.tex           # 82 REST endpoints, Pydantic schemas, sequence flows
│   ├── ch10_work_done.tex             # Comprehensive implementation review & UI verification
│   ├── ch11_results_testing.tex       # 216 test cases, quantitative backtests, alpha evaluation
│   └── ch12_conclusion.tex           # Academic contributions, limitations, prioritized roadmap
└── images/                            # 20 High-resolution diagrams, flowcharts, ERDs, and crests
    ├── NITKLogo.jpeg                  # Official NITK Surathkal institutional crest
    ├── 00_master_er_diagram.png       # Complete 63-table master ER diagram
    ├── 01_identity_and_security_domain.png
    ├── 02_investor_suitability_and_goals_domain.png
    ├── 03_security_master_and_companies_domain.png
    ├── 04_market_data_and_fundamentals_domain.png
    ├── 05_portfolio_engine_and_optimization_domain.png
    ├── 06_broker_integrations_and_orders_domain.png
    ├── 07_demat_diagnosis_and_rebalancing_domain.png
    ├── 08_multi_agent_telemetry_and_auditing_domain.png
    ├── SYSTEM_ARCHITECTURE.png
    ├── AGENTIC_AI_ARCHITECTURE.png
    ├── METHODOLOGY_FLOW.png
    ├── COMPLETE_DATA_FLOW.png
    ├── API_TO_AGENT_DATA_FLOW.png
    ├── NSE_BSE_DATA_FLOW.png
    ├── API_AUTH_FLOW.png
    ├── API_PORTFOLIO_GENERATION_FLOW.png
    ├── API_MONITORING_REBALANCE_FLOW.png
    ├── API_DIAGNOSIS_FLOW.png
    ├── ui_landing_dashboard.png
    └── ui_portfolio_allocation.png
```

---

## 2. Compilation Instructions

The report requires **pdfLaTeX** and **BibTeX** (available in TeX Live, MacTeX, or MikTeX).

To recompile the document cleanly from scratch, execute:

```bash
cd report

# First pass: compile document structure and generate aux files
pdflatex -interaction=nonstopmode main.tex

# Second pass: resolve academic citations via BibTeX
bibtex main

# Third pass: incorporate bibliography and update internal cross-references
pdflatex -interaction=nonstopmode main.tex

# Fourth pass: lock in page numbers for Table of Contents, LOF, and LOT
pdflatex -interaction=nonstopmode main.tex

# Copy output to root directory
cp main.pdf ../Final_Major_Project_Report.pdf
```

---

## 3. Institutional Formatting Adherence

The LaTeX structure in `main.tex` strictly follows the NITK Surathkal M.Tech dissertation guidelines:
1. **Paper & Geometry**: A4 twoside with `top=1.5in, bottom=1in, left=1.5in, right=1in`. Chapters open on right-hand (`openright`) odd pages with inner margin `1.65in`.
2. **Title Page**: Official NITK Surathkal emblem (`NITKLogo.jpeg`), course code `IT898`, candidate name and roll number (`252IT004`), guide name (`Dr. Biju R Mohan`), and departmental credits.
3. **Framed Front Matter**: Institutional framed **Declaration** and framed **Certificate** with guide and DPGC Chairman signatures.
4. **Roman Page Numbering**: Roman numerals (`i`, `ii`, `iii`...) for Abstract, Contents, List of Figures, List of Tables, and Abbreviations.
5. **Intentional Blank Page**: Formatted empty page prior to Chapter 1 ensuring that Chapter 1 begins on Arabic page 1 on an odd page.
6. **Report Conclusion**: The document terminates cleanly with Chapter 12 and the formal **REFERENCES** bibliography.
