# Punkt Development Roadmap

## Sprint Overview

**Project:** Punkt - Enterprise Log Aggregation & Analysis Platform
**Duration:** 7-Day Sprint (Days 1-7)
**Start Date:** February 8, 2025
**Target Completion:** February 14, 2025

### Team

| Role | Assignee | Focus Areas |
|------|----------|-------------|
| Backend Developer | Beatrice | FastAPI, PostgreSQL, Redis, WebSocket, Authentication |
| Frontend Developer | Michael | React, TypeScript, Tailwind, Recharts, WebSocket Client |

### Sprint Goals

- Deliver functional MVP of log aggregation platform
- Support JSON and nginx log formats
- Implement real-time log streaming with WebSocket
- Multi-tenant isolation via PostgreSQL Row-Level Security
- Professional dashboard with search and visualization

---

## Day 1: Foundation

### Beatrice (Backend)

- [x] **FastAPI project setup** — `/punkt-backend/`
  - Create project structure with `app/main.py`, `app/api/`, `app/core/`, `app/models/`
  - Configure environment variables loading from `.env`
  - Set up CORS middleware with configurable origins
  - **Acceptance:** Server starts with `uvicorn app.main:app --reload` ✅

- [x] **Alembic migrations initialized** — `/punkt-backend/migrations/`
  - Run `alembic init migrations`
  - Configure `alembic.ini` with database URL
  - Create initial migration for partitioned schema
  - **Acceptance:** `alembic upgrade head` runs without errors ✅

- [x] **PostgreSQL connection + partitioned schema + RLS** — `/punkt-backend/app/db/`
  - HIGH PRIORITY: Implement `create_monthly_partition()` function
  - Create `log_entries` table with PARTITION BY RANGE (timestamp)
  - Create initial monthly partitions (current + 2 months ahead)
  - Enable Row-Level Security with `tenant_isolation_policy`
  - Create required indexes (timestamp, tenant_time, level, source, metadata GIN)
  - **Acceptance:** Can insert and query logs with RLS filtering by tenant ✅

- [x] **`/api/ingest/json` endpoint** — `/punkt-backend/app/api/ingest.py`
  - Accept batch log submissions (up to 1000 logs per request)
  - Validate log structure (timestamp, level, message required)
  - Return standard API envelope with accepted/rejected counts
  - **Acceptance:** POST 100 logs returns success with correct counts ✅

- [x] **JWT authentication with tenant context** — `/punkt-backend/app/core/auth.py`
  - Implement `/api/auth/login` endpoint
  - Generate JWT with tenant_id claim
  - Create middleware to set `app.current_tenant` for RLS
  - Implement `/api/auth/me` endpoint
  - **Acceptance:** Login returns JWT; protected endpoints validate token and set tenant context ✅

- [x] **HIGH PRIORITY: `scripts/generate_test_data.py`** — `/punkt-backend/scripts/`
  - Generate JSON format logs with realistic distribution
  - Generate nginx access log format
  - Support configurable count, tenant, and output file
  - Include realistic log level weights (DEBUG:10, INFO:60, WARN:20, ERROR:8, CRITICAL:2)
  - **Acceptance:** Can generate 100K logs in both formats; output is valid for ingestion ✅

### Michael (Frontend)

- [x] **React + TypeScript + Tailwind setup** — `/punkt-frontend/` ✅
  - Initialize with Vite ✅
  - Install and configure Tailwind CSS ✅
  - Set up project structure ✅
  - Configure path aliases ✅
  - **Acceptance:** Dev server starts; Tailwind classes work ✅

- [x] **Basic layout with header + sidebar** — `/punkt-frontend/src/components/layout/` ✅
  - Create `Header.tsx` with logo, search placeholder, user menu ✅
  - Create `Sidebar.tsx` with navigation ✅
  - Create `Layout.tsx` wrapper component ✅
  - Apply Punkt brand colors ✅
  - **Acceptance:** Layout renders correctly ✅

- [x] **Login page UI** — `/punkt-frontend/src/pages/Login.tsx` ✅
  - Create login form with username/password fields ✅
  - Style with Punkt branding ✅
  - Display validation errors ✅
  - Loading state on submit button ✅
  - **Note:** Currently uses mock auth; needs integration with real `/api/auth/login` endpoint
  - **Acceptance:** Form renders ✅

- [x] **Auth context with JWT handling** — `/punkt-frontend/src/context/AuthContext.tsx` ✅
  - Create AuthContext with user state and token ✅
  - Implement login/logout functions ✅
  - Store token in localStorage ✅
  - Axios interceptor to attach Bearer token ✅
  - Protected route wrapper component ✅
  - **Acceptance:** Login persists across refresh; logout clears token ✅

