
# MichaelChablerL2: Project Portfolio

This repository consolidates five major projects developed from January 2026 to present. Each project is organized in its own subdirectory and represents a unique technical and product challenge.

---

## Executive Summary

This monorepo is a showcase of advanced, production-grade projects spanning data analytics, language learning, privacy, music discovery, and enterprise log management. Each project is self-contained and demonstrates modern engineering, thoughtful product design, and a focus on real-world impact.

---

## Project Overviews

### 1. AI-Grid-Infrastructure
**A real-time energy grid dashboard and analytics platform.**
Visualizes and analyzes live data from ERCOT (Texas) and ISO-NE (New England) using a FastAPI backend and Streamlit dashboard. Features robust API integrations, real-time data pipelines, and a modular Python codebase for energy market research and operations.

### 2. BabbleClone (LingoVision)
**A visual-first language learning MVP.**
Immersive Spanish vocabulary lessons using images and audio, with no translation crutch. Features a modern React/Tailwind UI, audio-visual learning flow, and a Node.js/Express/Supabase backend. Designed for rapid, intuitive language acquisition.

### 3. punkt_project (Punkt)
**A Splunk-inspired enterprise log analysis platform.**
Real-time log aggregation, advanced search, and beautiful analytics dashboards. Built for multi-tenant environments with sub-500ms streaming, a custom query language, and a premium React/TypeScript UI. Backend powered by FastAPI, PostgreSQL, and Redis.

### 4. Discografy
**A music discovery and curation platform.**
Empowers human curators and discovery-hungry fans to find new artists before they go mainstream. Features a random discovery engine, curated "crates," and a business model focused on exclusivity and taste leadership. Built with vanilla JS, Electron, and Firebase.

### 5. frodo (Ghost)
**A privacy threat scanning tool for everyday users.**
Alerts users to digital spaces where their personal information is at risk. Designed for non-technical users to reclaim their digital identity and reduce online exposure. Features a user-friendly interface and actionable privacy insights.

---

## Technical Breakdown

### AI-Grid-Infrastructure
**Stack:** Python 3.11+, FastAPI, Streamlit, Pydantic, pytest

- Real-time data ingestion from ERCOT and ISO-NE
- FastAPI backend with documented REST endpoints
- Streamlit dashboard for live visualization
- Modular code: api/, panels/, scripts/, tests/
- Environment-based config and .env support
- Example endpoints: `/ercot/prices`, `/isone/lmp/realtime`, `/ercot/frequency`

**Quickstart:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
streamlit run streamlit_app/app.py
```

---

### BabbleClone (LingoVision)
**Stack:** React 17, Vite, Tailwind CSS, Framer Motion, Zustand, Node.js, Express, Supabase (PostgreSQL)

- Visual-first deciphering engine (image + audio, then word reveal)
- Responsive, mobile-friendly UI with animations
- REST API backend with public read access (RLS)
- Supabase for persistent lesson and card data
- End-to-end browser testing with Playwright

**Architecture:**
```
React Frontend (Vite) → Express Backend (Node.js) → Supabase (PostgreSQL)
```

---

### punkt_project (Punkt)
**Stack:** React 18, TypeScript, Vite, Tailwind CSS, Recharts, FastAPI, PostgreSQL, Redis, Docker

- Real-time log streaming (sub-500ms latency)
- Advanced search with custom query language
- Interactive analytics: time-series, aggregation charts
- Row-Level Security for multi-tenant data
- Chunked ingestion for large log files
- Modern, glassmorphism-inspired UI
- Full OpenAPI docs and robust test suites

**Quickstart:**
```bash
docker-compose up --build
# or run frontend/backend separately
```

---

### Discografy
**Stack:** Vanilla JS, HTML/CSS, Electron, Firebase (Firestore/Auth/Storage)

- Human-curated music discovery (not algorithmic)
- Curator network effects and exclusive artist pipeline
- Random discovery engine and curated "crates"
- One-tap download for "real music"
- Firebase integration for data and auth
- Electron desktop wrapper and web demo

**Business Model:**
- Taste leadership, exclusivity, and viral curator sharing
- Optimized LTV:CAC ratio and phased path to profitability

---

### frodo (Ghost)
**Stack:** (See project for details)

- Alerts users to privacy threats and exposures
- Scans digital spaces for personal data risks
- Designed for non-technical users
- Executive summary and vision focused on digital identity protection

---

## Usage

Each project is self-contained in its respective folder. See the README or documentation inside each subdirectory for project-specific setup, usage, and contribution instructions.

---

## About

This repository was created to centralize and document all major projects developed in early 2026. For questions or contributions, please open an issue or pull request.
