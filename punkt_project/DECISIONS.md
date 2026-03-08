# Punkt Technical Decision Log

This document tracks significant technical decisions made during the development of Punkt, an enterprise log aggregation and analysis platform. Each decision includes context, alternatives considered, rationale, trade-offs, and implications.

---

## Decision Format & Guidelines

### When to Document a Decision

Document a decision when:
- It affects multiple components or team members
- It involves trade-offs that future developers should understand
- It constrains or enables future architectural choices
- It represents a departure from common patterns or expectations
- It was debated or required research to resolve

---

## Core Architecture Decisions

### ADR-001: FastAPI over Flask/Django for Backend Framework

**Date:** 2025-02-07
**Owner:** Beatrice (Backend)
**Status:** Accepted

#### Context

We needed to select a Python web framework for building the Punkt backend. The framework must support REST APIs, WebSocket connections, and async database operations efficiently within a 1-week sprint timeline.

#### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **FastAPI** | Native async support, automatic OpenAPI docs, Pydantic validation, WebSocket support, modern Python typing | Smaller ecosystem than Django, less "batteries included" |
| **Django + DRF** | Mature ecosystem, built-in admin, ORM, excellent documentation | Sync-first architecture, WebSocket requires channels (complex setup), heavier framework |
| **Flask** | Lightweight, flexible, large ecosystem | No built-in async, WebSocket requires extensions, manual validation |

#### Decision

Use **FastAPI** as the backend framework.

#### Rationale

1. **Native async support**: Critical for WebSocket connections and non-blocking database operations with asyncpg
2. **Built-in WebSocket**: No additional library needed for real-time log streaming
3. **Automatic API documentation**: FastAPI generates OpenAPI/Swagger docs automatically, reducing documentation burden
4. **Pydantic integration**: Type-safe request/response validation with minimal code
5. **Performance**: One of the fastest Python frameworks, important for query performance

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Native async/await for I/O operations | Django's built-in admin panel |
| Automatic OpenAPI documentation | Larger community and more tutorials |
| Modern Python type hints | Django ORM (using asyncpg directly) |
| WebSocket support out of the box | "Batteries included" approach |

#### Implications

- Must use asyncpg for database access (no Django ORM)
- Alembic required for migrations (no Django migrations)
- Authentication implemented manually (no Django auth)
- Team needs familiarity with async Python patterns

---

### ADR-002: PostgreSQL over Time-Series Databases

**Date:** 2025-02-07
**Owner:** Beatrice (Backend)
**Status:** Accepted

#### Context

Log data is inherently time-series data. We needed a database that can efficiently store and query millions of log entries with time-based access patterns while supporting multi-tenant isolation.

#### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **PostgreSQL with partitioning** | Familiar SQL, JSONB for metadata, RLS for multi-tenancy, native partitioning, mature ecosystem | Not purpose-built for time-series, requires partition management |
| **TimescaleDB** | Built on PostgreSQL, automatic partitioning, time-series optimized | Additional dependency, learning curve, may be overkill for MVP scale |
| **ClickHouse** | Extremely fast for analytics, columnar storage | Different query language, operational complexity, no RLS |
| **Elasticsearch** | Full-text search, log analysis features | Resource-heavy, separate query language, no ACID transactions |

#### Decision

Use **PostgreSQL 15 with native partitioning** and JSONB for flexible metadata storage.

#### Rationale

1. **Team familiarity**: Both developers know PostgreSQL well; no learning curve
2. **Row-Level Security**: Native RLS provides robust multi-tenant isolation at the database level
3. **JSONB flexibility**: Store variable log metadata without schema migrations
4. **Native partitioning**: PostgreSQL 15 handles partition pruning efficiently
5. **Single database**: Reduces operational complexity vs. adding specialized stores

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Single database to operate | Purpose-built time-series optimizations |
| SQL for all queries | Automatic partition management (TimescaleDB) |
| RLS for tenant isolation | Columnar storage compression (ClickHouse) |
| JSONB flexibility | Full-text search capabilities (Elasticsearch) |
| Team familiarity | Potential scaling limits beyond MVP |

#### Implications

- Must manually create partitions or implement partition creation function
- Full-text search limited to PostgreSQL capabilities
- Performance testing required for 100K log query time
- Schema designed around JSONB for extensibility

---

### ADR-003: Redis for Caching and Real-time State

**Date:** 2025-02-07
**Owner:** Beatrice (Backend)
**Status:** Accepted

#### Context

The application needs a fast cache layer for recent logs, query result caching, and WebSocket connection state management.

#### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Redis** | In-memory speed, rich data structures, pub/sub for broadcasting, well-known | Requires memory management, separate service |
| **In-process cache** | No additional service, simple | Lost on restart, no sharing between processes |
| **Memcached** | Simple, fast | No data structures, no pub/sub, no persistence |
| **PostgreSQL LISTEN/NOTIFY** | No additional service | Limited payload size, not a cache |

#### Decision

Use **Redis 7** for caching recent logs, query results, and WebSocket connection tracking.

#### Rationale

1. **List data structures**: LPUSH/LTRIM pattern perfect for capped recent-log buffers
2. **TTL support**: Automatic expiration for query cache entries
3. **Memory management**: maxmemory-policy prevents unbounded growth
4. **Pub/sub for future scaling**: If horizontal scaling needed, Redis pub/sub broadcasts logs
5. **Operational simplicity**: Single Redis instance adequate for MVP

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Sub-millisecond reads for recent logs | Additional service to operate |
| Rich data structures (Lists, Sets) | Complexity of memory management |
| TTL-based automatic cleanup | Risk of data loss on Redis failure |
| Pub/sub for future scaling | Simpler in-process cache |

#### Implications

- Must configure maxmemory (256MB) and eviction policy (allkeys-lru)
- Recent log cache limited to 1000 entries per tenant
- Query cache uses 5-minute TTL; stale results possible within window
- WebSocket connection state managed in Redis Sets

---

## Data Storage Decisions

### ADR-004: Monthly Partitions over Daily or Weekly

**Date:** 2025-02-07
**Owner:** Beatrice (Backend)
**Status:** Accepted

#### Context

PostgreSQL table partitioning requires choosing a partition granularity. The choice affects query performance, partition management overhead, and storage organization.

#### Options Considered

| Granularity | Partitions/Year | Pros | Cons |
|-------------|-----------------|------|------|
| **Daily** | 365 | Fine-grained pruning, easy archival | Many partitions, management overhead |
| **Weekly** | 52 | Moderate granularity | Odd date boundaries, moderate overhead |
| **Monthly** | 12 | Simple management, natural boundaries | Larger partitions, coarser pruning |

#### Decision

Use **monthly partitions** for log_entries table.

#### Rationale

1. **Management overhead**: 12 partitions/year vs 365 is significantly simpler
2. **MVP scale**: With 1M logs, monthly partitions contain ~83K logs each
3. **Natural boundaries**: Month boundaries align with business reporting
4. **Query patterns**: Most queries span hours to days; monthly still provides effective pruning
5. **Default partition**: Catches data outside defined ranges, preventing insert failures

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Simpler partition management | Fine-grained partition pruning |
| Fewer objects in database | Smaller partition sizes |
| Natural date boundaries | Flexibility for daily archival |

#### Implications

- Partition creation function runs on startup for current + 2 future months
- Queries spanning multiple months touch multiple partitions
- Old data archival would be month-granular
- Default partition catches edge cases

---

### ADR-005: Row-Level Security over Application-Level Filtering

**Date:** 2025-02-07
**Owner:** Beatrice (Backend)
**Status:** Accepted

#### Context

Punkt is a multi-tenant application where each tenant must only see their own log data. We must choose enforcement at database or application level.

#### Options Considered

| Approach | Pros | Cons |
|----------|------|------|
| **PostgreSQL RLS** | Enforced at database level, impossible to bypass, automatic filtering | Requires session variable setup, slightly complex testing |
| **Application-level WHERE clauses** | Simpler to understand, no PostgreSQL-specific features | Easy to forget, every query needs tenant_id, bugs leak data |
| **Separate databases per tenant** | Complete isolation, simple queries | Operational nightmare, connection pool explosion |
| **Separate schemas per tenant** | Strong isolation, shared infrastructure | Schema management complexity, migrations across schemas |

#### Decision

Use **PostgreSQL Row-Level Security (RLS)** with `app.current_tenant` session variable.

#### Rationale

1. **Defense in depth**: Even if application code misses a WHERE clause, RLS prevents data leakage
2. **Automatic filtering**: All queries against log_entries automatically filter by tenant
3. **Audit compliance**: Database-enforced security is easier to audit
4. **Developer experience**: Developers write simpler queries without tenant_id boilerplate
5. **Single policy point**: Tenant logic defined once in policy, not scattered across queries

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Database-enforced isolation | Portability (PostgreSQL-specific) |
| Simpler application queries | Testing complexity (must set session variable) |
| Impossible to accidentally leak data | Debugging complexity (invisible filtering) |
| Audit-friendly security model | Slight performance overhead (minimal) |

