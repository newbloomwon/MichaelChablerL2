# ARCHITECTURE.md

## Overview

Punkt is a B2B enterprise log aggregation and analysis platform designed for multi-tenant environments. This document describes the high-level architecture, technology decisions, and key design patterns that form the foundation of the system.

**Core Design Principles:**
- **Multi-tenancy with strong isolation** - Row-Level Security (RLS) at the database layer ensures complete data separation between tenants without application-level filtering
- **Real-time first** - WebSocket streaming enables sub-500ms latency for live log viewing
- **Time-series optimized** - PostgreSQL partitioning by month enables efficient querying of time-bounded log data
- **Memory-conscious** - Chunked uploads and capped Redis lists prevent memory exhaustion under high load
- **Standardized contracts** - Uniform API envelope format simplifies frontend error handling and debugging

---

## 1. Architecture Overview

### 1.1 High-Level System Architecture

```
                                    ┌─────────────────────────────────────┐
                                    │         Client Layer                │
                                    │  ┌─────────────────────────────┐    │
                                    │  │   React SPA (TypeScript)    │    │
                                    │  │   - Tailwind CSS styling    │    │
                                    │  │   - Recharts visualization  │    │
                                    │  │   - TanStack Virtual tables │    │
                                    │  └─────────────┬───────────────┘    │
                                    └───────────────┬┼───────────────────┘
                                                    ││
                              HTTP/REST ────────────┘│
                              (JSON over HTTPS)       │
                                                      │ WebSocket
                              ┌───────────────────────┴─────────────────────┐
                              │                API Gateway Layer             │
                              │  ┌─────────────────────────────────────────┐ │
                              │  │            FastAPI Application          │ │
                              │  │                                         │ │
                              │  │  ┌───────────────────────────────────┐  │ │
                              │  │  │       Tenant Middleware           │  │ │
                              │  │  │  - JWT validation                 │  │ │
                              │  │  │  - Sets app.current_tenant        │  │ │
                              │  │  │  - RLS context injection          │  │ │
                              │  │  └───────────────────────────────────┘  │ │
                              │  │                    │                    │ │
                              │  │  ┌─────────┬───────┴──────┬──────────┐  │ │
                              │  │  │         │              │          │  │ │
                              │  │  ▼         ▼              ▼          ▼  │ │
                              │  │ ┌────┐  ┌─────┐   ┌──────────┐  ┌────┐ │ │
                              │  │ │Auth│  │Ingest│  │WebSocket │  │Query│ │
                              │  │ │API │  │ API  │  │ Manager  │  │Engine│ │
                              │  │ └────┘  └─────┘   └──────────┘  └────┘ │ │
                              │  │                                         │ │
                              │  └─────────────────────────────────────────┘ │
                              └───────────────────────────────────────────────┘
                                                    │
                              ┌──────────────────────┴────────────────────────┐
                              │              Data Layer                       │
                              │                                               │
                              │  ┌─────────────────────────────────────────┐  │
                              │  │             PostgreSQL 15               │  │
                              │  │  ┌───────────────────────────────────┐  │  │
                              │  │  │  log_entries (Partitioned Table)  │  │  │
                              │  │  │  ├── log_entries_2025_02          │  │  │
                              │  │  │  ├── log_entries_2025_03          │  │  │
                              │  │  │  └── log_entries_default          │  │  │
                              │  │  └───────────────────────────────────┘  │  │
                              │  │  Row-Level Security: tenant_isolation   │  │
                              │  └─────────────────────────────────────────┘  │
                              │                                               │
                              │  ┌─────────────────────────────────────────┐  │
                              │  │               Redis 7                   │  │
                              │  │  - Recent logs cache (capped lists)     │  │
                              │  │  - WebSocket connection tracking        │  │
                              │  │  - Query result cache (TTL-based)       │  │
                              │  └─────────────────────────────────────────┘  │
                              │                                               │
                              │  ┌─────────────────────────────────────────┐  │
                              │  │           Alembic Migrations            │  │
                              │  │  - Version-controlled schema changes    │  │
                              │  │  - Partition creation automation        │  │
                              │  └─────────────────────────────────────────┘  │
                              └───────────────────────────────────────────────┘
```