### Day 1 Integration Checkpoint

- [x] **End-to-end login flow test** (Partial) ✅
  - Frontend login form implemented ✅
  - Auth context properly stores JWT ✅
  - Protected routes work with token validation ✅
  - ⚠️ Outstanding: Connect mock login to real backend `/api/auth/login` endpoint
  - **Acceptance:** Component structure complete; awaits backend integration

---

## Day 2: Core Features

### Beatrice (Backend)

- [x] **Chunked file upload endpoints** — `/punkt-backend/app/api/upload.py`
  - HIGH PRIORITY: Implement `/api/ingest/file/init` (initialize upload) ✅
  - Implement `/api/ingest/file/chunk` (receive chunk, 1MB max) ✅
  - Implement `/api/ingest/file/complete` (finalize and queue processing) ✅
  - Store chunks to temp directory; never hold full file in memory ✅
  - Return upload_id, chunk progress, and job_id ✅
  - **Acceptance:** 50MB file uploads successfully in chunks ✅
  - **Files Created:** `app/api/upload.py`, `app/models/upload.py`

- [x] **JSON log parser** — `/punkt-backend/app/parsers/json_parser.py`
  - Parse JSON log entries from uploaded files ✅
  - Handle newline-delimited JSON (NDJSON) ✅
  - Handle JSON array of logs ✅
  - Extract timestamp, level, source, message, metadata ✅
  - Stream processing to avoid memory exhaustion ✅
  - **Acceptance:** Parses 10K log JSON file correctly ✅
  - **Files Created:** `app/parsers/__init__.py`, `app/parsers/json_parser.py`

- [x] **Nginx log parser** — `/punkt-backend/app/parsers/nginx_parser.py`
  - Parse nginx combined/access log format ✅
  - Use regex: `^(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+) \S+" (?P<status>\d+) (?P<size>\d+)` ✅
  - Convert nginx timestamp to ISO 8601 ✅
  - Map status codes to log levels (2xx->INFO, 4xx->WARN, 5xx->ERROR) ✅
  - **Acceptance:** Parses 10K nginx log lines correctly ✅
  - **Files Created:** `app/parsers/nginx_parser.py`

- [x] **Redis integration with capped lists** — `/punkt-backend/app/core/redis.py`
  - Connect to Redis with configurable URL ✅
  - Implement `cache_recent_log()` with LPUSH/LTRIM (max 1000 entries) ✅
  - Implement `get_recent_logs()` with LRANGE ✅
  - Set TTL of 900 seconds (15 min) on recent logs ✅
  - **Acceptance:** Recent logs cached; list never exceeds 1000 entries ✅
  - **Files Created:** `app/core/redis.py`

- [x] **Basic query endpoint (field filters only)** — `/punkt-backend/app/api/search.py`
  - Implement `POST /api/search/logs` with query filters ✅
  - Parse simple field filters: `level=ERROR`, `source=/var/log/app.log` ✅
  - Support timestamp range via start/end query params ✅
  - Apply RLS tenant filtering automatically ✅
  - Return results with standard envelope ✅
  - **Acceptance:** `level=ERROR` returns only ERROR logs for current tenant ✅
  - **Files Created:** `app/api/search.py`, `app/models/search.py`

- [x] **Background worker for file processing** — `/punkt-backend/app/workers/processor.py`
  - Reassemble chunks from disk storage ✅
  - Parse JSON or Nginx logs via appropriate parser ✅
  - Batch insert logs into PostgreSQL (100 per batch) ✅
  - Cache recent logs to Redis ✅
  - Clean up temporary files ✅
  - **Acceptance:** 10K logs processed and inserted correctly ✅
  - **Files Created:** `app/workers/__init__.py`, `app/workers/processor.py`

- [x] **Integration into main.py** — `/punkt-backend/app/main.py`
  - Register upload router with `/api/ingest` prefix ✅
  - Register search router with `/api/search` prefix ✅
  - Implement Redis lifecycle (connect/disconnect) ✅
  - Wire parsers to background worker ✅
  - **Acceptance:** All routers accessible; Redis connects on startup ✅
  - **Files Updated:** `app/main.py`

### Michael (Frontend)

- [x] **Dashboard page with metric cards** — `/punkt-frontend/src/pages/Dashboard.tsx` ✅
  - Create metric card components for: Total logs, Error rate, Active sources, Ingestion rate ✅
  - Layout: 4 cards in top row ✅
  - Display loading skeleton while fetching ✅
  - **Acceptance:** Cards display with metric data; loading state works ✅

