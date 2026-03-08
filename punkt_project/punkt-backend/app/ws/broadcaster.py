"""Broadcast service for real-time log streaming.

Bridges the log ingestion pipeline with connected WebSocket clients.
"""
import logging
from typing import Any, Dict, List, Optional

from app.ws.manager import ws_manager

logger = logging.getLogger(__name__)


async def broadcast_log(
    tenant_id: str,
    log_entry: Dict[str, Any],
) -> int:
    """
    Broadcast a single log entry to all connected clients for a tenant.

    Args:
        tenant_id: Tenant ID
        log_entry: Log dict with timestamp, level, source, message, metadata

    Returns:
        Number of clients the message was queued for
    """
    message = {
        "type": "log",
        "payload": log_entry,
    }
    await ws_manager.broadcast(tenant_id, message)
    return ws_manager.get_connected_count(tenant_id)


async def broadcast_batch(
    tenant_id: str,
    log_entries: List[Dict[str, Any]],
) -> int:
    """
    Broadcast a batch of log entries as a single message.

    Preferred over calling broadcast_log() in a loop for high-volume
    ingestion because it results in one queue put per client instead of N.

    Args:
        tenant_id: Tenant ID
        log_entries: List of log entry dicts

    Returns:
        Number of clients the batch was queued for
    """
    if not log_entries:
        return 0

    message = {
        "type": "log_batch",
        "payload": log_entries,
        "count": len(log_entries),
    }
    await ws_manager.broadcast(tenant_id, message)
    return ws_manager.get_connected_count(tenant_id)