### 1.2 Request Flow Diagram

```
                                 User Action
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              React Application                               │
│                                                                              │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────────┐ │
│   │  Auth       │    │  Axios      │    │  WebSocket Hook                 │ │
│   │  Context    │───▶│  Client     │    │  - Auto-reconnection            │ │
│   │  (JWT)      │    │  (REST)     │    │  - last_seen_id tracking        │ │
│   └─────────────┘    └──────┬──────┘    └───────────────┬─────────────────┘ │
└─────────────────────────────┼───────────────────────────┼───────────────────┘
                              │                           │
                              │ HTTP + Bearer Token       │ WS + Bearer Token
                              ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             FastAPI Backend                                  │
│                                                                              │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │                      Tenant Middleware                                 │ │
│   │  1. Extract JWT from Authorization header                              │ │
│   │  2. Validate token signature and expiration                            │ │
│   │  3. Extract tenant_id from token claims                                │ │
│   │  4. SET app.current_tenant = '{tenant_id}'  ◀── RLS Context            │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│                              │                                               │
│         ┌────────────────────┼────────────────────┐                         │
│         ▼                    ▼                    ▼                         │
│   ┌──────────┐        ┌───────────┐        ┌───────────┐                   │
│   │ Ingestion│        │   Query   │        │ WebSocket │                   │
│   │ Handler  │        │  Handler  │        │  Manager  │                   │
│   └────┬─────┘        └─────┬─────┘        └─────┬─────┘                   │
│        │                    │                    │                          │
└────────┼────────────────────┼────────────────────┼──────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PostgreSQL 15                                      │
│                                                                              │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │                   Row-Level Security Policy                            │ │
│   │   CREATE POLICY tenant_isolation_policy ON log_entries                 │ │
│   │       FOR ALL                                                          │ │
│   │       USING (tenant_id = current_setting('app.current_tenant', true)); │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│   All queries automatically filtered by tenant_id - no manual WHERE needed   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

### 2.1 Backend Stack

| Technology | Version | Purpose | Why This Choice |
|------------|---------|---------|-----------------|
| **FastAPI** | Latest | Web framework | Async-first, automatic OpenAPI docs, excellent performance, type safety with Pydantic |
| **Python** | 3.11+ | Runtime | Pattern matching, performance improvements, better async support |
| **PostgreSQL** | 15 | Primary database | Native partitioning, Row-Level Security, JSONB for flexible metadata, mature and reliable |
| **Redis** | 7 | Caching & pub/sub | Capped lists for memory-bounded caching, connection tracking for WebSockets |
| **Alembic** | Latest | Migrations | SQLAlchemy-native, version control for schema, supports raw SQL for complex DDL |
| **asyncpg** | Latest | DB driver | Native async PostgreSQL driver, significantly faster than psycopg2 for async workloads |
| **python-jose** | Latest | JWT handling | Industry standard JWT library, supports RS256/HS256 algorithms |

### 2.2 Frontend Stack

| Technology | Version | Purpose | Why This Choice |
|------------|---------|---------|-----------------|
| **React** | 18 | UI framework | Concurrent rendering, automatic batching, Suspense for data fetching |
| **TypeScript** | 5+ | Type safety | Compile-time error detection, better IDE support, self-documenting code |
| **Vite** | Latest | Build tool | Near-instant HMR, ESM-native, significantly faster than webpack for development |
| **Tailwind CSS** | 3 | Styling | Utility-first, consistent design system, eliminates CSS specificity issues |
| **Recharts** | Latest | Charting | React-native, composable, good performance with large datasets |
| **TanStack Virtual** | Latest | Virtualization | Essential for rendering 100K+ log entries without browser performance degradation |
| **React Router** | v6 | Routing | Nested routes, loader patterns, industry standard |
| **Axios** | Latest | HTTP client | Interceptors for auth tokens, automatic JSON parsing, request/response transformation |

---

## 3. Core Design Patterns

### 3.1 Multi-tenancy with Row-Level Security

PostgreSQL RLS provides database-enforced tenant isolation - the most secure approach.

```
Request arrives with JWT
    │
    ▼