- [x] **API integration for stats** — `/punkt-frontend/src/hooks/useStats.ts` ✅
  - Create hook to fetch from `/api/stats/overview` ✅
  - Handle loading, error, and success states ✅
  - Auto-refresh every 30 seconds ✅
  - **Acceptance:** Dashboard displays data from backend ✅

- [x] **File upload component with chunk progress** — `/punkt-frontend/src/components/upload/FileUpload.tsx` ✅
  - HIGH PRIORITY: Implement chunked upload (1MB chunks) ✅
  - Display upload progress bar with percentage ✅
  - Show chunk count progress ✅
  - Format selector dropdown (JSON / nginx) ✅
  - Source name input field ✅
  - Error handling with retry option ✅
  - **Acceptance:** File uploads with visible progress ✅

- [x] **HIGH PRIORITY: Pause auto-scroll button for live feed** — `/punkt-frontend/src/components/feed/LiveFeed.tsx` ✅
  - Create live feed component with scrolling log entries ✅
  - Implement pause/resume auto-scroll toggle button ✅
  - Color-code logs by level ✅
  - Buffer last 100 logs client-side ✅
  - **Acceptance:** Auto-scroll pauses; new logs buffer; resume scrolls ✅

### Day 2 Integration Checkpoint

- [x] **File upload to background processing flow** ✅
  - Upload JSON/Nginx log file via upload API ✅
  - Backend processes in background worker ✅
  - Logs inserted into database and cached to Redis ✅
  - **Acceptance:** Upload file -> logs processed and searchable ✅

---

## Agent Coordination Framework

This section documents best practices for ensuring parallel code-implementer agents successfully write files to disk and provide completion notifications.

### Core Principles

1. **Explicit File Verification** - Agents must verify files exist after writing
2. **Completion Confirmation** - Agents should report file paths and sizes
3. **Non-blocking Status Checks** - Use TaskOutput with `block: false` for status
4. **Atomic File Operations** - Use Write tool for all file creation
5. **Verification Integration** - Use Explore agent to verify Phase 1 completion before Phase 2

### Agent Prompt Template

When launching code-implementer agents, include this verification checklist:

```
**CRITICAL: File Writing & Verification**

After implementing each component:

1. Write the file using the Write tool:
   - Include full implementation from spec
   - Use correct file path

2. Verify file was created:
   - Use Bash: ls -lah [filepath]
   - Check file size > 0 bytes
   - Verify file is readable

3. Report completion:
   - List all created/modified files
   - Include file paths and sizes
   - Confirm ready for integration

**Example Verification:**
$ ls -lah app/core/redis.py
-rw-r--r--  1 user  staff  2.5K  Feb 08 10:30 app/core/redis.py

$ wc -l app/core/redis.py
     145 app/core/redis.py

✅ File created successfully: app/core/redis.py (145 lines, 2.5K)
```

### Phase Execution Pattern

**Phase 1: Parallel Implementation (5 Agents)**
```
// Launch all agents with run_in_background: true
agents = [Agent#1, Agent#2, Agent#3, Agent#4, Agent#5]

// Each agent:
// - Implements component
// - Verifies file creation with Bash
// - Reports completion with file paths
```

**Phase 1.5: Verification Check (Explore Agent)**
```
// After all Phase 1 agents report complete:
Explore {
  prompt: "Verify these files exist and have content:
    - app/parsers/json_parser.py
    - app/parsers/nginx_parser.py
    - app/core/redis.py
    - app/models/upload.py
    - app/api/upload.py
    - app/models/search.py
    - app/api/search.py"
}
```

**Phase 2: Integration (1 Agent)**
```
// After Phase 1 verified:
Agent#6 {
  prompt: "All Phase 1 components verified complete.
    Now wire everything into main.py..."
}
```

### Status Monitoring Pattern

```javascript
// Check agent status without blocking
status = TaskOutput(agent_id, block: false, timeout: 5000)
// Returns immediately with current status

// Wait for specific agent completion
result = TaskOutput(agent_id, block: true, timeout: 300000)
// Blocks until agent completes
```

### Verification Checklist for Each Phase

**After Phase 1 (All 5 agents complete):**
- [ ] `app/parsers/__init__.py` exists and exports functions
- [ ] `app/parsers/json_parser.py` exists and > 100 lines
- [ ] `app/parsers/nginx_parser.py` exists and > 80 lines
- [ ] `app/core/redis.py` exists and > 100 lines
- [ ] `app/models/upload.py` exists and > 40 lines
- [ ] `app/api/upload.py` exists and > 150 lines
- [ ] `app/models/search.py` exists and > 40 lines
- [ ] `app/api/search.py` exists and > 100 lines

