# Punkt - Demo Guide

Welcome to the Punkt demo! This guide walks you through the key features of the platform, from authentication to real-time analysis.

## Setup

Start the full stack with Docker Compose:

```bash
docker-compose up --build
```

Wait ~30 seconds for all services to pass health checks, then open:
- **Dashboard**: http://localhost:3000
- **API docs**: http://localhost:8000/docs

**Demo credentials** (seeded automatically by migrations):

| Username | Password |
|----------|----------|
| `demo@acme.com` | `demo123` |

**Start the demo log stream** (in a separate terminal, after Docker is healthy):

```bash
cd punkt-backend
python -m scripts.demo_stream
```

This continuously streams synthetic logs to the backend, populating the Live Feed
in real time. Leave it running throughout the demo. Press Ctrl+C to stop.

---

## Scenario 1: Authentication & Dashboard Overview

1. **Login**: Open http://localhost:3000. Enter `demo@acme.com` / `demo123` and click **Authenticate**.
2. **Dashboard**: Once logged in, observe the **System Overview**:
   - **Metric Cards**: Real-time stats including "Total Logs Today" and "Error Rate"
   - **Live Stream Status**: The pulsing "Live Stream Connected" indicator in the top right
   - **Charts**: The "Log Volume by Hour" time-series chart showing ingest trends

## Scenario 2: Real-time Log Monitoring

1. **Navigate to Search**: Click **Logs** in the sidebar.
2. **Live Feed Controls**:
   - In the right panel, observe incoming logs streaming in real-time.
   - Click **Pause** — a "X new logs buffered" notification appears as logs continue arriving in the background.
   - Click **Resume** to instantly catch up to the latest logs.
   - Use the **Clear** (trash icon) to wipe the current buffer.

## Scenario 3: Log Ingestion

1. **Navigate to Ingest**: Click **Ingest** in the sidebar.
2. **Upload a file**:
   - Drag and drop or select a `.json` or nginx access log file.
   - Watch the **chunked upload** progress bar — large files are split into managed chunks.
   - A success notification confirms ingestion; logs appear in the live feed within seconds.

## Scenario 4: Powerful Search & Analysis

1. **Navigate to Search**: Click **Logs** in the sidebar.
2. **Execute a query** — try these in the search bar:

   | Query | What it does |
   |-------|-------------|
   | `level=ERROR` | All error logs |
   | `level=ERROR source=nginx` | Errors from nginx only |
   | `"connection refused"` | Full-text search |
   | `level=ERROR \| stats count by source` | Error count per source |
   | `level!=DEBUG \| head 50` | Latest 50 non-debug logs |

3. **Inspect metadata**: Click any log row to expand the full JSON metadata.
4. **Export**: Click **Export Results** to download the current view as a CSV file.

## Scenario 5: Infrastructure Management

1. **Navigate to Sources**: Click **Sources** in the sidebar.
2. **Fleet overview**:
   - Review all active log sources for your tenant.
   - Check the **Last Seen** column to spot stale or silent emitters.
   - Click the **Search** icon on any source to jump to filtered logs for that source.

---

## Query Cheat Sheet

```
# Field filters (implicit AND)
level=ERROR
level=ERROR source=nginx
timestamp>2025-02-07T00:00:00Z

# Text search
"connection refused"
"timeout" level=ERROR

# Aggregations
level=ERROR | stats count by source
| stats avg response_time by source
| stats max response_time by source

# Modifiers
| head 50
| sort timestamp desc
| sort level asc
```

**Tip**: Use the Help icon in the search bar for inline query examples!