#### Implications

- Middleware MUST set `app.current_tenant` session variable on every request
- Database role (punkt_app) must have RLS policies applied
- Testing requires explicit tenant context setup
- Cross-tenant queries require separate role or policy exceptions

---

### ADR-006: JSONB for Log Metadata over Structured Columns

**Date:** 2025-02-07
**Owner:** Beatrice (Backend)
**Status:** Accepted

#### Context

Log entries contain variable metadata (host, request_id, user_id, etc.) that differs by source. We need a strategy that handles variability without constant schema changes.

#### Options Considered

| Approach | Pros | Cons |
|----------|------|------|
| **JSONB column** | Schema-flexible, GIN indexable, PostgreSQL-native | No strict typing, larger storage, JSON query syntax |
| **EAV (Entity-Attribute-Value)** | Fully normalized, traditional SQL | Slow queries, complex joins |
| **Fixed wide columns** | Predictable schema, fast queries | Sparse data waste, schema changes needed |
| **Separate metadata table** | Normalized, flexible | Joins on every query, complexity |

#### Decision

Use a **JSONB column** (`metadata`) with a GIN index for flexible metadata storage.

#### Rationale

1. **Schema flexibility**: New log sources can have unique fields without migrations
2. **Query capability**: PostgreSQL JSONB operators enable metadata field queries
3. **GIN indexing**: Index supports containment queries (@>) and key existence (?)
4. **Storage efficiency**: JSONB is compressed and deduplicates keys
5. **MVP velocity**: No need to predict all possible metadata fields upfront

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| No schema changes for new fields | Strong typing on metadata fields |
| Flexible per-source metadata | Simpler SQL syntax |
| GIN index for containment queries | Optimal column-specific indexes |
| Single column for all metadata | Clear data dictionary |

#### Implications

- Query parser must translate metadata field filters to JSONB operators
- GIN index supports `metadata @> '{"host": "server-01"}'` queries
- No foreign keys or constraints on metadata values
- Documentation needed for expected metadata fields per source
- Raw log preserved in `raw_log` column for troubleshooting

---

## API Design Decisions

### ADR-007: Chunked Upload over Direct File Upload

**Date:** 2025-02-07
**Owner:** Beatrice (Backend)
**Status:** Accepted

#### Context

Users need to upload log files up to 100MB. We must handle large uploads without exhausting server memory or causing timeout issues.

#### Options Considered

| Approach | Pros | Cons |
|----------|------|------|
| **Chunked upload (multi-part)** | Memory efficient, resumable, progress tracking | More complex protocol, multiple requests |
| **Direct upload (single request)** | Simple implementation, single request | Memory exhaustion risk, no progress, timeout risk |
| **Pre-signed URL to object storage** | Offloads to S3/GCS, scales well | Additional infrastructure, latency |
| **Streaming upload** | Memory efficient | No resume, complex buffering |

#### Decision

Use **chunked upload** with three-phase protocol: init, chunk upload, complete.

#### Rationale

1. **Memory safety**: 1MB chunks mean server never holds >1MB of upload in memory
2. **Progress tracking**: Frontend can show chunk-by-chunk progress bar
3. **Resumability**: If chunk fails, only that chunk needs retry
4. **Timeout avoidance**: Small requests complete quickly
5. **MVP simplicity**: More complex than direct upload but avoids S3 infrastructure

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Memory-safe processing | Simple single-request upload |
| Resume capability | Simpler frontend implementation |
| Progress visibility | Fewer API endpoints |
| Timeout immunity | State management (upload_id tracking) |

#### Implications

- Three endpoints: `/ingest/file/init`, `/ingest/file/chunk`, `/ingest/file/complete`
- Server must track upload state (upload_id -> temp file location)
- Cleanup job needed for abandoned uploads
- Frontend must implement chunk sequencing and retry logic
- Chunk size fixed at 1MB

---

### ADR-008: Standardized API Response Envelope

**Date:** 2025-02-07
**Owner:** Beatrice (Backend), Michael (Frontend)
**Status:** Accepted

#### Context

Frontend and backend need to agree on a consistent response format for all API endpoints. This affects error handling, loading states, and data extraction patterns.

#### Options Considered

