# Product Requirements Document: Punkt

## Executive Summary

**Product Name:** Punkt  
**Version:** 2.0 (MVP - Amended)  
**Timeline:** 1 Week Sprint  
**Team:** 2 Developers (Beatrice - Backend, Michael - Frontend)  
**Tagline:** Enterprise Log Aggregation & Analysis Platform

Punkt is a B2B software solution that replicates the core functionality of Splunk: data ingestion, aggregation, and enrichment for enterprise log management. The platform enables organizations to collect logs from multiple sources, search through them efficiently, and visualize patterns in real-time.

---

## Document Change Log

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | Feb 7, 2025 | Initial PRD for MVP sprint |
| v2.0 | Feb 7, 2025 | Amended based on architecture review: simplified query language, added PostgreSQL partitioning + RLS, enhanced WebSocket spec, standardized API envelope, added chunked uploads, limited log formats to JSON + nginx, fixed Redis cache strategy, added Alembic migrations, added test data generation requirement |

---

## 1. Product Overview

### 1.1 Problem Statement
Organizations generate massive volumes of log data from applications, servers, and infrastructure. Without centralized aggregation and analysis tools, teams struggle to:
- Debug production issues quickly
- Identify security threats
- Monitor system health
- Analyze usage patterns

### 1.2 Solution
Punkt provides a centralized platform for:
- **Ingesting** logs from multiple sources (files, APIs)
- **Storing** logs in a time-series optimized database with partitioning
- **Searching** logs using a simplified query language
- **Visualizing** log patterns through real-time dashboards
- **Streaming** live log updates via WebSocket connections

### 1.3 Target Users
- DevOps Engineers
- Site Reliability Engineers (SREs)
- Security Operations Teams
- Application Developers
- IT Operations Managers

### 1.4 Success Criteria
- Ingest and display logs from at least 2 different sources
- Execute search queries in <2 seconds for datasets up to 100K logs
- Real-time log streaming with <500ms latency
- Multi-tenant support with proper isolation via Row-Level Security
- Professional UI that demonstrates enterprise readiness

---

## 2. Core Features

### 2.1 Data Ingestion (Priority: P0)

#### 2.1.1 File Upload (Chunked)
**Description:** Users can upload log files through the web interface using chunked uploads for large files.

**Requirements:**
- Accept supported log formats: `.log`, `.txt` (nginx format), JSON
- Support file sizes up to 100MB via chunked upload
- Parse logs asynchronously (background processing)
- Display upload progress indicator with chunk progress
- Return ingestion confirmation with log count
- Stream file processing to avoid memory exhaustion

> [!IMPORTANT]
> **MVP Scope:** Only JSON and nginx access log formats are supported. Format must be specified by user on upload.

**API Specification - Chunked Upload:**
```
# Step 1: Initialize upload
POST /api/ingest/file/init
Content-Type: application/json
Authorization: Bearer <token>

Request:
{
  "filename": "app.log",
  "total_size": 52428800,
  "total_chunks": 50,
  "source": "nginx",
  "format": "nginx"  // "json" or "nginx"
}

Response:
{
  "success": true,
  "data": {
    "upload_id": "upload_abc123",
    "chunk_size": 1048576
  },
  "error": null,
  "timestamp": "2025-02-07T14:23:01Z"
}

# Step 2: Upload chunks
POST /api/ingest/file/chunk
Content-Type: multipart/form-data
Authorization: Bearer <token>

Request:
- upload_id: string (required)
- chunk_index: integer (required, 0-based)
- chunk: File (required)

Response:
{
  "success": true,
  "data": {
    "chunk_index": 0,
    "received": true,
    "chunks_remaining": 49
  },
  "error": null,
  "timestamp": "2025-02-07T14:23:02Z"
}

# Step 3: Finalize upload
POST /api/ingest/file/complete
Content-Type: application/json
Authorization: Bearer <token>

Request:
{
  "upload_id": "upload_abc123"
}

Response:
{
  "success": true,
  "data": {
    "status": "processing",
    "filename": "app.log",
    "estimated_count": 5432,
    "job_id": "job_xyz789"
  },
  "error": null,
  "timestamp": "2025-02-07T14:23:03Z"
}
```

**Memory Constraints:**
- Maximum chunk size: 1MB
- Server processes chunks sequentially, writing to temp storage
- Full file never held in memory
- Async worker parses file after all chunks received

#### 2.1.2 JSON API Ingestion
**Description:** External systems can POST logs directly via REST API.

**Requirements:**
- Accept batch log submissions (up to 1000 logs per request)
- Validate log structure before acceptance
- Support authentication via API keys or JWT
- Return ingestion errors with specific validation messages

**API Specification:**
```
POST /api/ingest/json
Content-Type: application/json
Authorization: Bearer <token>

Request:
{
  "logs": [
    {
      "timestamp": "2025-02-07T14:23:01Z",
      "level": "ERROR",
      "source": "/var/log/app.log",
      "message": "Connection timeout",
      "metadata": { "host": "web-01" }
    }
  ]
}

Response:
{
  "success": true,
  "data": {
    "accepted": 1,
    "rejected": 0,
    "errors": []
  },
  "error": null,
  "timestamp": "2025-02-07T14:23:01Z"
}
```