Middleware extracts tenant_id
    │
    ▼
SET app.current_tenant = '{tenant_id}' (PostgreSQL session variable)
    │
    ▼
All queries automatically filtered by RLS policy
(No WHERE clauses needed in application code)
    │
    ▼
Queries execute only on data matching current tenant
```

### 3.2 Chunked File Upload

Prevents memory exhaustion when handling large files.

```
POST /api/ingest/file/init
    │ Returns upload_id
    ▼
POST /api/ingest/file/chunk (repeat for each chunk)
    │ Store to temp file, never hold in memory
    ▼
POST /api/ingest/file/complete
    │ Trigger async parsing
    ▼
Background worker processes file stream
    │ Parses logs, inserts to database, updates Redis
    ▼
Response to user: processing_status
```

### 3.3 API Response Envelope

All responses use consistent structure for predictable error handling.

```json
{
  "success": true/false,
  "data": { ... } or null,
  "error": { "code": "...", "message": "..." } or null,
  "timestamp": "ISO8601"
}
```

---

## 4. Database Schema

### 4.1 Partitioned Log Entries Table

```sql
CREATE TABLE log_entries (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,
    source VARCHAR(100),
    level VARCHAR(20),
    message TEXT,
    raw_log TEXT,
    metadata JSONB,
    indexed_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);
```

**Key Design Decisions:**
- Partitioned by month for query performance and data lifecycle management
- JSONB metadata for flexible schema without migrations
- Composite primary key (id, timestamp) required for partitioning
- RLS policy ensures tenant_id filtering on all queries

### 4.2 Indexes

| Index | Purpose |
|-------|---------|
| `idx_log_entries_timestamp` | Fast time-range queries, recent logs first |
| `idx_log_entries_tenant_time` | RLS + time queries (most common pattern) |
| `idx_log_entries_level` | Filter by log level (ERROR, WARN, etc.) |
| `idx_log_entries_source` | Filter by source file/application |
| `idx_log_entries_metadata` (GIN) | JSONB field queries |

---

## 5. API Contract

### 5.1 Standard Response Envelope

**Success Response:**
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2025-02-07T14:23:01Z"
}
```

**Error Response:**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid timestamp format",
    "details": { "field": "timestamp" }
  },
  "timestamp": "2025-02-07T14:23:01Z"
}
```

### 5.2 Core Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/login` | POST | Returns JWT token |
| `/api/ingest/json` | POST | Batch insert logs |
| `/api/ingest/file/init` | POST | Start chunked upload |
| `/api/ingest/file/chunk` | POST | Upload single chunk |
| `/api/ingest/file/complete` | POST | Finalize and process |
| `/api/search` | GET | Execute query |
| `/api/stats/overview` | GET | Dashboard metrics |
| `/ws/{tenant_id}` | WS | Real-time log stream |

---

## 6. Real-time Architecture

### 6.1 WebSocket Design

- **Endpoint:** `/ws/{tenant_id}`
- **Authentication:** JWT token via query parameter (`?token=...`)
- **Connection:** Persistent TCP connection managed by FastAPI WebSocket
- **Heartbeat:** Ping every 30s, pong required within 10s (disconnects on timeout)
- **Backpressure Strategy:**
  - Per-client bounded asyncio.Queue with MAX_QUEUE_SIZE = 100 messages
  - Queue warning logged when 80%+ full (80 messages)
  - When queue reaches 100: oldest message dropped, SLOW_CLIENT warning queued
  - After 10 consecutive drops: client forcefully disconnected with code 4002
  - Consecutive drop counter resets to 0 on successful send