| Approach | Pros | Cons |
|----------|------|------|
| **Envelope format** | Consistent structure, explicit success/error, metadata slot | Slightly verbose, extra nesting |
| **Direct data responses** | Less verbose, straightforward | Inconsistent error handling, no metadata slot |
| **JSON:API spec** | Industry standard, relationships | Complex for this use case |
| **GraphQL** | Flexible queries, typed | Different paradigm, overkill for MVP |

#### Decision

Use a **standardized envelope format** for all API responses:
```json
{
  "success": true/false,
  "data": { ... } or null,
  "error": { "code": "...", "message": "..." } or null,
  "timestamp": "ISO8601"
}
```

#### Rationale

1. **Predictable parsing**: Frontend always knows where to find data vs errors
2. **Explicit success flag**: No ambiguity about whether request succeeded
3. **Error structure**: Consistent error codes enable centralized error handling
4. **Timestamp**: Useful for debugging and cache invalidation
5. **Extensible**: Can add pagination, rate limit info without breaking contract

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Consistent client-side handling | Minimal response size |
| Explicit error codes | Direct data access |
| Metadata slot for extensions | Simplicity of ad-hoc responses |
| Timestamp for debugging | Slight additional complexity |

#### Implications

- ALL endpoints must use this envelope - no exceptions
- Error codes must be documented and used consistently
- Frontend can create single response handler for all API calls
- FastAPI response models enforce envelope structure
- 4xx/5xx status codes still used; envelope provides detail

---

### ADR-009: JWT with Embedded tenant_id over Session Cookies

**Date:** 2025-02-07
**Owner:** Beatrice (Backend)
**Status:** Accepted

#### Context

Authentication must identify users and their tenant for RLS enforcement. We need a mechanism that works for both REST API calls and WebSocket connections.

#### Options Considered

| Approach | Pros | Cons |
|----------|------|------|
| **JWT with tenant_id** | Stateless, works with WebSocket, self-contained | Token size, revocation complexity |
| **Session cookies** | Built-in browser handling, easy revocation | CSRF concerns, doesn't work well with WebSocket |
| **API keys** | Simple, good for service-to-service | No user identity, harder to rotate |
| **OAuth2 with external IdP** | Enterprise-ready, delegated auth | Complexity, external dependency |

#### Decision

Use **JWT tokens** with `tenant_id` embedded in the payload, passed via `Authorization: Bearer` header.

#### Rationale

1. **WebSocket compatibility**: JWT can be passed during WebSocket handshake; cookies are problematic
2. **Stateless**: No server-side session storage needed
3. **Self-contained**: tenant_id in token means no database lookup to determine tenant
4. **RLS integration**: Middleware extracts tenant_id from JWT to set `app.current_tenant`
5. **Standard pattern**: Well-understood, library support in both Python and JavaScript

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Stateless authentication | Easy token revocation |
| WebSocket compatibility | Smaller token size |
| No session storage | Built-in browser cookie handling |
| tenant_id always available | Ability to change tenant without re-login |

#### Implications

- JWT secret must be kept secure (environment variable)
- Token expiration set to 24 hours; refresh mechanism needed
- Logout is client-side only (token deletion)
- Token includes: user_id, tenant_id, exp, iat
- Middleware extracts tenant_id for every authenticated request

---

## Real-time Features Decisions

### ADR-010: WebSocket over Server-Sent Events or Polling

**Date:** 2025-02-07
**Owner:** Beatrice (Backend), Michael (Frontend)
**Status:** Accepted

#### Context

Punkt needs real-time log streaming to show new logs as they are ingested. We must choose a technology for pushing data from server to client.

#### Options Considered

| Approach | Pros | Cons |
|----------|------|------|
| **WebSocket** | Bidirectional, low overhead after handshake, widely supported | Connection management, more complex than SSE |
| **Server-Sent Events (SSE)** | Simple, unidirectional, auto-reconnect | Unidirectional only, limited browser connections |
| **Long polling** | Works everywhere, simple | High overhead, latency, server resource usage |
| **HTTP/2 Server Push** | Efficient | Not for real-time, limited support |

#### Decision

Use **WebSocket** for real-time log streaming with heartbeat and reconnection support.

#### Rationale

1. **Bidirectional**: Client can send filter subscriptions, not just receive logs
2. **Low latency**: <500ms latency requirement is easily met
3. **Efficiency**: Single persistent connection vs repeated HTTP requests
4. **FastAPI support**: Native WebSocket support in FastAPI
5. **Filter subscriptions**: Client can send subscription messages to filter by source/level

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Bidirectional communication | Simplicity of SSE |
| Low latency | SSE's automatic reconnection |
| Single connection per client | Stateless request model |
| Client-controlled filters | HTTP caching |