### 2.2 Log Parsing (Priority: P0)

> [!IMPORTANT]
> **MVP Scope:** Only two log formats are supported. Users must specify format on upload.

#### 2.2.1 Supported Formats

**JSON Logs:**
```json
{
  "timestamp": "2025-02-07T14:23:01Z",
  "level": "ERROR",
  "logger": "app.database",
  "message": "Connection pool exhausted",
  "metadata": {
    "pool_size": 20,
    "request_id": "abc-123"
  }
}
```

**Nginx Access Logs:**
```
192.168.1.1 - - [07/Feb/2025:14:23:01 +0000] "GET /api/users HTTP/1.1" 200 1234 "-" "Mozilla/5.0"
```

Parsed using regex:
```python
NGINX_PATTERN = r'^(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+) \S+" (?P<status>\d+) (?P<size>\d+)'
```

---

### 2.3 Data Storage (Priority: P0)

#### 2.3.1 PostgreSQL Schema with Partitioning
**Requirements:**
- Time-series optimized table structure with native partitioning
- Partitioning by month for query performance
- JSONB field for flexible metadata storage
- Indexes on: timestamp, source, level
- Row-Level Security for multi-tenant isolation
- Support for up to 1M log entries in MVP

**Schema Design:**
```sql
-- Enable Row-Level Security support
ALTER DATABASE punkt SET row_security = on;

-- Create partitioned log entries table
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

-- Create monthly partitions (generate for each month needed)
CREATE TABLE log_entries_2025_02 PARTITION OF log_entries
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

CREATE TABLE log_entries_2025_03 PARTITION OF log_entries
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');

-- Create default partition for data outside defined ranges
CREATE TABLE log_entries_default PARTITION OF log_entries DEFAULT;

-- Indexes (created on parent, automatically applied to partitions)
CREATE INDEX idx_log_entries_timestamp ON log_entries (timestamp DESC);
CREATE INDEX idx_log_entries_tenant_time ON log_entries (tenant_id, timestamp DESC);
CREATE INDEX idx_log_entries_level ON log_entries (level);
CREATE INDEX idx_log_entries_source ON log_entries (source);
CREATE INDEX idx_log_entries_metadata ON log_entries USING GIN (metadata);

-- Row-Level Security
ALTER TABLE log_entries ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see logs from their tenant
CREATE POLICY tenant_isolation_policy ON log_entries
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant', true));

-- Create application role
CREATE ROLE punkt_app LOGIN PASSWORD 'punkt_app_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON log_entries TO punkt_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO punkt_app;
```

**Partition Management Function:**
```sql
-- Function to auto-create partitions
CREATE OR REPLACE FUNCTION create_monthly_partition(target_date DATE)
RETURNS void AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    start_date := date_trunc('month', target_date);
    end_date := start_date + INTERVAL '1 month';
    partition_name := 'log_entries_' || to_char(start_date, 'YYYY_MM');
    
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF log_entries
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;

-- Create partitions for next 3 months on startup
SELECT create_monthly_partition(CURRENT_DATE);
SELECT create_monthly_partition(CURRENT_DATE + INTERVAL '1 month');
SELECT create_monthly_partition(CURRENT_DATE + INTERVAL '2 months');
```

#### 2.3.2 Multi-tenant Implementation with RLS

**Setting Tenant Context:**
```python
# FastAPI middleware to set tenant context
async def set_tenant_context(request: Request, call_next):
    tenant_id = get_tenant_from_jwt(request)
    
    async with db.connection() as conn:
        # Set tenant context for RLS
        await conn.execute(
            "SET app.current_tenant = $1", tenant_id
        )
        request.state.db = conn
        response = await call_next(request)
    
    return response
```

> [!NOTE]
> With RLS enabled, all queries automatically filter by tenant_id. No manual WHERE clauses needed.

#### 2.3.3 Redis Cache Layer
**Requirements:**
- Cache recent logs (last 15 minutes) for fast retrieval
- Store active WebSocket subscriptions
- TTL-based expiration for hot data
- Size-limited lists to prevent memory exhaustion

**Data Structures:**
```python
# Recent logs cache with size limit
RECENT_LOG_LIMIT = 1000
RECENT_LOG_TTL = 900  # 15 minutes

async def cache_recent_log(tenant_id: str, log_json: str):
    key = f"logs:recent:{tenant_id}"
    pipe = redis.pipeline()
    pipe.lpush(key, log_json)
    pipe.ltrim(key, 0, RECENT_LOG_LIMIT - 1)  # Cap at 1000 logs
    pipe.expire(key, RECENT_LOG_TTL)
    await pipe.execute()

async def get_recent_logs(tenant_id: str, limit: int = 100) -> list:
    key = f"logs:recent:{tenant_id}"
    return await redis.lrange(key, 0, min(limit - 1, RECENT_LOG_LIMIT - 1))
```

```
Key: logs:recent:{tenant_id}
Type: List (LPUSH/LTRIM/LRANGE)
Max Size: 1000 entries
TTL: 900 seconds (15 min)

Key: ws:connections:{tenant_id}
Type: Set
TTL: None (managed by connection lifecycle)

Key: query:cache:{hash(query)}
Type: String (JSON)
TTL: 300 seconds (5 min)
```