- **Dedicated Sender Loop:** Each client has its own coroutine draining queue to WebSocket asynchronously
- **ClientState Tracking:** Consolidated per-client state including queue, tasks, dropped message counts, filters, connection time

### 6.2 Message Types

```json
// Server → Client: New log entry
{"type": "log", "data": {...}}

// Server → Client: Heartbeat
{"type": "ping", "timestamp": "ISO8601"}

// Client → Server: Heartbeat response
{"type": "pong"}

// Server → Client: Slow client warning
{"type": "warning", "code": "SLOW_CLIENT", "dropped_count": 15}

// Client → Server: Subscribe with filters
{"type": "subscribe", "filters": {"level": ["ERROR"], "source": "/var/log/app"}}

// Server → Client: Subscription confirmed
{"type": "subscribed", "filters_applied": {...}}

// Server → Client: Reconnection acknowledgment
{"type": "reconnect_ack", "last_seen_id": 12344, "missed_count": 5}

// Server → Client: Batch of log entries
{"type": "log_batch", "data": [...], "count": 100}
```

### 6.3 Broadcast Service

The broadcast service bridges ingestion pipelines with WebSocket clients:

```python
# Single log broadcast (used by direct ingestion)
await broadcast_log(tenant_id, log_entry)

# Batch broadcast (preferred for high-volume, used by file processing)
await broadcast_batch(tenant_id, log_entries)
```

**Integration Points:**
- `app/api/ingest.py`: Calls `broadcast_log()` for each directly ingested log
- `app/workers/processor.py`: Calls `broadcast_batch()` after each database batch insert
- Both use non-fatal error handling (log warning but continue)
- Backpressure is handled by the manager's queue system

---

## 7. Caching Strategy

### 7.1 Redis Data Structures

| Key | Type | TTL | Purpose |
|-----|------|-----|---------|
| `logs:recent:{tenant_id}` | List | 15 min | Recent logs for live feed |
| `query:cache:{hash}` | String (JSON) | 5 min | Query result cache |
| `ws:connections:{tenant_id}` | Set | None | Active WebSocket connections |

### 7.2 Caching Decisions

- **Recent logs:** LPUSH/LTRIM pattern with max 1000 entries
- **Query results:** 5-minute TTL balances freshness with performance
- **No cache invalidation:** By design; 5-min staleness acceptable for dashboards

---

## 8. Query Engine

### 8.1 MVP Query Grammar

```
query := search_terms [ "|" command ]?

search_terms := search_term [ search_term ]*    // Implicit AND

search_term :=
    | text_search           // "error"
    | field_filter          // level=ERROR

field_filter := field_name operator value
operator := "=" | "!=" | ">" | "<" | ">=" | "<="

command :=
    | "stats" aggregation_func "by" field_name
    | "head" number
    | "tail" number
    | "sort" field_name ["asc" | "desc"]

aggregation_func := "count" | "sum" | "avg" | "min" | "max"
```

### 8.2 Example Query Translation

```
User:   level=ERROR source=/var/log/app | stats count by source

SQL:    SELECT source, COUNT(*) as count
        FROM log_entries
        WHERE level = 'ERROR'
          AND source = '/var/log/app'
          AND timestamp BETWEEN $1 AND $2
        -- RLS automatically adds:
        AND tenant_id = 'tenant_abc'
        GROUP BY source
```

---

## 9. Security Architecture

### 9.1 Implemented Security Measures

✓ Row-Level Security (PostgreSQL) - Tenant isolation at database level
✓ JWT Authentication - 24-hour token expiration
✓ CORS Configuration - Restricted to known origins
✓ Input Validation - Pydantic models for all requests
✓ Query Parameterization - No string concatenation in SQL

