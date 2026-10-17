# Major Project: Intelligent Portfolio Creation via Agentic AI

## Overview
An application-oriented Agentic AI framework for intelligent portfolio creation by capturing the experience of Indian mutual fund managers.

## Architecture
- **7 Agents**: 4 Data Ingestion (Market, News, Macro, MFKG) + 3 Reasoning Triad (Strategist, Critic, Moderator)
- **LangGraph** orchestration separating LLM reasoning from deterministic Python math
- **Neo4j MFKG** for episodic memory of expert fund manager behavior
- **FAISS** for historical news grounding
- **FastAPI** backend + **Next.js** frontend

## Tech Stack
- Python 3.11+, FastAPI, LangGraph, Neo4j, PostgreSQL, Redis, FAISS
- Gemini 2.5 Flash (free tier) / Llama 3.1 8B (local fallback)
- Next.js 14, Tailwind CSS, Recharts

## Quick Start
```bash
# 1. Set up environment
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# 2. Start services
docker-compose up -d  # Neo4j, PostgreSQL, Redis

# 3. Download data
python data/scripts/download_amfi.py
python data/scripts/download_prices.py

# 4. Build knowledge graph
python data/scripts/build_mfkg.py

# 5. Run backend
cd backend && uvicorn main:app --reload

# 6. Run frontend
cd frontend && npm install && npm run dev
```

## Project Structure
See `docs/architecture.md` for full details.
