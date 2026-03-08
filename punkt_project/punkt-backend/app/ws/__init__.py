"""WebSocket module for real-time log streaming."""
from .manager import ClientState, WebSocketManager, ws_manager
from .broadcaster import broadcast_batch, broadcast_log

__all__ = [
    "WebSocketManager",
    "ws_manager",
    "ClientState",
    "broadcast_log",
    "broadcast_batch",
]