### 9.2 Known MVP Limitations

| Issue | Status | Production Remediation |
|-------|--------|----------------------|
| JWT secret in docker-compose | ⚠️ | Use secrets management (Vault) |
| No rate limiting | ⚠️ | Add API gateway rate limiting |
| Plaintext demo passwords | ⚠️ | Implement bcrypt hashing |
| No HTTPS | ⚠️ | TLS termination at load balancer |
| No audit logging | ⚠️ | Add request logging for compliance |

---

## 10. Deployment Architecture

### 10.1 Docker Compose Stack

```yaml
services:
  postgres:
    - PostgreSQL 15 with volumes
    - Health checks

  redis:
    - Redis 7
    - maxmemory: 256MB
    - maxmemory-policy: allkeys-lru

  backend:
    - FastAPI application
    - Runs migrations on startup

  frontend:
    - nginx serving SPA
    - SPA routing configured
```

### 10.2 Development Workflow

```
Local development:
  Backend: uvicorn --reload (hot reloading)
  Frontend: npm run dev (Vite HMR)
  Infrastructure: docker-compose (postgres, redis)

Production-ready demo:
  docker-compose up --build
  All services start automatically
  Migrations run on backend startup
```

---

## 11. Performance Considerations

### 11.1 Query Performance Targets

| Operation | Target | Optimization |
|-----------|--------|---------------|
| Query 100K logs | <2s | Indexes, partitioning, caching |
| File upload (100MB) | <5s | Chunked upload, streaming |
| WebSocket latency | <500ms avg, <2s 99th percentile | Backpressure queue, dedicated sender loop |
| Dashboard render | <1s | Cached metrics, virtualization |
| Message broadcast to 100 clients | <100ms | Non-blocking queue.put_nowait() |

### 11.2 Scaling Limits (MVP)

- **Single instance:** ~100 concurrent WebSocket connections (bounded by backpressure queue limits)
- **PostgreSQL:** 1M log entries (monthly partitions)
- **Redis:** 1000 recent logs per tenant
- **File upload:** 100MB maximum
- **WebSocket backpressure:** 100 messages queued per client (configurable, prevents memory exhaustion)

---

## 12. Key Design Decisions

### 12.1 Why RLS over Application Filtering?

**Defense in depth:** Database enforces isolation even if app code has bugs

### 12.2 Why Chunked Upload?

**Memory safety:** 1MB chunks prevent server from holding large files in memory

### 12.3 Why WebSocket over SSE?

**Bidirectional:** Clients can send filter subscriptions, not just receive

### 12.4 Why Simplified Query Language?

**Timeline:** Full parser would take 3+ days; MVP is 1 day and sufficient for demonstration

### 12.5 Why FastAPI over Django?

**Native async:** Essential for WebSocket and efficient database operations

### 12.6 Why Bounded Queue with Message Dropping over Flow Control?

**Scalability vs. Latency Trade-off:**
- **Flow control (backoff)** would wait for slow clients, causing cascading timeouts for all clients
- **Bounded queue with dropping** serves fast clients immediately, gracefully degrades for slow ones
- **Per-client isolation** means one slow client doesn't affect others
- **Warning messages** alert clients to their slowness, enabling client-side optimization
- **Automatic disconnection** after 10 consecutive drops prevents resource accumulation

**Implementation Details:**
- Dedicated sender loop per client prevents shared writer contention
- Non-blocking queue.put_nowait() ensures broadcast latency stays <100ms
- Consecutive drop counter resets on successful send (recoverable degradation)
- Configuration values (MAX_QUEUE_SIZE, thresholds) are tunable for different workloads

---

*Architecture Document Version: 2.0*
*Last Updated: February 10, 2025*
*Major Update: Day 4 - WebSocket backpressure and broadcaster service*