#### Implications

- WebSocket endpoint: `/ws/{tenant_id}`
- Heartbeat required: ping every 30s, pong within 10s or disconnect
- Reconnection with `last_seen_id` to catch missed logs
- Backpressure handling for slow clients (drop old messages)
- Connection state tracked in Redis

---

### ADR-011: Drop Messages for Slow Clients over Blocking or Buffering

**Date:** 2025-02-07
**Owner:** Beatrice (Backend)
**Status:** Accepted

#### Context

When log ingestion is faster than a WebSocket client can consume messages, we must decide how to handle backpressure.

#### Options Considered

| Approach | Pros | Cons |
|----------|------|------|
| **Drop old messages** | Protects server resources, clients see newest logs | Data loss for slow clients |
| **Block ingestion** | No data loss | Slow client blocks entire system |
| **Unlimited buffer** | No data loss | Memory exhaustion risk |
| **Disconnect slow clients** | Simple, frees resources | Bad user experience |

#### Decision

**Drop oldest messages** when client queue exceeds 100 pending messages. Notify client with dropped count.

#### Rationale

1. **System protection**: One slow client cannot affect others or block ingestion
2. **Most recent data**: Users care most about recent logs; old logs can be queried
3. **Graceful degradation**: Client is warned about drops, can use search for complete data
4. **Bounded memory**: Maximum 100 pending messages per client
5. **User feedback**: Warning message tells client they're behind

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| System stability | Complete real-time data for slow clients |
| Bounded resource usage | Zero data loss |
| Other clients unaffected | Simple implementation |
| Graceful degradation with warnings | Perfect ordering guarantee |

#### Implications

- MAX_PENDING_MESSAGES = 100 per client
- When limit exceeded, drop oldest 50, keep newest 50
- Send warning message with dropped count periodically
- Client can use `last_seen_id` on reconnection to query missed logs
- Frontend should display warning when received

---

## Query Engine Decisions

### ADR-012: Simplified MVP Query Language over Full Splunk-like Syntax

**Date:** 2025-02-07
**Owner:** Beatrice (Backend)
**Status:** Accepted

#### Context

A powerful query language is essential for log analysis, but implementing a full parser is time-consuming. We must balance capability with the 1-week sprint timeline.

#### Options Considered

| Scope | Features | Complexity | Timeline Risk |
|-------|----------|------------|---------------|
| **Full Splunk-like** | OR, AND, NOT, parentheses, pipes, chained, timechart | High | Very high |
| **MVP subset** | Implicit AND, field filters, single aggregation, sort/head/tail | Medium | Acceptable |
| **Basic filters only** | Field equals/not-equals, no aggregation | Low | Safe |

#### Decision

Implement **MVP subset** query language:
- Text search and field filters with implicit AND
- Single pipe command: `stats`, `head`, `tail`, `sort`
- No OR logic, no parentheses, no chained commands

#### Rationale

1. **80/20 rule**: Most queries are simple field filters
2. **Timeline safety**: Full parser could consume 3+ days; MVP is ~1 day
3. **Clear upgrade path**: Grammar designed to extend with OR, parentheses later
4. **Demonstration value**: Even simple queries show platform capability
5. **User testing**: Learn what queries users actually need before building full parser

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Deliverable in timeline | OR logic (level=ERROR OR level=CRITICAL) |
| Reduced parser complexity | Parentheses for grouping |
| Clear scope boundaries | Chained pipes (stats ... \| sort ... \| head) |
| Foundation for iteration | NOT operator |

#### Implications

- Document post-MVP features clearly for future development
- Query parser designed for extension (grammar is subset of full)
- Users may need multiple queries for complex conditions
- Marketing/demo should focus on MVP capabilities
- Post-MVP: Add OR, parentheses, timechart, NOT in priority order

---

### ADR-013: Query Result Caching Strategy

**Date:** 2025-02-07
**Owner:** Beatrice (Backend)
**Status:** Accepted

#### Context

Query performance requirement is <2s for 100K logs. Caching can help with repeated queries, but log data is constantly changing.

#### Options Considered

| Strategy | Freshness | Performance | Complexity |
|----------|-----------|-------------|------------|
| **No caching** | Perfect | Slowest | Lowest |
| **Short TTL (5 min)** | Acceptable | Good | Low |
| **Invalidation-based** | Perfect | Good | High |
| **Stale-while-revalidate** | Good | Best | Medium |

