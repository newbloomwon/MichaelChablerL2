"""
api_server.py — FastAPI Backend for AI Grid Orchestrator
=========================================================
Exposes grid data as a REST API for the Streamlit dashboard
and any other consumers.

Run:
    uvicorn api_server:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import ingestion_worker
from maine_ingestion import fetch_maine_snapshot
from texas_ingestion import fetch_texas_snapshot
from snapshot_store import get_latest, get_history, get_all_latest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# ---------------------------------------------------------------------------
# App lifespan — start/stop the background worker
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start ingestion worker on startup, stop on shutdown."""
    # Startup: kick off background polling
    ingestion_worker.start(interval=60)
    yield
    # Shutdown: clean up worker
    ingestion_worker.stop()


app = FastAPI(
    title="AI Grid Orchestrator API",
    version="0.1.0",
    description="Real-time grid monitoring for Maine (and later Texas).",
    lifespan=lifespan,
)

# Allow Streamlit or any frontend to hit this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "service": "AI Grid Orchestrator API",
        "version": "0.1.0",
        "endpoints": [
            "/snapshot/maine",
            "/snapshot/maine/live",
            "/snapshot/maine/history",
            "/snapshot/texas",
            "/snapshot/texas/live",
            "/snapshot/texas/history",
            "/snapshot/all",
            "/health",
        ],
    }


@app.get("/health")
def health():
    """Health check for the API."""
    return {"status": "ok"}


@app.get("/snapshot/maine")
def snapshot_maine():
    """
    Get the latest cached Maine snapshot from the background worker.
    Updates every 60 seconds.
    """
    return get_latest("maine")


@app.get("/snapshot/maine/live")
def snapshot_maine_live():
    """
    Fetch a FRESH Maine snapshot right now (bypasses cache).
    Useful for one-off checks, but slower.
    """
    return fetch_maine_snapshot()


@app.get("/snapshot/maine/history")
def snapshot_maine_history(limit: int = 60):
    """
    Get the last N Maine snapshots (default: 60 ≈ 1 hour).
    Used by the dashboard for trend charts.
    """
    return get_history("maine", limit)


@app.get("/snapshot/all")
def snapshot_all():
    """
    Get the latest snapshot for every state we're tracking.
    Returns { "maine": {...}, "texas": {...} }.
    """
    return get_all_latest()


# ---------------------------------------------------------------------------
# Texas endpoints
# ---------------------------------------------------------------------------

@app.get("/snapshot/texas")
def snapshot_texas():
    """
    Get the latest cached Texas snapshot from the background worker.
    Updates every 60 seconds.
    """
    return get_latest("texas")


@app.get("/snapshot/texas/live")
def snapshot_texas_live():
    """
    Fetch a FRESH Texas snapshot right now (bypasses cache).
    Useful for one-off checks, but slower.
    """
    return fetch_texas_snapshot()


@app.get("/snapshot/texas/history")
def snapshot_texas_history(limit: int = 60):
    """
    Get the last N Texas snapshots (default: 60 ≈ 1 hour).
    Used by the dashboard for trend charts.
    """
    return get_history("texas", limit)
# @app.get("/snapshot/texas")
# def snapshot_texas():
#     return get_latest("texas")