---

### 2.4 Search & Query Engine (Priority: P0)

#### 2.4.1 Query Language (MVP Scope)

> [!IMPORTANT]
> **MVP Simplification:** The query language has been reduced from the original specification to ensure delivery within the 1-week timeline. Advanced features (OR logic, parentheses, timechart) are documented as post-MVP enhancements.

**MVP Supported Syntax:**
```
# Basic text search (searches message field)
error
connection timeout

# Field filters (implicit AND)
level=ERROR
level=ERROR source=/var/log/app.log
status=500 method=GET

# Timestamp filters
timestamp>"2025-02-07T00:00:00Z"
timestamp<"2025-02-07T23:59:59Z"

# Single aggregation command
| stats count by source
| stats count by level
| stats avg(status) by source

# Output modifiers
| head 100
| tail 50
| sort timestamp desc
```

**MVP Grammar:**
```
query := search_terms [ "|" command ]?

search_terms := search_term [ search_term ]*  // Implicit AND

search_term := 
    | text_search           // "error"
    | field_filter          // level=ERROR

field_filter := field_name operator value
field_name := "level" | "source" | "timestamp" | "status" | "method" | metadata_field
operator := "=" | "!=" | ">" | "<" | ">=" | "<="
value := quoted_string | unquoted_string | number

command :=
    | "stats" aggregation_func "by" field_name
    | "head" number
    | "tail" number
    | "sort" field_name ["asc" | "desc"]

aggregation_func := "count" | "sum" | "avg" | "min" | "max"
```

**Post-MVP Features (Documented for Future):**
```
# OR logic and parentheses
error OR warning
(status=500 OR status=503) AND source=/var/log/app.log

# Timechart aggregation
| timechart count span=1h
| timechart avg(response_time) span=15m

# Chained commands
| stats count by source | sort count desc | head 10

# NOT operator
NOT level=DEBUG
```

**API Specification:**
```
GET /api/search
Query Parameters:
- query: string (required, e.g., "level=ERROR | stats count by source")
- start: ISO timestamp (optional, default: 24h ago)
- end: ISO timestamp (optional, default: now)
- limit: integer (optional, default: 1000, max: 10000)

Response:
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 12345,
        "timestamp": "2025-02-07T14:23:01Z",
        "level": "ERROR",
        "source": "/var/log/app.log",
        "message": "Connection timeout",
        "metadata": { "host": "web-01" }
      }
    ],
    "total_count": 1523,
    "returned_count": 100,
    "took_ms": 145,
    "aggregations": {
      "bySource": {
        "/var/log/app.log": 800,
        "/var/log/nginx.log": 723
      }
    }
  },
  "error": null,
  "timestamp": "2025-02-07T14:23:01Z"
}
```

#### 2.4.2 Query Performance
**Requirements:**
- Queries on 100K logs must complete in <2 seconds
- Utilize PostgreSQL indexes and partitioning efficiently
- Cache frequent queries in Redis (5-minute TTL)
- Return partial results if query exceeds timeout (5s)

---

### 2.5 Real-time Log Streaming (Priority: P0)

#### 2.5.1 WebSocket Connection
**Description:** Live feed of logs as they're ingested.

**Requirements:**
- WebSocket endpoint per tenant
- Heartbeat mechanism for connection health
- Auto-reconnection on disconnect with last-seen tracking
- Broadcast new logs to all connected clients
- Filter streaming by source or level (optional)
- Drop messages to slow clients (backpressure handling)
- Buffer management (keep last 100 logs client-side)

**WebSocket Specification:**
```
Connection: ws://api.punkt.io/ws/{tenant_id}
Authorization: Bearer <token>

# Server → Client: New log entry
{
  "type": "log",
  "data": {
    "id": 12345,
    "timestamp": "2025-02-07T14:23:01Z",
    "level": "ERROR",
    "source": "/var/log/app.log",
    "message": "Connection timeout"
  }
}

# Server → Client: Heartbeat ping (every 30 seconds)
{
  "type": "ping",
  "timestamp": "2025-02-07T14:23:01Z"
}

# Client → Server: Heartbeat response
{
  "type": "pong"
}

# Server → Client: Reconnection acknowledgment
{
  "type": "reconnect_ack",
  "last_seen_id": 12344,
  "missed_count": 5
}

# Client → Server: Subscribe with filters
{
  "type": "subscribe",
  "filters": {
    "source": "/var/log/app.log",
    "level": ["ERROR", "CRITICAL"]
  },
  "last_seen_id": 12300  // For reconnection
}

# Server → Client: Subscription confirmed
{
  "type": "subscribed",
  "filters_applied": {
    "source": "/var/log/app.log",
    "level": ["ERROR", "CRITICAL"]
  }
}

# Server → Client: Backpressure warning
{
  "type": "warning",
  "code": "SLOW_CLIENT",
  "message": "Messages dropped due to slow consumption",
  "dropped_count": 15
}
```