#### Decision

Use **short TTL caching (5 minutes)** for query results in Redis.

#### Rationale

1. **Implementation simplicity**: TTL expiration requires no invalidation logic
2. **Acceptable staleness**: For dashboards, 5-minute-old data is acceptable
3. **Repeated query benefit**: Same dashboard refreshes hit cache
4. **Memory management**: TTL prevents cache growth
5. **MVP appropriate**: More sophisticated caching adds complexity

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Simple implementation | Real-time query accuracy |
| Reduced database load | Immediate consistency |
| Fast repeated queries | Memory for unique queries |
| Automatic cleanup | Cache warm-up on cold start |

#### Implications

- Cache key: hash of (query, start, end, tenant_id)
- TTL: 300 seconds (5 minutes)
- New log ingestion does NOT invalidate cache (by design)
- Real-time feed is separate from cached queries
- Large result sets may not fit in cache

---

## Frontend Architecture Decisions

### ADR-014: Tailwind CSS over Component Libraries or CSS-in-JS

**Date:** 2025-02-07
**Owner:** Michael (Frontend)
**Status:** Accepted

#### Context

We need a styling approach for the React frontend that enables rapid development while maintaining professional appearance.

#### Options Considered

| Approach | Pros | Cons |
|----------|------|------|
| **Tailwind CSS** | Utility-first, fast iteration, small bundle, design system built-in | Verbose classNames, learning curve |
| **CSS Modules** | Scoped styles, familiar CSS | No design system, more files, slower iteration |
| **Styled-components** | Component-scoped, dynamic styles | Bundle size, runtime overhead |
| **Material UI / Chakra** | Pre-built components, consistent | Large bundle, opinionated design |

#### Decision

Use **Tailwind CSS** with utility classes for all styling.

#### Rationale

1. **Speed**: No context switching between files; style inline with markup
2. **Design tokens**: Built-in spacing, colors, typography scales
3. **Bundle size**: PurgeCSS removes unused utilities; small production build
4. **Customization**: Easy to match brand colors (purple primary)
5. **No component lock-in**: Build custom components, not locked to library

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Rapid prototyping | Pre-built component library |
| Small bundle size | Familiar CSS file structure |
| Consistent design tokens | Semantic class names |
| Full design control | Out-of-the-box component styling |

#### Implications

- All team members must learn Tailwind utility classes
- Custom components built from scratch
- Color palette configured in tailwind.config.js
- Log level colors defined as custom utilities
- Consider Headless UI for accessible interactive components

---

### ADR-015: React Context over Redux/Zustand for State Management

**Date:** 2025-02-07
**Owner:** Michael (Frontend)
**Status:** Accepted

#### Context

The frontend needs to manage state for authentication, WebSocket connection, and UI preferences.

#### Options Considered

| Approach | Pros | Cons |
|----------|------|------|
| **React Context + Hooks** | Built-in, simple, no dependencies | Prop drilling for deep trees, re-render concerns |
| **Redux Toolkit** | Powerful, devtools, middleware | Boilerplate, learning curve, overkill |
| **Zustand** | Simple, lightweight, minimal boilerplate | Another dependency, less ecosystem |
| **Jotai/Recoil** | Atomic state, fine-grained updates | Learning curve, newer patterns |

#### Decision

Use **React Context with custom hooks** for state management.

#### Rationale

1. **No additional dependencies**: React Context is built-in
2. **MVP scale**: State is limited (auth, WebSocket, preferences)
3. **Simplicity**: Fewer concepts for team to learn
4. **Custom hooks**: Encapsulate Context consumption in reusable hooks
5. **Upgrade path**: Can add Zustand later if Context becomes limiting

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Zero dependencies | Redux DevTools |
| Simpler mental model | Middleware for async actions |
| Faster initial setup | Fine-grained re-render control |
| Standard React patterns | Time-travel debugging |

#### Implications

- Create separate contexts: AuthContext, WebSocketContext, ThemeContext
- Custom hooks: useAuth(), useWebSocket(), useTheme()
- Avoid putting frequently-changing data in Context
- React.memo for expensive child components
- Server state (logs, search results) managed by component state

---

### ADR-016: TanStack Virtual for Log Table Virtualization

**Date:** 2025-02-07
**Owner:** Michael (Frontend)
**Status:** Accepted

#### Context

Search results may return thousands of log entries. Rendering all rows causes performance issues. We need virtualization to render only visible rows.

#### Options Considered

