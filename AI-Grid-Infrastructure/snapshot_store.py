"""
snapshot_store.py — In-Memory Snapshot History
================================================
Stores the last N grid snapshots for both Maine and (later) Texas.
Used by the dashboard and Logic Engine to show trends.
"""

from collections import deque
from threading import Lock
from datetime import datetime, timezone

# Keep last 60 snapshots per state (≈ 1 hour at 60s intervals)
MAX_HISTORY = 60

_stores = {
    "maine": deque(maxlen=MAX_HISTORY),
    "texas": deque(maxlen=MAX_HISTORY),  # Ready for Ibrahima's merge
}
_lock = Lock()


def save_snapshot(snapshot: dict):
    """Save a snapshot to the in-memory store."""
    state = snapshot.get("state", "unknown")
    with _lock:
        if state not in _stores:
            _stores[state] = deque(maxlen=MAX_HISTORY)
        _stores[state].append(snapshot)


def get_latest(state: str) -> dict:
    """Get the most recent snapshot for a given state."""
    with _lock:
        store = _stores.get(state, deque())
        return store[-1] if store else {}


def get_history(state: str, limit: int = MAX_HISTORY) -> list:
    """Get the last `limit` snapshots for a given state."""
    with _lock:
        store = _stores.get(state, deque())
        items = list(store)
        return items[-limit:]


def get_all_latest() -> dict:
    """Get the latest snapshot for every state we're tracking."""
    result = {}
    for state in _stores:
        latest = get_latest(state)
        if latest:
            result[state] = latest
    return result
