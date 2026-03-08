# Punkt - Enterprise Log Analysis Platform

Punkt is a modern, high-performance log aggregation and analysis platform designed for enterprise multi-tenant environments. It provides real-time streaming, advanced search capabilities, and beautiful visualizations to help teams monitor and debug their infrastructure.

![Punkt Dashboard Mockup](https://raw.githubusercontent.com/placeholder-logo.png) <!-- Replace with real image if available -->

## 🚀 Features

- **Real-time Live Feed**: Sub-500ms latency log streaming with pause/resume functionality and unread log notifications.
- **Advanced Search**: Powerful query language with field-level filters and instantaneous results via TanStack Virtualization.
- **Visual Analytics**: Interactive time-series and aggregation charts powered by Recharts.
- **Enterprise Security**: Row-Level Security (RLS) at the database layer ensuring strict tenant isolation.
- **Chunked Ingestion**: Handle large log files reliably with multi-chunk parallel-ready upload and progress tracking.
- **Modern UI**: A premium, "glassmorphism" inspired dashboard with smooth transitions and responsive design.

## 🛠️ Tech Stack

### Frontend
- **React 18** + **TypeScript**
- **Vite** for lightning-fast builds
- **Tailwind CSS** for modern, utility-first styling
- **Recharts** for performant visualizations
- **TanStack Virtual** for handling massive log datasets
- **Vitest** + **Testing Library** for robust unit testing

### Backend
- **FastAPI** (Python 3.11+)
- **PostgreSQL 15** with Partitioning & RLS
- **Redis 7** for real-time caching and pub/sub
- **Alembic** for schema migrations

## 📦 Getting Started

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker & Docker Compose

### Quick Start (Docker)
The easiest way to run the full stack:

```bash
docker-compose up --build
```

Access the dashboard at `http://localhost:5173` and the API at `http://localhost:8000`.

### Development Setup

#### Frontend
```bash
cd punkt-frontend
npm install
npm run dev
```

#### Backend
```bash
cd punkt-backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 🔑 Default Credentials

The demo user is seeded automatically by Alembic migrations:

| Username | Password | Tenant |
|----------|----------|--------|
| `demo@acme.com` | `demo123` | `tenant_acme` |

To seed additional users for integration tests:
```bash
cd punkt-backend
python -m scripts.seed_test_users
```

## 🔍 Query Syntax Reference

The Punkt query language supports field filters, text search, and pipe commands.

### Basic Filters
```
level=ERROR                          filter by field (exact match)
level!=DEBUG                         not equal
timestamp>2025-02-07T00:00:00Z      comparison operators
source=nginx level=ERROR             implicit AND (multiple filters)
"connection refused"                 full-text search on message field
```

### Aggregations & Modifiers
```
level=ERROR | stats count by source  count by group
| stats avg response_time by source  aggregate a numeric field
| head 50                            limit to 50 results
| sort timestamp desc                sort results
```

**Operators:** `=`  `!=`  `>`  `<`  `>=`  `<=`

**Pipe commands:** `stats`, `head`, `sort`

**Stats functions:** `count`, `sum`, `avg`, `min`, `max`

## 🌐 API Reference

All endpoints require `Authorization: Bearer <token>` except `/api/auth/login`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login — returns JWT token |
| GET | `/api/auth/me` | Current user info |
| POST | `/api/ingest/json` | Ingest batch of JSON logs |
| POST | `/api/ingest/file/init` | Initialize chunked file upload |
| POST | `/api/ingest/file/chunk` | Upload a file chunk |
| POST | `/api/ingest/file/complete` | Finalize upload & process |
| GET | `/api/search?q=...&limit=100` | Search logs (query string) |
| POST | `/api/search/query` | Search logs (JSON body) |
| GET | `/api/stats/overview` | Dashboard stats summary |
| GET | `/api/sources` | List log sources with metadata |
| WS | `/ws/{tenant_id}?token=...` | Real-time log stream |

Full OpenAPI docs available at `http://localhost:8000/docs` when the backend is running.

## 🧪 Testing

Run the frontend test suite:
```bash
cd punkt-frontend
npm test
```

Run backend unit tests (no external services required):
```bash
cd punkt-backend
pytest tests/test_query_parser.py tests/test_ws_backpressure.py -v
```

Run backend integration tests (requires PostgreSQL + Redis):
```bash
cd punkt-backend
pytest tests/test_api.py -v
```

## 📄 License
Internal Development - Proprietary
