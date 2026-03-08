

# MichaelChablerL2: Project Portfolio

## About Me

I love creating exciting designs that draw people in. I love solving problems.


This repository consolidates five major projects developed from January 2026 to present. Each project is organized in its own subdirectory and represents a unique technical and product challenge.

---



## L2 Builds

Here are the five L2 builds, listed in order from earliest to latest:

1. **frodo (Ghost)**
2. **Discografy**
3. **punkt_project (Punkt)**
4. **BabbleClone (LingoVision)**
5. **AI-Grid-Infrastructure**

---

## Executive Summary

This monorepo is a showcase of advanced, production-grade projects spanning data analytics, language learning, privacy, music discovery, and enterprise log management. Each project is self-contained and demonstrates modern engineering, thoughtful product design, and a focus on real-world impact.

---


## Project Overviews

### 1. frodo (Ghost)

**Solution Overview:**
Ghost is a privacy threat scanning tool that identifies and alerts users to digital spaces where their personal information may be at risk. By providing clear, actionable insights in a user-friendly interface, it empowers non-technical users to proactively protect their digital identity and reduce online exposure.

**Tech Stack:** (See project for details)

**Key Features:**
- Scans digital spaces for privacy threats and exposures
- Alerts users to personal data risks in real time
- User-friendly interface for non-technical audiences
- Actionable recommendations to reduce online exposure

**A privacy threat scanning tool for everyday users.**

Ghost (frodo) empowers everyday users to reclaim their digital identity by moving from total exposure to strategic invisibility. In a world where personal information is constantly at risk, Ghost scans digital spaces and alerts users to potential privacy threats—helping them understand where their data might be exposed or compromised. The tool is designed for non-technical audiences, providing clear, actionable insights and a user-friendly interface. Ghost’s mission is to make privacy protection accessible, proactive, and effective for anyone concerned about their online footprint.

### 2. Discografy

**Solution Overview:**
Discografy is a music discovery platform that connects fans with emerging artists through curated playlists and human tastemakers. By prioritizing taste leadership and exclusivity, it offers a unique, high-engagement alternative to algorithm-driven streaming, helping users find real music before it goes mainstream.

**Tech Stack:** Vanilla JS, HTML/CSS, Electron, Firebase (Firestore/Auth/Storage)

**Key Features:**
- Human-curated music discovery (not algorithmic)
- Curated "crates" and exclusive artist pipeline
- Random discovery engine for active listening
- Social sharing and curator-driven growth

**A music discovery and curation platform.**

Discografy is built for true music lovers—those who crave discovery, not just background noise. Unlike algorithm-driven platforms, Discografy puts human curators at the center, letting genre experts and influencers share their taste and build loyal followings. Fans discover emerging artists through curated "crates" and a high-friction, intentional discovery engine that rewards active listening. The platform’s business model is rooted in exclusivity: artists can offer new releases first on Discografy for higher royalties, while curators drive organic growth by bringing their audiences. With a focus on taste leadership, community, and real music, Discografy aims to reshape how people find and value new sounds.

### 3. punkt_project (Punkt)

**Solution Overview:**
Punkt is an enterprise-grade log aggregation and analysis platform designed for real-time infrastructure monitoring and debugging. It solves the challenge of handling massive log volumes with sub-second latency, advanced search, and secure multi-tenant access, enabling teams to quickly identify and resolve issues.

**Tech Stack:** React 18, TypeScript, Vite, Tailwind CSS, Recharts, FastAPI, PostgreSQL, Redis, Docker

**Key Features:**
- Real-time log streaming with sub-500ms latency
- Advanced search with custom query language
- Interactive analytics and visual dashboards
- Row-Level Security for multi-tenant data
- Chunked ingestion for large log files

**A Splunk-inspired enterprise log analysis platform.**

Punkt is a next-generation log aggregation and analysis platform built for enterprise environments that demand speed, security, and clarity. It streams logs in real time with sub-500ms latency, supports advanced search with a custom query language, and visualizes data through interactive, glassmorphism-inspired dashboards. Designed for multi-tenant use, Punkt enforces strict row-level security and supports chunked ingestion for massive log files. Its architecture combines a React/TypeScript frontend with a FastAPI backend, PostgreSQL for storage, and Redis for real-time features. Punkt empowers teams to monitor, debug, and analyze infrastructure with confidence and style.

### 4. BabbleClone (LingoVision)

**Solution Overview:**
LingoVision (BabbleClone) is a language learning app that immerses users in Spanish vocabulary using images and native audio, eliminating the need for translation. Its unique "thinking gap" method and modern UI make language acquisition intuitive, engaging, and effective for learners of all ages.

**Tech Stack:** React 17, Vite, Tailwind CSS, Framer Motion, Zustand, Node.js, Express, Supabase (PostgreSQL)

**Key Features:**
- Visual-first deciphering engine (image + audio, then word reveal)
- Responsive, mobile-friendly UI with animations
- REST API backend with public read access
- Supabase for persistent lesson and card data

**A visual-first language learning MVP.**

LingoVision (BabbleClone) reimagines language learning by immersing users in Spanish vocabulary lessons that rely solely on images and native audio—no translations, just pure context-driven understanding. The app’s "thinking gap" method encourages direct neural connections between concepts and words, making learning more natural and memorable. With a clean, modern UI, responsive design, and seamless audio-visual flow, users progress through lessons in a way that feels more like play than study. The backend, powered by Node.js and Supabase, ensures fast, secure access to lesson content, while the frontend delivers a delightful, distraction-free experience for learners of all ages.

### 5. AI-Grid-Infrastructure

**Solution Overview:**
AI-Grid-Infrastructure is a real-time dashboard and analytics platform for energy grid data from ERCOT and ISO-NE. It streamlines the process of collecting, visualizing, and analyzing live grid information, supporting energy market research and operational decision-making with reliable, accessible insights.

**Tech Stack:** Python 3.11+, FastAPI, Streamlit, Pydantic, pytest

**Key Features:**
- Real-time data ingestion from ERCOT and ISO-NE
- FastAPI backend with documented REST endpoints
- Streamlit dashboard for live visualization
- Modular, extensible Python codebase

**A real-time energy grid dashboard and analytics platform.**

AI-Grid-Infrastructure delivers real-time energy grid data from ERCOT (Texas) and ISO-NE (New England), providing researchers, analysts, and operators with actionable insights. The platform features a FastAPI backend that ingests and serves live grid data, while a Streamlit dashboard offers intuitive, interactive visualizations. Designed for both rapid prototyping and production use, it supports robust API integrations, modular Python code, and future expansion for additional grids or analytics. The project emphasizes transparency, reliability, and ease of use for energy market professionals and enthusiasts.

---

## Technical Breakdown


### frodo (Ghost)
**Stack:** (See project for details)

- Alerts users to privacy threats and exposures
- Scans digital spaces for personal data risks
- Designed for non-technical users
- Executive summary and vision focused on digital identity protection

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

## Usage

Each project is self-contained in its respective folder. See the README or documentation inside each subdirectory for project-specific setup, usage, and contribution instructions.

---

## About

This repository was created to centralize and document all major projects developed in early 2026. For questions or contributions, please open an issue or pull request.