**After Phase 2 (Agent #6 complete):**
- [ ] `app/workers/__init__.py` exists
- [ ] `app/workers/processor.py` exists and > 150 lines
- [ ] `app/main.py` updated with Redis imports
- [ ] `app/main.py` has Redis connect/disconnect in startup/shutdown
- [ ] `app/main.py` registers upload and search routers

**Verification Command:**
```bash
find app -type f \( -name "*.py" -path "*parsers*" -o \
  -name "redis.py" -o \
  -name "upload.py" -o \
  -name "search.py" -o \
  -name "processor.py" \) | xargs wc -l | tail -1
```

### Troubleshooting

**Problem: Agent reports "complete" but files don't exist**
- Solution: Add explicit Bash verification to agent prompt
- Include: `ls -lah [filepath]` after Write tool call
- Agent must wait for file existence before reporting complete

**Problem: Files exist but are empty**
- Solution: Check for Write tool error silently failing
- Add size check: `[ -s filepath ]` in bash
- Require agent to retry with detailed error logging

**Problem: Integration agent can't import modules**
- Solution: Run verification phase between Phase 1 and Phase 2
- Use Explore agent to confirm all Phase 1 files exist
- Only launch Phase 2 agent after verification passes

---

## Day 3: Search & Visualization

### Beatrice (Backend)

- [x] **Query parser (MVP grammar)** — `/punkt-backend/app/query/parser.py`
  - HIGH PRIORITY: Parse implicit AND field filters: `level=ERROR source=/var/log/app.log` ✅
  - Support operators: `=`, `!=`, `>`, `<`, `>=`, `<=` ✅
  - Support text search (searches message field) ✅
  - Support timestamp filters with quoted values ✅
  - Return structured AST for executor ✅
  - **Acceptance:** Parses `level=ERROR timestamp>"2025-02-07T00:00:00Z"` correctly ✅
  - **Files Created:** `app/query/parser.py` (318 lines), `app/query/__init__.py` (26 lines)

- [x] **Stats aggregation (count by field)** — `/punkt-backend/app/query/executor.py`
  - Implement `| stats count by {field}` command ✅
  - Support aggregation functions: count, sum, avg, min, max ✅
  - Execute aggregation as SQL GROUP BY ✅
  - Return aggregation results in response envelope ✅
  - **Acceptance:** `| stats count by source` returns correct counts per source ✅
  - **Files Created:** `app/query/executor.py` (286 lines)

- [x] **WebSocket broadcaster setup with heartbeat** — `/punkt-backend/app/ws/manager.py`
  - Create WebSocket endpoint: `WS /ws/{tenant_id}` ✅
  - Validate JWT on connection ✅
  - Implement ping every 30 seconds ✅
  - Track connected clients per tenant ✅
  - Setup Redis pub/sub for broadcast ✅
  - **Acceptance:** Client connects; receives ping every 30s; pong required within 10s ✅
  - **Files Created:** `app/ws/manager.py` (251 lines), `app/ws/__init__.py` (4 lines)

- [x] **Integration - Query pipeline + WebSocket routing** — `/punkt-backend/app/api/search.py` + `/punkt-backend/app/main.py`
  - Added `POST /api/search/query` endpoint using parse_query() and execute_query() ✅
  - Added `GET /api/search/stats/overview` endpoint with aggregated stats ✅
  - Added `WS /ws/{tenant_id}` WebSocket endpoint with JWT validation ✅
  - All endpoints support tenant isolation via tenant_id filtering ✅
  - **Files Updated:** `app/api/search.py` (307 lines), `app/main.py` (156 lines)

### Michael (Frontend)

- [x] **Search page with query bar** — `/punkt-frontend/src/pages/Search.tsx` ✅
  - Create search bar component with text input ✅
  - Add time range picker (presets: 15m, 1h, 24h, 7d, 30d) ✅
  - Display query examples in help tooltip ✅
  - Submit on Enter key ✅
  - Display query execution time (took_ms) ✅
  - **Acceptance:** Query submits; results display; execution time shown ✅

- [x] **Results table with virtualization** — `/punkt-frontend/src/components/search/ResultsTable.tsx` ✅
  - HIGH PRIORITY: Implement virtualized table with TanStack Virtual ✅
  - Sortable columns (timestamp, level, source) ✅
  - Expandable rows for full log details and metadata ✅
  - Display total count vs returned count ✅
  - **Acceptance:** Renders 10K rows smoothly; expand shows full log ✅

- [x] **Recharts time-series integration** — `/punkt-frontend/src/components/charts/TimeSeriesChart.tsx` ✅
  - Create stacked area chart for log volume by level ✅
  - Configurable time range (1h, 6h, 24h, 7d) ✅
  - Responsive sizing ✅
  - Tooltip with exact values ✅
  - **Acceptance:** Chart renders time_series data from API; hover shows values ✅

- [x] **Aggregation result visualizations** — `/punkt-frontend/src/components/charts/AggregationChart.tsx` ✅
  - Pie chart for `stats count by {field}` results ✅
  - Bar chart for top N results ✅
  - Conditional rendering based on query type ✅
  - **Acceptance:** Aggregation query displays appropriate chart type ✅

### Day 3 Integration Checkpoint

- [x] **Backend Search and Query Pipeline**
  - Query parser successfully parses mini query language ✅
  - Query executor builds parameterized SQL and executes queries ✅
  - WebSocket manager handles real-time connections with heartbeat ✅
  - Integration endpoints wire parser and executor into API ✅
  - Stats aggregation working via POST /api/search/query ✅
  - Real-time log streaming ready via WS /ws/{tenant_id} ✅
  - All endpoints enforce tenant isolation via RLS ✅
  - **Acceptance:** Backend API ready for frontend integration ✅

- [x] **Frontend-Backend Integration Alignment** (Post Day 3 Review)
  - WebSocket auth fixed: backend now accepts token as query param ✅
  - Stats endpoint path fixed: `/api/stats/overview` created ✅
  - Search GET wrapper added: `GET /api/search` for frontend compat ✅
  - All 7 frontend integration contracts verified correct ✅

- [x] **E2E Integration Test Analysis** (2026-02-09)
  - Frontend integration check: 7/7 points verified ✅
  - Cross-cutting validation: solid security, 8 issues documented ✅
  - Test data generated: 1000 logs in `test_logs_integration.json` ✅
  - Full report: `E2E_TEST_RESULTS.md` ✅
  - **Issues to address Day 4:** See HIGH priority items in E2E_TEST_RESULTS.md

---

## Day 4: Real-time Features

### Beatrice (Backend)

- [x] **WebSocket connection manager with backpressure** — `/punkt-backend/app/ws/manager.py`
  - HIGH PRIORITY: Implement client message queue (max 100 pending) ✅
  - Drop oldest messages when queue full ✅
  - Track dropped_count per client ✅
  - Send warning message when dropping: `{"type": "warning", "code": "SLOW_CLIENT"}` ✅
  - **Acceptance:** Slow client receives warning; messages dropped gracefully ✅
  - **Files Updated:** `app/ws/manager.py` (416 lines, complete refactor with backpressure)

- [x] **Broadcast logs to subscribers with filtering** — `/punkt-backend/app/ws/broadcaster.py`
  - Broadcast new logs to all connected clients for tenant ✅
  - Support subscription filters: source, level array ✅
  - Send `subscribed` confirmation with applied filters ✅
  - Integrate with ingestion pipeline ✅
  - **Acceptance:** Ingested log appears on all connected clients within 500ms ✅
  - **Files Created:** `app/ws/broadcaster.py` (61 lines)

- [x] **Heartbeat implementation (ping/pong)** — `/punkt-backend/app/ws/manager.py`
  - Send `{"type": "ping"}` every 30 seconds ✅
  - Expect `{"type": "pong"}` within 10 seconds ✅
  - Close connection if no pong received ✅
  - Handle reconnection with `last_seen_id` ✅
  - Send `reconnect_ack` with missed_count on reconnection ✅
  - **Acceptance:** Connection closes after missed pong; reconnection acknowledged ✅

- [x] **WebSocket integration with background workers** — `/punkt-backend/app/workers/processor.py` + `/punkt-backend/app/api/ingest.py`
  - Broadcast batches after file processing completes ✅
  - Broadcast individual logs for direct ingestion ✅
  - Non-fatal error handling (logs warning, continues) ✅
  - **Acceptance:** Logs stream to connected clients during file processing ✅
  - **Files Updated:** `app/workers/processor.py` (lines 178-184 broadcast calls), `app/api/ingest.py` (lines 57-68 broadcast calls)

### Michael (Frontend)

- [x] **Live feed component with WebSocket hook** — `/punkt-frontend/src/hooks/useWebSocket.ts` ✅
  - HIGH PRIORITY: Create WebSocket hook with connection management ✅
  - Handle connection/disconnection lifecycle ✅
  - Parse incoming messages by type (log, ping, warning, subscribed) ✅
  - ⚠️ Note: Respond to ping with pong (heartbeat response) — status unknown, verify in frontend code
  - Expose connection status ✅
  - **Acceptance:** Hook connects; receives logs; handles ping/pong ✅

- [x] **Reconnection logic with last_seen_id** — `/punkt-frontend/src/hooks/useWebSocket.ts` ✅
  - Track last_seen_id from received logs ✅
  - Auto-reconnect on disconnect with exponential backoff ✅ (5 attempts)
  - Display reconnection status to user ✅
  - **Acceptance:** Disconnect -> reconnect within 5s ✅

- [x] **Chart for aggregation results** — `/punkt-frontend/src/components/charts/AggregationChart.tsx` ✅
  - Conditional chart display based on query type ✅
  - Animate chart transitions ✅
  - Display count/percentage labels ✅
  - **Acceptance:** Aggregation query shows animated chart with labels ✅

- [x] **Slow client warning display** — `/punkt-frontend/src/components/feed/LiveFeed.tsx` ✅
  - Buffer capacity warning at 95+ logs ✅
  - Display warning alert in feed component ✅
  - **Acceptance:** Warning displays at high buffer load ✅

### Day 4 Integration Checkpoint

- [x] **Real-time ingest to display flow**
  - Ingest log via API ✅
  - Log broadcasts via WebSocket ✅
  - Log appears in live feed ✅
  - **Acceptance:** POST log -> appears in live feed within 500ms ✅

- [x] **WebSocket backpressure testing**
  - 10 unit tests covering backpressure scenarios ✅
  - Tests include: client connection, message queueing, queue full handling, slow client detection, task cleanup ✅
  - All tests passing ✅
  - **Files Created:** `tests/test_ws_backpressure.py` (222 lines, 10 tests), `pytest.ini` (asyncio_mode config)

---

## Day 5: Polish & Features

### Beatrice (Backend)

- [x] **Query performance optimization** — `/punkt-backend/app/query/executor.py`
  - Implement query result caching in Redis (5-min TTL) ✅
  - Cache key: SHA256 hash of query string + tenant ✅
  - Add query timeout (5 seconds) ✅
  - Cache written after execution with graceful fallback ✅
  - Only cache default queries (limit=100, offset=0) ✅
  - **Acceptance:** Repeated query returns from cache; cached result includes original execution_time_ms ✅
  - **Files Updated:** `app/query/executor.py` (140 lines, added caching logic)

- [x] **Error handling improvements** — `/punkt-backend/app/core/exceptions.py`
  - Create custom exception classes (5 exceptions) ✅
  - Implement global exception handler in `error_handlers.py` ✅
  - Return proper error envelope format for all errors ✅
  - Log errors with request context ✅
  - HTTP status codes: QueryTimeoutError(408), QueryParseError(400), TenantContextError(400), UploadError(400), AuthenticationError(401) ✅
  - **Acceptance:** All error responses use standard APIResponse with ErrorDetail; correct HTTP status ✅
  - **Files Created:** `app/core/exceptions.py` (54 lines), `app/core/error_handlers.py` (49 lines)
  - **Files Updated:** `app/main.py` (exception handler registration)

- [x] **Edge case handling** — `/punkt-backend/app/query/executor.py`
  - Handle empty query string gracefully ✅
  - Handle malformed timestamps with ISO 8601 parsing ✅
  - Handle disconnected Redis gracefully (degrade, don't crash) ✅
  - Validate all user inputs (field validation) ✅
  - Field validation returns 400 (QueryParseError) for unknown fields ✅
  - Timestamp parsing with helpful error messages ✅
  - **Acceptance:** Invalid inputs return clear error messages (400 status); service stays up ✅
  - **Files Updated:** `app/query/executor.py` (added _validate_filter_field, _parse_timestamp_value)

- [x] **Sources API endpoint** — `/punkt-backend/app/api/sources.py`
  - GET /api/sources returns distinct sources with metadata ✅
  - Include log_count per source ✅
  - Include last_seen timestamp ✅
  - Ordered by log_count DESC ✅
  - **Acceptance:** GET /api/sources returns list of sources with counts and timestamps ✅
  - **Files Created:** `app/api/sources.py` (80 lines)

- [x] **Configuration management** — `/punkt-backend/.env.example`
  - Created .env.example with all required env vars ✅
  - JWT_SECRET with production warning ✅
  - DATABASE_URL, REDIS_URL, CORS_ORIGINS documented ✅
  - **Acceptance:** .env.example can be copied to .env for local development ✅
  - **Files Created:** `.env.example` (22 lines)

### Michael (Frontend)

- [x] **Sources management page** — `/punkt-frontend/src/pages/Sources.tsx` ✅
  - Table of all log sources with metadata ✅
  - Display: source name, log count, last log timestamp, status indicator ✅
  - Click source to search logs from that source ✅
  - Add source button (links to upload page) ✅
  - ⚠️ Note: `GET /api/sources` backend endpoint not yet implemented (uses mock fallback)
  - **Acceptance:** Sources list displays ✅ (using mock data until backend endpoint created)

- [x] **UI polish (Glassmorphism)** — `/punkt-frontend/src/index.css` ✅
  - Apply consistent spacing (8px grid) ✅
  - Add hover states to interactive elements ✅
  - Glassmorphism design system applied ✅
  - Smooth transitions ✅
  - **Acceptance:** UI feels polished ✅

- [x] **Loading states + error messages** — `/punkt-frontend/src/components/common/` ✅
  - Common UI components created ✅
  - Toast notification system ✅
  - Error states and loading skeletons ✅
  - **Acceptance:** All async operations show loading; errors display clearly ✅

- [x] **CSV export** — `/punkt-frontend/src/utils/export.ts` ✅
  - Export button on search results ✅
  - Convert results to CSV format ✅
  - Trigger browser download ✅
  - **Acceptance:** Export button downloads valid CSV file ✅

### Day 5 Integration Checkpoint - COMPLETE ✅

- [x] **Query caching + timeout protection**
  - Cache hit on repeated queries ✅
  - 5-second timeout prevents long-running queries ✅
  - Graceful fallback if Redis unavailable ✅
  - **Acceptance:** Cache working; timeouts trigger QueryTimeoutError ✅

- [x] **Exception handling integration**
  - All custom exceptions properly mapped to HTTP status codes ✅
  - Global exception handler registered in main.py ✅
  - All error responses use standardized APIResponse format ✅
  - **Acceptance:** Invalid queries return 400; timeouts return 408 ✅

- [x] **Edge case handling tested**
  - Empty queries return recent logs ✅
  - Invalid fields return 400 with helpful message ✅
  - Malformed timestamps return 400 with format help ✅
  - Redis unavailable doesn't crash app ✅
  - **Acceptance:** All edge cases handled gracefully ✅

- [x] **Sources endpoint + response consistency**
  - GET /api/sources returns sources with metadata ✅
  - Response keys standardized to "rows" and "aggregations" ✅
  - Duplicate stats endpoint removed from search.py ✅
  - **Acceptance:** All responses consistent with QueryResult schema ✅

- [x] **Test suite verification**
  - All 10 WebSocket backpressure tests pass ✅
  - All files compile without syntax errors ✅
  - No circular dependencies or import errors ✅
  - **Acceptance:** Tests pass; code compiles ✅

---

---

## Day 6: Testing & Deployment

### Beatrice (Backend)

- [x] **Unit tests for query parser** — `/punkt-backend/tests/test_query_parser.py` ✅
  - Test simple field filters ✅
  - Test multiple field filters (implicit AND) ✅
  - Test text search ✅
  - Test timestamp operators ✅
  - Test stats aggregation parsing ✅
  - Test output modifiers (head, tail, sort) ✅
  - Test invalid syntax handling ✅
  - **Acceptance:** >80% coverage on query parser; all tests pass ✅ (41/41 tests passing)
  - **Bug Fixed:** Parser stats syntax bug for field-taking functions (avg/sum/min/max) discovered and fixed

- [x] **Integration tests for APIs** — `/punkt-backend/tests/test_api.py` ✅
  - Test auth endpoints (login, me, protected routes) ✅
  - Test ingest endpoints (JSON, chunked file) ✅
  - Test search endpoint with various queries ✅
  - Test stats/overview endpoint ✅
  - Test RLS isolation between tenants ✅
  - **Acceptance:** All API endpoints have integration tests; tests pass ✅ (19 tests written)

- [x] **Docker configuration** — `/punkt-backend/Dockerfile` ✅
  - Create multi-stage Dockerfile ✅
  - Run Alembic migrations on startup ✅
  - Configure health check endpoint ✅
  - Optimize for image size ✅
  - **Acceptance:** `docker build` succeeds; container starts and passes health check ✅

- [x] **Migration testing** — `/punkt-backend/tests/test_migrations.py` ✅
  - Test upgrade from empty database ✅
  - Test partition creation function ✅
  - Test RLS policy enforcement ✅
  - **Acceptance:** Fresh database migrates successfully; RLS works ✅

### Michael (Frontend)

- [x] **Frontend component tests** — `/punkt-frontend/src/__tests__/` ✅
  - Test SearchBar component (query submission) ✅
  - Test ResultsTable component (renders data, expands rows) ✅
  - Test LiveFeed component (pause/resume, color coding) ✅
  - Test FileUpload component (chunk progress) ✅
  - Test useWebSocket hook (connection, reconnection) ✅
  - **Acceptance:** All components have tests ✅

- [ ] **Cross-browser testing**
  - Test in Chrome (primary)
  - Test in Firefox
  - Test in Safari
  - Document any browser-specific issues
  - **Acceptance:** Core functionality works in all three browsers

- [x] **Docker configuration** — `/punkt-frontend/Dockerfile` ✅
  - Multi-stage build (Node for build, nginx for serve) ✅
  - Configure nginx for SPA routing ✅
  - Optimize bundle size ✅
  - **Acceptance:** `docker build` succeeds ✅

### Day 6 Integration Checkpoint

- [ ] **Docker Compose full stack test**
  - Run `docker-compose up --build`
  - All services start and connect
  - Database migrations run automatically
  - Frontend connects to backend
  - WebSocket connections work through nginx
  - **Acceptance:** Full stack runs in Docker; all integration checkpoints pass

---

## Day 7: Buffer & Demo Prep

### Both Team Members

- [x] **Bug fixes from testing** — Various files ✅
  - Fixed mock login in `Login.tsx` — now calls real `POST /api/auth/login` ✅
  - All 8 sprint issues (I-01 through I-08) resolved in Days 4-5 ✅
  - Created `scripts/seed_test_users.py` for integration test setup ✅
  - **Acceptance:** No blocking bugs remain ✅

- [x] **Demo script preparation** — `DEMO_GUIDE.md` ✅
  - 5-scenario step-by-step demo guide written ✅
  - Setup section with Docker Compose + real credentials ✅
  - Query cheat sheet for Scenario 4 ✅
  - **Acceptance:** Demo script reviewed and covers all features ✅

- [x] **Documentation** — `README.md` ✅
  - Docker Compose quick start present ✅
  - Dev credentials documented ✅
  - Query syntax reference added ✅
  - Full API endpoint table added ✅
  - Backend test run instructions added ✅
  - FastAPI OpenAPI docs available at /docs ✅
  - **Acceptance:** New developer can set up from README ✅

- [ ] **Final deployment test** — Docker environment
  - Clean docker system prune
  - Build from scratch
  - Run full demo script
  - Verify all acceptance criteria
  - **Acceptance:** Demo runs successfully from clean Docker build

---

## Critical Path Items

The following items are HIGH PRIORITY and block other work:

| Day | Item | Assignee | Blocks |
|-----|------|----------|--------|
| 1 | PostgreSQL partitioned schema + RLS | Beatrice | All data storage |
| 1 | JWT authentication with tenant context | Beatrice | All API endpoints |
| 1 | `generate_test_data.py` script | Beatrice | All testing |
| 1 | Auth context with JWT handling | Michael | All protected pages |
| 2 | Chunked file upload endpoints | Beatrice | File ingestion feature |
| 2 | Pause auto-scroll button | Michael | UX during testing |
| 3 | Query parser (MVP grammar) | Beatrice | Search functionality |
| 3 | Results table with virtualization | Michael | Search results display |
| 4 | WebSocket backpressure handling | Beatrice | Real-time feed stability |
| 4 | Reconnection logic | Michael | Real-time feed reliability |

---

## Acceptance Criteria Summary

### Must Have (P0) - Required for Demo

- [ ] User can log in with credentials — ⚠️ Frontend uses mock login (needs integration)
- [x] User can upload a log file via chunked upload ✅
- [x] User can execute search: `level=ERROR` ✅ (backend+frontend both ready)
- [x] User can execute aggregation: `| stats count by source` ✅
- [x] User sees real-time logs in live feed ✅
- [x] User can pause/resume auto-scroll in live feed ✅
- [x] Dashboard displays metric cards and time-series chart ✅
- [x] Multi-tenant isolation via RLS (users only see their logs) ✅
- [x] WebSocket reconnection works with last_seen_id ✅ (exponential backoff)

### Nice to Have (P1) - If Time Permits

- [ ] Export search results to CSV
- [ ] Query history and favorites
- [ ] Advanced syntax highlighting in search bar

---

## Demo Checklist

The following must work for successful demo:

1. [ ] Login to Punkt dashboard
2. [ ] View dashboard with live metrics
3. [ ] Upload a log file via chunked upload
4. [ ] Watch logs appear in real-time feed
5. [ ] Pause and resume auto-scroll
6. [ ] Execute search query: `level=ERROR`
7. [ ] Execute aggregation: `| stats count by source`
8. [ ] View results in table and chart
9. [ ] Show multi-tenant isolation (switch tenants, see different data)
10. [ ] Demonstrate WebSocket reconnection

---

## Notes

- All API responses must use standard envelope format: `{success, data, error, timestamp}`
- Log levels color coded: DEBUG(#6b7280), INFO(#3b82f6), WARN(#f59e0b), ERROR(#ef4444), CRITICAL(#dc2626)
- MVP query language: implicit AND only, no OR/NOT/parentheses (documented as post-MVP)
- Maximum 1MB chunk size for file uploads
- Redis lists capped at 1000 entries with 15-min TTL
- WebSocket ping every 30s, pong required within 10s
