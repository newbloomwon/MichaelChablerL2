# AGENTS.md

## Team Overview

The Punkt project is developed by a 2-person team executing a 1-week MVP sprint. This document defines roles, responsibilities, and coordination guidelines for Claude-assisted development workflows.

**Project:** Punkt - Enterprise Log Aggregation & Analysis Platform
**Timeline:** 1 Week Sprint (Feb 7-13, 2025)
**Team Size:** 2 Developers

---

## Agent Profiles

### Beatrice

- **Name**: Beatrice
- **Role**: Backend Developer
- **Primary Focus**: FastAPI backend, PostgreSQL data layer, real-time infrastructure, and authentication systems
- **Key Deliverables**:
  - FastAPI application setup with Alembic migrations
  - PostgreSQL schema with partitioning and Row-Level Security (RLS)
  - Redis integration with capped lists for caching
  - Ingestion API (chunked file upload + JSON batch)
  - Log parsers (JSON + nginx formats)
  - Query parser and executor (MVP grammar)
  - WebSocket manager with heartbeat and backpressure handling
  - Authentication middleware with RLS tenant context
  - Test data generation script (`scripts/generate_test_data.py`)
- **Expertise**:
  - Python 3.11+ / FastAPI / asyncio / asyncpg
  - PostgreSQL 15 (partitioning, RLS, indexes)
  - Redis 7 (caching patterns, pub/sub)
  - JWT authentication (python-jose)
  - WebSocket protocol implementation
  - Database migrations (Alembic)
  - Query language parsing
  - pytest for testing
- **Availability/Hours**: Full-time during sprint (Days 1-7)
- **Communication Preference**: Technical discussions via code reviews and API contract documentation

### Michael

- **Name**: Michael
- **Role**: Frontend Developer
- **Primary Focus**: React application, user interface, data visualization, and real-time WebSocket integration
- **Key Deliverables**:
  - React application scaffold (TypeScript + Vite)
  - Layout components (header, sidebar, main layout)
  - Authentication UI and context management
  - Dashboard page with metric cards + time-series charts
  - Search page with query bar + virtualized results table
  - Live feed with pause auto-scroll functionality (early priority)
  - WebSocket hook with reconnection logic and last_seen_id tracking
  - Source management page
  - Responsive styling with Tailwind CSS
  - CSV export functionality
- **Expertise**:
  - React 18 / TypeScript
  - Vite build tooling
  - State management (React Context + Hooks)
  - React Router v6
  - Axios HTTP client
  - Native WebSocket API
  - Recharts for data visualization
  - Tailwind CSS
  - TanStack Virtual for virtualized tables
- **Availability/Hours**: Full-time during sprint (Days 1-7)
- **Communication Preference**: UI mockups and component specifications

---

## Communication & Coordination Guidelines

### Daily Integration Points

Each day includes a scheduled integration milestone to verify frontend-backend compatibility:

| Day | Integration Checkpoint |
|-----|------------------------|
| 1 | Test login flow end-to-end |
| 2 | Upload file, verify stats update |
| 3 | Execute search, display results |
| 4 | Ingest log, verify appears in live feed |
| 5 | Full user journey testing |
| 6 | Docker Compose full stack test |
| 7 | Demo preparation and final deployment test |

### API Contract Coordination

All API responses use a standardized envelope format. Both agents must adhere to this contract:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2025-02-07T14:23:01Z"
}
```

### Shared Resources

- **Test Data**: Beatrice provides `scripts/generate_test_data.py` on Day 1 for Michael to test frontend features
- **API Documentation**: FastAPI auto-generated docs at `/docs` serve as the contract reference
- **WebSocket Protocol**: Documented message types (log, ping, pong, subscribe, subscribed, warning, reconnect_ack)

### Escalation Path

- **Blocked by backend API**: Michael documents required endpoint and notifies Beatrice with expected request/response format
- **Blocked by frontend**: Beatrice can test APIs via curl/Postman using test data script
- **Integration failures**: Both agents participate in joint debugging session

---

## Decision-Making Authority

### Beatrice (Backend)

| Domain | Authority Level |
|--------|-----------------|
| Database schema design | Full |
| API endpoint structure | Full |
| Query language grammar | Full |
| Authentication/authorization logic | Full |
| WebSocket protocol implementation | Full |
| Backend performance optimization | Full |
| Redis caching strategy | Full |
| API response format changes | Requires coordination with Michael |

### Michael (Frontend)

| Domain | Authority Level |
|--------|-----------------|
| UI/UX design decisions | Full |
| Component architecture | Full |
| State management approach | Full |
| Chart/visualization library choices | Full |
| Styling and responsive behavior | Full |
| Frontend build configuration | Full |
| API client implementation | Full |
| API contract changes | Requires coordination with Beatrice |

### Joint Decisions (Both Required)

- Changes to the standardized API envelope format
- WebSocket message schema modifications
- Authentication flow changes
- Docker Compose configuration
- Demo script and presentation

---

## Sprint Schedule Reference

### Day 1: Foundation
- **Beatrice**: FastAPI setup, Alembic, PostgreSQL schema with RLS, `/ingest/json`, JWT auth, test data script
- **Michael**: React/TypeScript/Tailwind setup, layout components, login page, auth context

### Day 2: Core Features
- **Beatrice**: Chunked upload endpoints, log parsers, Redis integration, basic query endpoint
- **Michael**: Dashboard with metrics, API integration, file upload component, pause auto-scroll

### Day 3: Search & Visualization
- **Beatrice**: Query parser (MVP grammar), stats aggregation, WebSocket broadcaster with heartbeat
- **Michael**: Search page, results table with virtualization, Recharts integration

### Day 4: Real-time Features
- **Beatrice**: WebSocket connection manager with backpressure, broadcast with filtering, output modifiers
- **Michael**: Live feed component, WebSocket hook with reconnection, aggregation charts

### Day 5: Polish & Features
- **Beatrice**: Query performance optimization, error handling, edge cases
- **Michael**: Sources page, UI polish, loading states, CSV export

### Day 6: Testing & Deployment
- **Beatrice**: Unit tests (query parser), integration tests, Docker config, migration testing
- **Michael**: Component tests, cross-browser testing, Docker config

### Day 7: Buffer & Demo Prep
- **Both**: Bug fixes, demo script, documentation, final deployment test

---

## Technology Stack Reference

### Backend (Beatrice)
- FastAPI (Python 3.11+)
- PostgreSQL 15 (partitioning, RLS)
- Redis 7
- Alembic (migrations)
- python-jose (JWT)
- asyncpg (async PostgreSQL)
- pytest

### Frontend (Michael)
- React 18 + TypeScript
- Vite
- React Router v6
- Axios
- Recharts
- Tailwind CSS
- TanStack Virtual