| Library | Pros | Cons |
|---------|------|------|
| **TanStack Virtual** | Lightweight, flexible, headless | Build table UI from scratch |
| **react-window** | Popular, simple API | Less flexible, fixed item sizes |
| **react-virtualized** | Feature-rich, many components | Heavy, complex API |
| **ag-Grid** | Enterprise features, fast | Large bundle, commercial license |

#### Decision

Use **TanStack Virtual** for virtualized log table rendering.

#### Rationale

1. **Headless approach**: Full control over table markup and styling (works with Tailwind)
2. **Lightweight**: Small bundle size (~3KB)
3. **Variable row heights**: Log messages vary in length; fixed heights waste space
4. **Modern React**: Hooks-based API, maintained actively
5. **Same family**: Consistent with TanStack Query if added later

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Full styling control | Pre-built table component |
| Small bundle size | Built-in features (sorting, filtering) |
| Variable row heights | Zero-config setup |
| Flexibility | Learning curve for headless pattern |

#### Implications

- Must build table markup manually (headers, rows, cells)
- Sorting/filtering handled at API level
- Row height estimation needed for variable height rows
- Smooth scrolling for large result sets (10K+)
- Expandable rows for full log details

---

## Security Decisions

### ADR-017: Accept Known MVP Security Limitations

**Date:** 2025-02-07
**Owner:** Beatrice (Backend)
**Status:** Accepted

#### Context

Production-grade security requires significant investment. For a 1-week sprint creating a class presentation demo, we must decide which security measures to implement vs. document as known limitations.

#### Security Measures Evaluated

| Measure | MVP Decision | Production Requirement |
|---------|--------------|----------------------|
| Row-Level Security | **Implement** | Critical |
| JWT Authentication | **Implement** | Critical |
| Input Validation | **Implement** | Critical |
| CORS Configuration | **Implement** | Required |
| Password Hashing | **Defer** (plaintext demo) | Critical |
| HTTPS/TLS | **Defer** | Critical |
| Rate Limiting | **Defer** | Important |
| Query Sanitization | **Defer** | Important |
| Secrets Management | **Defer** (env vars) | Critical |
| Audit Logging | **Defer** | Compliance |

#### Decision

Implement **core security measures** (RLS, JWT, validation, CORS) and **document all deferred items** as known limitations.

#### Rationale

1. **Tenant isolation is critical**: Data leakage would be demo-breaking; RLS is non-negotiable
2. **Authentication is visible**: Login flow is part of demo; must work correctly
3. **Other risks are acceptable**: For class demo, no real data, no real users, no public exposure
4. **Transparency**: Documenting limitations shows security awareness

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Deliverable in 1 week | Production-ready security |
| Focus on features | Defense in depth |
| Demo functionality | Security hardening |
| Documented limitations | Peace of mind |

#### Implications

- WARNING added to documentation about MVP security status
- No real passwords or sensitive data in demo
- System must NOT be deployed publicly
- Post-MVP security sprint would address all deferred items
- Demo script mentions security as future enhancement

---

## DevOps Decisions

### ADR-018: Docker Compose for Development and Demo

**Date:** 2025-02-07
**Owner:** Beatrice (Backend), Michael (Frontend)
**Status:** Accepted

#### Context

The application has multiple components (backend, frontend, PostgreSQL, Redis). We need a consistent way to run everything locally and for demos.

#### Options Considered

| Approach | Pros | Cons |
|----------|------|------|
| **Docker Compose** | Single command startup, reproducible, isolates dependencies | Docker knowledge required, resource usage |
| **Manual local install** | No Docker needed, native performance | "Works on my machine" issues |
| **Kubernetes (minikube)** | Production-like | Overkill for MVP, complex |
| **Cloud deployment** | Accessible anywhere | Cost, deployment complexity |

#### Decision

Use **Docker Compose** for all services with ability to run backend/frontend natively for development.

#### Rationale

1. **Reproducibility**: Same environment for both developers
2. **Single command**: `docker-compose up` starts everything
3. **Dependency isolation**: PostgreSQL and Redis versions locked
4. **Demo portability**: Can run demo on any Docker-capable machine
5. **Development flexibility**: Can run app natively against Compose infrastructure

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Consistent environments | Slightly slower startup than native |
| Easy infrastructure setup | Docker knowledge requirement |
| Demo portability | Direct debugging (use native for this) |
| Version-locked dependencies | Disk space for images |

#### Implications

- docker-compose.yml with: postgres, redis, backend, frontend
- Health checks for startup ordering
- Volume mounts for persistence
- Documented native development workflow as alternative
- Hot reload works with volume mounts