**Backpressure Handling:**
```python
class WebSocketClient:
    MAX_PENDING_MESSAGES = 100
    
    async def send_log(self, log: dict):
        if len(self.pending_queue) >= self.MAX_PENDING_MESSAGES:
            # Drop oldest messages, track count
            dropped = len(self.pending_queue) - 50
            self.pending_queue = self.pending_queue[-50:]
            self.dropped_count += dropped
            
            # Warn client periodically
            if self.dropped_count % 10 == 0:
                await self.send_warning(dropped)
        
        self.pending_queue.append(log)
```

**Connection Lifecycle:**
```
1. Client connects with JWT token
2. Server validates token, extracts tenant_id
3. Server sends reconnect_ack with last_seen_id (if reconnection)
4. Client optionally sends subscribe with filters
5. Server confirms subscription
6. Server sends ping every 30 seconds
7. Client must respond with pong within 10 seconds
8. If no pong received, server closes connection
9. On disconnect, client should reconnect with last_seen_id
```

---

### 2.6 Visualization Dashboard (Priority: P0)

#### 2.6.1 Dashboard Overview Page
**Description:** High-level metrics and charts on landing page.

**Components:**
1. **Metric Cards** (Top Row)
   - Total logs today
   - Error rate (% of ERROR/CRITICAL logs)
   - Active log sources
   - Average ingestion rate (logs/min)

2. **Time Series Chart** (Main Section)
   - Log volume over last 24 hours
   - Grouped by log level (stacked area chart)
   - Configurable time range (1h, 6h, 24h, 7d)

3. **Live Feed** (Right Sidebar)
   - Real-time scrolling log entries
   - Color-coded by level
   - **Pause auto-scroll button (implement early)**
   - Click to view full log details

> [!IMPORTANT]
> **Early Implementation Priority:** The pause auto-scroll feature must be implemented in Day 2-3 to prevent UX issues during high-volume testing.

**Data Requirements:**
```
GET /api/stats/overview

Response:
{
  "success": true,
  "data": {
    "logs_today": 45320,
    "error_rate": 2.3,
    "active_sources": 8,
    "ingestion_rate": 125.4,
    "time_series": [
      { 
        "timestamp": "2025-02-07T00:00:00Z", 
        "info": 1200, 
        "error": 45, 
        "warn": 230,
        "debug": 500,
        "critical": 5
      }
    ]
  },
  "error": null,
  "timestamp": "2025-02-07T14:23:01Z"
}
```

#### 2.6.2 Search & Explore Page
**Description:** Query interface with results visualization.

**Components:**
1. **Search Bar**
   - Syntax highlighting for query language
   - Auto-complete for field names
   - Query history dropdown
   - Example queries (help tooltip)

2. **Time Range Picker**
   - Preset ranges: Last 15m, 1h, 24h, 7d, 30d
   - Custom date/time range selector

3. **Results Table**
   - Virtualized scrolling for performance
   - Sortable columns
   - Expandable rows for full log details
   - Export to CSV button

4. **Visualization Panel** (Conditional on query type)
   - Pie chart for "stats count by {field}"
   - Bar chart for top N results

#### 2.6.3 Sources Management Page
**Description:** View and manage log sources.

**Components:**
- Table of all sources with metadata:
  - Source name/path
  - Total log count
  - Last log received timestamp
  - Status indicator (active/inactive)
- Add new source button
- Source-specific search shortcut

---

### 2.7 Authentication & Multi-tenancy (Priority: P0)

#### 2.7.1 User Authentication
**Requirements:**
- JWT-based authentication
- Login with username/password
- Token expiration (24 hours)
- Token refresh mechanism
- Logout (client-side token deletion)

**API Specification:**
```
POST /api/auth/login
Request:
{
  "username": "admin@company.com",
  "password": "securepassword"
}

Response:
{
  "success": true,
  "data": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": "user123",
      "username": "admin@company.com",
      "tenant_id": "tenant_acme"
    }
  },
  "error": null,
  "timestamp": "2025-02-07T14:23:01Z"
}
```

#### 2.7.2 Multi-tenant Isolation
**Requirements:**
- Each user belongs to one tenant
- Logs are isolated by tenant_id via PostgreSQL RLS
- All queries automatically filtered by tenant (RLS policy)
- WebSocket connections scoped to tenant
- No cross-tenant data leakage

**Implementation (Row-Level Security):**
```python
# Middleware sets tenant context from JWT
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.url.path != "/api/auth/login":
        token = extract_token(request)
        tenant_id = decode_tenant_from_jwt(token)
        
        # Set PostgreSQL session variable for RLS
        await request.state.db.execute(
            f"SET app.current_tenant = '{tenant_id}'"
        )
    
    return await call_next(request)
```

---

## 3. User Interface Specifications

### 3.1 Design System

#### 3.1.1 Brand Identity
- **Name:** Punkt
- **Logo:** Mohawk punk character (spiky hair, edgy aesthetic)
- **Color Palette:**
  - Primary: Purple (#8b5cf6)
  - Secondary: Dark Gray (#1f2937)
  - Accent: Electric Blue (#3b82f6)
  - Success: Green (#10b981)
  - Warning: Yellow (#f59e0b)
  - Error: Red (#ef4444)
  - Info: Cyan (#06b6d4)

#### 3.1.2 Log Level Color Coding
```css
DEBUG:    #6b7280 (Gray)
INFO:     #3b82f6 (Blue)
WARN:     #f59e0b (Yellow)
ERROR:    #ef4444 (Red)
CRITICAL: #dc2626 (Dark Red)
```

#### 3.1.3 Typography
- **Headings:** Inter or Poppins (bold, modern)
- **Body:** System font stack for performance
- **Code/Logs:** Fira Code or JetBrains Mono (monospace)

#### 3.1.4 Component Library
- Use Tailwind CSS for utility-first styling
- Recharts for all data visualizations
- TanStack Virtual for virtualized log tables

### 3.2 Page Layouts

#### 3.2.1 Main Layout Structure
```
┌─────────────────────────────────────────────────┐
│ Header: Logo | Search | User Menu              │
├──────────┬──────────────────────────────────────┤
│          │                                      │
│ Sidebar  │         Main Content Area           │
│ Nav      │                                      │
│          │                                      │
└──────────┴──────────────────────────────────────┘
```

**Sidebar Navigation:**
- Dashboard (home icon)
- Search (magnifying glass icon)
- Sources (folder icon)
- Settings (gear icon)

#### 3.2.2 Responsive Behavior
- Desktop-first design (primary use case)
- Collapsible sidebar on tablets
- Minimum supported width: 768px

---

## 4. Technical Architecture

### 4.1 Technology Stack

#### 4.1.1 Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL 15 with native partitioning
- **Cache:** Redis 7
- **Migrations:** Alembic
- **Authentication:** JWT (python-jose)
- **Async:** asyncio, asyncpg
- **Testing:** pytest

#### 4.1.2 Frontend
- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite
- **State Management:** React Context + Hooks
- **Routing:** React Router v6
- **HTTP Client:** Axios
- **WebSocket:** Native WebSocket API with reconnection logic
- **Charts:** Recharts
- **Styling:** Tailwind CSS
- **Tables:** TanStack Virtual (virtualization)

#### 4.1.3 DevOps
- **Containerization:** Docker + Docker Compose
- **Version Control:** Git

### 4.2 System Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                     Client (Browser)                     │
│  React App + WebSocket Client (with reconnection)        │
└────────────┬────────────────────────────┬────────────────┘
             │ HTTP/REST                  │ WebSocket
             ▼                            ▼
┌────────────────────────────────────────────────────────┐
│                  FastAPI Backend                       │
│  ┌──────────────┐                                      │
│  │ Tenant       │ Sets app.current_tenant for RLS     │
│  │ Middleware   │                                      │
│  └──────┬───────┘                                      │
│         ▼                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │Ingestion │  │  Query   │  │   WebSocket      │    │
│  │   API    │  │  Engine  │  │   Manager        │    │
│  │(Chunked) │  │  (MVP)   │  │  (Backpressure)  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────────────┘    │
│       │             │              │                   │
│       ▼             ▼              ▼                   │
│  ┌──────────────────────────────────────────────┐     │
│  │           Storage Layer                      │     │
│  │  ┌────────────────┐    ┌────────────┐       │     │
│  │  │ PostgreSQL 15  │    │   Redis 7  │       │     │
│  │  │ (Partitioned)  │    │  (Capped)  │       │     │
│  │  │ (RLS Enabled)  │    │            │       │     │
│  │  └────────────────┘    └────────────┘       │     │
│  └──────────────────────────────────────────────┘     │
│                                                        │
│  ┌──────────────────────────────────────────────┐     │
│  │           Alembic Migrations                 │     │
│  └──────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────┘
```

### 4.3 Database Migrations with Alembic

**Setup:**
```bash
cd punkt-backend
pip install alembic
alembic init migrations
```

**alembic.ini configuration:**
```ini
[alembic]
script_location = migrations
sqlalchemy.url = postgresql://punkt:punkt123@localhost:5432/punkt
```

**Initial migration (migrations/versions/001_initial.py):**
```python
"""Initial schema with partitioning and RLS

Revision ID: 001
Create Date: 2025-02-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None

def upgrade():
    # Create partitioned table
    op.execute("""
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
    """)
    
    # Create initial partitions
    op.execute("""
        SELECT create_monthly_partition(CURRENT_DATE);
        SELECT create_monthly_partition(CURRENT_DATE + INTERVAL '1 month');
    """)
    
    # Enable RLS
    op.execute("ALTER TABLE log_entries ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON log_entries
        FOR ALL USING (tenant_id = current_setting('app.current_tenant', true));
    """)
    
    # Create indexes
    op.create_index('idx_log_entries_timestamp', 'log_entries', ['timestamp'])
    op.create_index('idx_log_entries_tenant_time', 'log_entries', ['tenant_id', 'timestamp'])

def downgrade():
    op.drop_table('log_entries')
```

**Running migrations:**
```bash
# Create new migration
alembic revision -m "description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 5. API Contract Specifications

### 5.1 Standard Response Envelope

> [!IMPORTANT]
> All API responses MUST use this envelope format. No exceptions.

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
    "details": { "field": "timestamp", "expected": "ISO 8601" }
  },
  "timestamp": "2025-02-07T14:23:01Z"
}
```

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `AUTHENTICATION_ERROR` | 401 | Missing or invalid token |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

### 5.2 Complete API Reference

#### Authentication
```
POST /api/auth/login      # Login, returns JWT
POST /api/auth/refresh    # Refresh token
GET  /api/auth/me         # Current user info
POST /api/auth/logout     # Logout (client-side)
```

#### Ingestion
```
POST /api/ingest/json           # Batch JSON logs
POST /api/ingest/file/init      # Initialize chunked upload
POST /api/ingest/file/chunk     # Upload chunk
POST /api/ingest/file/complete  # Finalize upload
GET  /api/ingest/status/{job_id} # Check processing status
```

#### Query & Search
```
GET  /api/search                 # Execute query
GET  /api/stats/overview         # Dashboard metrics
GET  /api/sources                # List all sources
GET  /api/sources/{source_id}    # Source details
```

#### WebSocket
```
WS   /ws/{tenant_id}    # Real-time log stream
```

### 5.3 Log Entry Schema (Canonical Format)

```typescript
interface LogEntry {
  id: number;
  timestamp: string;      // ISO 8601 format
  tenant_id: string;
  source: string;
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'CRITICAL';
  message: string;
  raw_log: string;        // Original unparsed log
  metadata: Record<string, any>;
  indexed_at: string;     // ISO 8601 format
}
```

---

## 6. Development Plan

### 6.1 Team Responsibilities

#### 6.1.1 Beatrice (Backend Developer)
**Deliverables:**
- FastAPI application setup with Alembic migrations
- PostgreSQL schema with partitioning and RLS
- Redis integration with capped lists
- Ingestion API (chunked file upload + JSON)
- Log parsers (JSON + nginx formats)
- Query parser and executor (MVP grammar)
- WebSocket manager with heartbeat and backpressure
- Authentication middleware with RLS tenant context
- Test data generation script

#### 6.1.2 Michael (Frontend Developer)
**Deliverables:**
- React application scaffold
- Layout components (header, sidebar, layout)
- Authentication UI and context
- Dashboard page with metric cards + charts
- Search page with query bar + results
- **Live feed with pause auto-scroll (early priority)**
- WebSocket hook with reconnection logic
- Source management page
- Responsive styling

### 6.2 Development Timeline

#### Day 1 (Foundation)
**Beatrice:**
- FastAPI project setup
- Alembic migrations initialized
- PostgreSQL connection + partitioned schema + RLS
- `/ingest/json` endpoint
- JWT authentication with tenant context
- **`scripts/generate_test_data.py`** ← Critical for testing

**Michael:**
- React + TypeScript + Tailwind setup
- Basic layout with header + sidebar
- Login page UI
- Auth context with JWT handling

**Integration:** Test login flow end-to-end

#### Day 2 (Core Features)
**Beatrice:**
- Chunked file upload endpoints
- JSON + nginx log parsers
- Redis integration with capped lists
- Basic query endpoint (field filters only)

**Michael:**
- Dashboard page with metric cards
- API integration for stats
- File upload component with chunk progress
- **Pause auto-scroll button for live feed**

**Integration:** Upload file → see stats update

#### Day 3 (Search & Visualization)
**Beatrice:**
- Query parser (MVP grammar: implicit AND, field filters)
- Stats aggregation (count by field)
- WebSocket broadcaster setup with heartbeat

**Michael:**
- Search page with query bar
- Results table with virtualization
- Recharts time-series integration
- Aggregation result visualizations

**Integration:** Execute search → display results

#### Day 4 (Real-time Features)
**Beatrice:**
- WebSocket connection manager with backpressure
- Broadcast logs to subscribers with filtering
- Heartbeat implementation (ping/pong)
- Query output modifiers (head, tail, sort)

**Michael:**
- Live feed component with WebSocket hook
- Reconnection logic with last_seen_id
- Chart for aggregation results
- Slow client warning display

**Integration:** Ingest log → appears in live feed

#### Day 5 (Polish & Features)
**Beatrice:**
- Query performance optimization
- Error handling improvements
- Edge case handling

**Michael:**
- Sources management page
- UI polish (colors, spacing, hover states)
- Loading states + error messages
- CSV export

**Integration:** Full user journey testing

#### Day 6 (Testing & Deployment)
**Beatrice:**
- Unit tests for query parser
- Integration tests for APIs
- Docker configuration
- Migration testing

**Michael:**
- Frontend component tests
- Cross-browser testing
- Docker configuration

**Integration:** Docker Compose full stack test

#### Day 7 (Buffer & Demo Prep)
**Both:**
- Bug fixes from testing
- Demo script preparation
- Documentation
- Final deployment test

### 6.3 Test Data Generation Script

**Required on Day 1:** `scripts/generate_test_data.py`

```python
#!/usr/bin/env python3
"""Generate test log data for Punkt development and testing."""

import json
import random
import argparse
from datetime import datetime, timedelta
from typing import Generator

SOURCES = [
    "/var/log/nginx/access.log",
    "/var/log/app/api.log",
    "/var/log/app/worker.log",
    "/var/log/auth.log",
]

LEVELS = ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]
LEVEL_WEIGHTS = [10, 60, 20, 8, 2]  # Realistic distribution

MESSAGES = {
    "DEBUG": ["Cache hit for key", "Query executed in {ms}ms", "Request payload: {size} bytes"],
    "INFO": ["User logged in", "Request completed", "Background job finished", "File uploaded"],
    "WARN": ["Slow query detected", "Rate limit approaching", "Disk usage at 80%"],
    "ERROR": ["Connection timeout", "Database error", "Invalid request format"],
    "CRITICAL": ["Out of memory", "Database connection lost", "Service unavailable"],
}

def generate_json_logs(count: int, tenant_id: str) -> Generator[dict, None, None]:
    """Generate JSON format logs."""
    base_time = datetime.utcnow() - timedelta(hours=24)
    
    for i in range(count):
        level = random.choices(LEVELS, weights=LEVEL_WEIGHTS)[0]
        source = random.choice(SOURCES)
        timestamp = base_time + timedelta(seconds=i * (86400 / count))
        
        yield {
            "timestamp": timestamp.isoformat() + "Z",
            "level": level,
            "source": source,
            "message": random.choice(MESSAGES[level]).format(
                ms=random.randint(10, 5000),
                size=random.randint(100, 10000)
            ),
            "metadata": {
                "host": f"server-{random.randint(1, 5):02d}",
                "request_id": f"req-{random.randint(10000, 99999)}",
                "user_id": f"user-{random.randint(1, 100)}" if random.random() > 0.3 else None
            }
        }

def generate_nginx_logs(count: int) -> Generator[str, None, None]:
    """Generate nginx access log format."""
    base_time = datetime.utcnow() - timedelta(hours=24)
    methods = ["GET", "POST", "PUT", "DELETE"]
    paths = ["/api/users", "/api/logs", "/api/search", "/health", "/static/app.js"]
    statuses = [200, 200, 200, 201, 204, 400, 401, 404, 500]
    
    for i in range(count):
        timestamp = base_time + timedelta(seconds=i * (86400 / count))
        formatted_time = timestamp.strftime("%d/%b/%Y:%H:%M:%S +0000")
        
        yield (
            f"192.168.1.{random.randint(1, 255)} - - [{formatted_time}] "
            f'"{random.choice(methods)} {random.choice(paths)} HTTP/1.1" '
            f"{random.choice(statuses)} {random.randint(100, 50000)} "
            f'"-" "Mozilla/5.0"'
        )

def main():
    parser = argparse.ArgumentParser(description="Generate test log data")
    parser.add_argument("--count", type=int, default=10000, help="Number of logs")
    parser.add_argument("--format", choices=["json", "nginx"], default="json")
    parser.add_argument("--tenant", default="tenant_demo", help="Tenant ID")
    parser.add_argument("--output", default="-", help="Output file (- for stdout)")
    
    args = parser.parse_args()
    
    if args.format == "json":
        logs = list(generate_json_logs(args.count, args.tenant))
        output = json.dumps({"logs": logs}, indent=2)
    else:
        output = "\n".join(generate_nginx_logs(args.count))
    
    if args.output == "-":
        print(output)
    else:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Generated {args.count} {args.format} logs to {args.output}")

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Generate 10K JSON logs to stdout
python scripts/generate_test_data.py --count 10000 --format json > test_logs.json

# Generate 100K nginx logs to file
python scripts/generate_test_data.py --count 100000 --format nginx --output nginx_access.log

# Generate for specific tenant
python scripts/generate_test_data.py --count 50000 --tenant tenant_acme --output acme_logs.json
```

---

## 7. Testing Strategy

### 7.1 Backend Testing (Beatrice)

**Unit Tests:**
- Query parser: Test all MVP syntax variations
- Log parsers: Test JSON and nginx format parsing
- Aggregation functions: Verify calculations
- Redis caching: Test capped list behavior

**Integration Tests:**
- API endpoints: Test request/response with envelope format
- Database queries: Verify RLS isolation
- WebSocket: Test connection/heartbeat/broadcast logic

**Performance Tests:**
- Query 100K logs: <2s (use generated test data)
- Ingest 1000 logs: <1s
- WebSocket broadcast to 10 clients: <500ms

### 7.2 Frontend Testing (Michael)

**Component Tests:**
- SearchBar: Test query submission
- LogTable: Test rendering with mock data
- Charts: Test Recharts integration
- LiveFeed: Test pause/resume auto-scroll

**Integration Tests:**
- Login flow: Enter credentials → dashboard
- Search flow: Query → results display
- Upload flow: Select file → chunk upload → success message
- WebSocket: Connect → receive logs → handle reconnection

### 7.3 Acceptance Criteria

**Must Have (P0):**
- [ ] User can log in with credentials
- [ ] User can upload a log file via chunked upload
- [ ] User can execute search: `level=ERROR`
- [ ] User can execute aggregation: `| stats count by source`
- [ ] User sees real-time logs in live feed
- [ ] User can pause/resume auto-scroll in live feed
- [ ] Dashboard displays metric cards and time-series chart
- [ ] Multi-tenant isolation via RLS (users only see their logs)
- [ ] WebSocket reconnection works with last_seen_id

**Nice to Have (P1):**
- [ ] Export search results to CSV
- [ ] Query history and favorites
- [ ] Advanced syntax highlighting in search bar

---

## 8. Deployment

### 8.1 Docker Configuration

**Backend Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations on startup, then start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Docker Compose:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: punkt
      POSTGRES_USER: punkt
      POSTGRES_PASSWORD: punkt123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U punkt"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

  backend:
    build: ./punkt-backend
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    environment:
      DATABASE_URL: postgresql://punkt:punkt123@postgres:5432/punkt
      REDIS_URL: redis://redis:6379
      JWT_SECRET: dev-secret-key-not-for-production
      CORS_ORIGINS: http://localhost:3000

  frontend:
    build: ./punkt-frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### 8.2 Environment Variables

**Backend (.env):**
```
DATABASE_URL=postgresql://punkt:punkt123@localhost:5432/punkt
REDIS_URL=redis://localhost:6379
JWT_SECRET=dev-secret-key-not-for-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
CORS_ORIGINS=http://localhost:3000
```

**Frontend (.env):**
```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### 8.3 Running the Application

**Development:**
```bash
# Start infrastructure
docker-compose up postgres redis

# Backend (terminal 1)
cd punkt-backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (terminal 2)
cd punkt-frontend
npm install
npm run dev

# Generate test data
python scripts/generate_test_data.py --count 100000 --output test_data.json
```

**Production (Docker):**
```bash
docker-compose up --build
```

Access application at: `http://localhost:3000`

---

## 9. Security Considerations

> [!WARNING]
> **MVP Security Limitations:** The following security gaps are known and acceptable for this class presentation. These would require remediation before any production deployment.

### 9.1 Known MVP Limitations

| Issue | Risk Level | Remediation for Production |
|-------|------------|---------------------------|
| JWT secret in docker-compose | High | Use secrets management (Vault, AWS Secrets) |
| No rate limiting | Medium | Add rate limiting middleware |
| No input sanitization for query language | Medium | Add query validation and escaping |
| Passwords stored in plaintext (demo) | High | Use bcrypt hashing |
| No HTTPS | High | Add TLS termination |
| No audit logging | Low | Add request logging for compliance |

### 9.2 What IS Implemented

- Row-Level Security for tenant isolation (critical)
- JWT authentication with expiration
- CORS configuration
- Input validation on API endpoints

---

## 10. Success Metrics

### 10.1 Demo Criteria

**Must Successfully Demonstrate:**
1. Login to Punkt dashboard
2. View dashboard with live metrics
3. Upload a log file via chunked upload
4. Watch logs appear in real-time feed
5. Pause and resume auto-scroll
6. Execute search query: `level=ERROR`
7. Execute aggregation: `| stats count by source`
8. View results in table and chart
9. Show multi-tenant isolation (switch tenants, see different data)
10. Demonstrate WebSocket reconnection

### 10.2 Code Quality Metrics

**Backend:**
- Test coverage: >60%
- API response time: <200ms (excluding queries)
- All endpoints use standard envelope format

**Frontend:**
- Bundle size: <500KB gzipped
- Lighthouse performance score: >80
- No console errors on core flows

### 10.3 Documentation Deliverables

- [ ] README.md with setup instructions
- [ ] API documentation (FastAPI auto-generated)
- [ ] Query syntax examples
- [ ] Architecture diagram
- [ ] Demo script

---

## Appendix A: Sample Log Formats

### A.1 Nginx Access Log (Supported)
```
192.168.1.1 - - [07/Feb/2025:14:23:01 +0000] "GET /api/users HTTP/1.1" 200 1234 "-" "Mozilla/5.0"
```

### A.2 Application JSON Log (Supported)
```json
{
  "timestamp": "2025-02-07T14:23:01Z",
  "level": "ERROR",
  "logger": "app.database",
  "message": "Connection pool exhausted",
  "metadata": {
    "pool_size": 20,
    "request_id": "abc-123"
  }
}
```

### A.3 Syslog Format (Post-MVP)
```
Feb  7 14:23:01 web-server-01 sshd[1234]: Failed password for invalid user admin
```

---

## Appendix B: Query Language Grammar (MVP)

```
query := search_terms [ "|" command ]?

search_terms := search_term [ search_term ]*

search_term := 
    | text_search
    | field_filter

field_filter := field_name operator value
operator := "=" | "!=" | ">" | "<" | ">=" | "<="

command :=
    | "stats" aggregation_func "by" field_name
    | "head" number
    | "tail" number
    | "sort" field_name ["asc" | "desc"]

aggregation_func := "count" | "sum" | "avg" | "min" | "max"
```

**MVP Examples:**
```
error
level=ERROR
level=ERROR source=/var/log/app.log
timestamp>"2025-02-07T00:00:00Z"
error | stats count by source
level=WARN | head 100
| sort timestamp desc
```

---

## Document Control

**Version:** 2.0  
**Last Updated:** February 7, 2025  
**Authors:** Product Team  
**Reviewers:** Beatrice (Backend), Michael (Frontend)  
**Status:** Approved for Development (Amended)

**Change Log:**
- v1.0 (Feb 7, 2025): Initial PRD for MVP sprint
- v2.0 (Feb 7, 2025): Architecture review amendments
  - Simplified query language to MVP scope
  - Added PostgreSQL partitioning and RLS
  - Enhanced WebSocket spec (heartbeat, backpressure)
  - Added chunked file upload
  - Limited log formats to JSON + nginx
  - Standardized API envelope
  - Added Alembic migrations
  - Added test data generation script
  - Documented security limitations