---

### ADR-019: Alembic for Database Migrations

**Date:** 2025-02-07
**Owner:** Beatrice (Backend)
**Status:** Accepted

#### Context

Database schema will evolve. We need a migration tool that works with asyncpg and can handle PostgreSQL-specific features like partitioning and RLS.

#### Options Considered

| Tool | Pros | Cons |
|------|------|------|
| **Alembic** | SQLAlchemy integration, raw SQL support, mature | Learning curve, boilerplate |
| **Django migrations** | Excellent UX | Requires Django, sync-only |
| **Flyway** | Simple, SQL files | Java dependency, less Python-friendly |
| **Manual SQL scripts** | Full control | No version tracking, error-prone |

#### Decision

Use **Alembic** with raw SQL migrations for PostgreSQL-specific features.

#### Rationale

1. **Industry standard**: Go-to for Python projects without Django
2. **Raw SQL support**: Partition creation, RLS policies require raw SQL
3. **Version tracking**: Migrations are versioned and can be rolled back
4. **Docker integration**: Runs migrations on container startup
5. **Team familiarity**: Common tool, documentation available

#### Trade-offs

| Gained | Sacrificed |
|--------|------------|
| Version-controlled schema changes | Django's migration UX |
| Rollback capability | Simpler raw SQL approach |
| CI/CD integration | Zero learning curve |
| Raw SQL for complex features | Auto-generated migrations |

#### Implications

- alembic/ directory with migration scripts
- Initial migration creates partitioned table + RLS
- Subsequent migrations for schema evolution
- Run `alembic upgrade head` on startup
- Raw SQL for partition creation functions

---

## Decision Timeline

| Date | ID | Decision | Status |
|------|-----|----------|--------|
| 2025-02-07 | ADR-001 | FastAPI over Flask/Django | Accepted |
| 2025-02-07 | ADR-002 | PostgreSQL over Time-Series DBs | Accepted |
| 2025-02-07 | ADR-003 | Redis for Caching | Accepted |
| 2025-02-07 | ADR-004 | Monthly Partitions | Accepted |
| 2025-02-07 | ADR-005 | RLS over App-Level Filtering | Accepted |
| 2025-02-07 | ADR-006 | JSONB for Metadata | Accepted |
| 2025-02-07 | ADR-007 | Chunked Upload | Accepted |
| 2025-02-07 | ADR-008 | Standardized API Envelope | Accepted |
| 2025-02-07 | ADR-009 | JWT with tenant_id | Accepted |
| 2025-02-07 | ADR-010 | WebSocket over SSE | Accepted |
| 2025-02-07 | ADR-011 | Drop Messages for Slow Clients | Accepted |
| 2025-02-07 | ADR-012 | Simplified MVP Query Language | Accepted |
| 2025-02-07 | ADR-013 | Query Result Caching (5min TTL) | Accepted |
| 2025-02-07 | ADR-014 | Tailwind CSS | Accepted |
| 2025-02-07 | ADR-015 | React Context over Redux | Accepted |
| 2025-02-07 | ADR-016 | TanStack Virtual | Accepted |
| 2025-02-07 | ADR-017 | Accept MVP Security Limitations | Accepted |
| 2025-02-07 | ADR-018 | Docker Compose | Accepted |
| 2025-02-07 | ADR-019 | Alembic Migrations | Accepted |

---

## Post-MVP Decisions (Future Reference)

These decisions are documented for future development but NOT implemented in MVP.

### POST-001: Query Language Extensions

**Future Decision Needed:** How to extend query language with OR, parentheses, NOT

**Options to Evaluate:**
1. Parser generator (PLY, Lark) for full grammar
2. Hand-written recursive descent parser
3. Existing query language library

### POST-002: Horizontal Scaling Strategy

**Future Decision Needed:** How to scale beyond single-instance

**Options to Evaluate:**
1. Redis pub/sub for WebSocket broadcast across instances
2. Dedicated message broker (RabbitMQ, Kafka)
3. PostgreSQL LISTEN/NOTIFY

### POST-003: Log Format Auto-Detection

**Future Decision Needed:** Automatically detect log format instead of user-specified

### POST-004: Full-Text Search Enhancement

**Future Decision Needed:** How to improve search beyond PostgreSQL LIKE

### POST-005: Authentication Enhancement

**Future Decision Needed:** Enterprise authentication integration (SAML/OIDC)

---

*Document Version: 1.0*
*Last Updated: February 2025*
