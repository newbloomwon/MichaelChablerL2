"""WebSocket connection manager for real-time log streaming."""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from fastapi import WebSocket, status

logger = logging.getLogger(__name__)

# Backpressure configuration
MAX_QUEUE_SIZE = 100           # Maximum pending messages per client
QUEUE_WARNING_THRESHOLD = 80  # Log warning when queue reaches this size
MAX_CONSECUTIVE_DROPS = 10    # Disconnect after this many consecutive drops


class WebSocketError(Exception):
    """Base WebSocket connection error."""
    pass


class WebSocketAuthError(WebSocketError):
    """JWT validation failed."""
    pass


@dataclass
class ClientState:
    """Tracks state for a single WebSocket client."""
    websocket: WebSocket
    tenant_id: str
    user_id: str
    queue: asyncio.Queue
    sender_task: Optional[asyncio.Task] = None
    heartbeat_task: Optional[asyncio.Task] = None
    pong_received: bool = True
    last_seen_id: Optional[str] = None
    dropped_count: int = 0
    consecutive_drops: int = 0
    connected_at: float = field(default_factory=time.time)
    filters: dict = field(default_factory=dict)


class WebSocketManager:
    """Manages WebSocket connections for real-time log streaming."""

    def __init__(self):
        """Initialize the WebSocket manager."""
        # Structure: {tenant_id: {user_id: ClientState}}
        self.clients: Dict[str, Dict[str, ClientState]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        tenant_id: str,
        user_id: str
    ) -> bool:
        """
        Accept and register a WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            tenant_id: Tenant ID from URL path
            user_id: User ID extracted from JWT

        Returns:
            True if connected successfully, False if auth failed
        """
        try:
            # If user already connected, disconnect their old session first
            if tenant_id in self.clients and user_id in self.clients[tenant_id]:
                logger.info(f"Replacing existing connection: tenant={tenant_id}, user={user_id}")
                old_client = self.clients[tenant_id][user_id]
                await self.disconnect(old_client.websocket, tenant_id)

            # Accept the WebSocket connection
            await websocket.accept()

            # Create bounded queue for this client
            queue: asyncio.Queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)

            # Create client state
            client = ClientState(
                websocket=websocket,
                tenant_id=tenant_id,
                user_id=user_id,
                queue=queue,
            )

            # Register connection
            if tenant_id not in self.clients:
                self.clients[tenant_id] = {}
            self.clients[tenant_id][user_id] = client

            # Start sender loop (drains queue → websocket)
            client.sender_task = asyncio.create_task(
                self._sender_loop(client)
            )

            # Start heartbeat task
            client.heartbeat_task = asyncio.create_task(
                self._send_heartbeat(client)
            )

            # Queue subscription confirmation
            await queue.put({
                "type": "subscribed",
                "filters": {}
            })

            logger.info(f"WebSocket connected: tenant={tenant_id}, user={user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            return False

    async def disconnect(self, websocket: WebSocket, tenant_id: str):
        """
        Remove connection from tracking and clean up resources.

        Args:
            websocket: WebSocket instance to disconnect
            tenant_id: Tenant ID
        """
        client: Optional[ClientState] = None
        user_id: Optional[str] = None

        # Find the ClientState matching this websocket
        if tenant_id in self.clients:
            for uid, c in list(self.clients[tenant_id].items()):
                if c.websocket is websocket:
                    client = c
                    user_id = uid
                    break

        if client is None:
            return

        # Cancel sender and heartbeat tasks
        for task in (client.sender_task, client.heartbeat_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Remove from tracking
        if tenant_id in self.clients and user_id in self.clients[tenant_id]:
            del self.clients[tenant_id][user_id]
            logger.info(
                f"WebSocket disconnected: tenant={tenant_id}, user={user_id}, "
                f"total_dropped={client.dropped_count}"
            )

        # Clean up empty tenant dict
        if tenant_id in self.clients and not self.clients[tenant_id]:
            del self.clients[tenant_id]

    async def _sender_loop(self, client: ClientState):
        """
        Coroutine that drains the client's message queue to the WebSocket.

        Runs continuously until cancelled or the WebSocket closes.
        """
        try:
            while True:
                message = await client.queue.get()
                try:
                    await client.websocket.send_json(message)
                    client.consecutive_drops = 0
                except Exception as e:
                    logger.warning(
                        f"Send failed for tenant={client.tenant_id}, "
                        f"user={client.user_id}: {e}"
                    )
                    break
                finally:
                    client.queue.task_done()
        except asyncio.CancelledError:
            logger.debug(
                f"Sender loop cancelled: tenant={client.tenant_id}, user={client.user_id}"
            )
        except Exception as e:
            logger.error(
                f"Sender loop error: tenant={client.tenant_id}, "
                f"user={client.user_id}: {e}"
            )

    async def broadcast(self, tenant_id: str, message: dict):
        """
        Send message to all connected clients for a tenant.

        Uses non-blocking queue puts with backpressure handling:
        - Queue not full: message is enqueued for the sender loop
        - Queue 80%+ full: warning is logged
        - Queue full: oldest message dropped, SLOW_CLIENT warning sent to client
        - 10+ consecutive drops: client disconnected with code 4002

        Args:
            tenant_id: Tenant ID to broadcast to
            message: Dict with 'type' and payload
        """
        if tenant_id not in self.clients:
            return

        clients_to_disconnect: List[tuple] = []

        for user_id, client in list(self.clients.get(tenant_id, {}).items()):
            try:
                queue_size = client.queue.qsize()

                if QUEUE_WARNING_THRESHOLD <= queue_size < MAX_QUEUE_SIZE:
                    logger.warning(
                        f"Client queue filling: tenant={tenant_id}, user={user_id}, "
                        f"size={queue_size}/{MAX_QUEUE_SIZE}"
                    )

                try:
                    client.queue.put_nowait(message)
                except asyncio.QueueFull:
                    client.dropped_count += 1
                    client.consecutive_drops += 1

                    logger.warning(
                        f"Dropping message for slow client: tenant={tenant_id}, "
                        f"user={user_id}, dropped={client.dropped_count}, "
                        f"consecutive={client.consecutive_drops}"
                    )

                    if client.consecutive_drops >= MAX_CONSECUTIVE_DROPS:
                        logger.error(
                            f"Disconnecting slow client after {MAX_CONSECUTIVE_DROPS} "
                            f"consecutive drops: tenant={tenant_id}, user={user_id}"
                        )
                        clients_to_disconnect.append((tenant_id, user_id, client))
                        continue

                    # Drop the oldest message to make room
                    try:
                        client.queue.get_nowait()
                        client.queue.task_done()
                    except asyncio.QueueEmpty:
                        pass

                    # Notify client about the drop
                    warning_msg = {
                        "type": "warning",
                        "code": "SLOW_CLIENT",
                        "message": "Messages being dropped due to slow connection",
                        "dropped_count": client.dropped_count,
                    }
                    try:
                        client.queue.put_nowait(warning_msg)
                    except asyncio.QueueFull:
                        pass

                    # Retry queuing the original message
                    try:
                        client.queue.put_nowait(message)
                    except asyncio.QueueFull:
                        pass

            except Exception as e:
                logger.error(
                    f"Broadcast error for tenant={tenant_id}, user={user_id}: {e}"
                )
                clients_to_disconnect.append((tenant_id, user_id, client))

        for tid, uid, client in clients_to_disconnect:
            try:
                await client.websocket.close(code=4002, reason="Slow client disconnected")
            except Exception:
                pass
            await self.disconnect(client.websocket, tid)

    async def handle_client_message(
        self,
        websocket: WebSocket,
        tenant_id: str,
        message: dict
    ):
        """
        Handle incoming client messages (pong, subscribe, reconnect).

        Args:
            websocket: WebSocket instance
            tenant_id: Tenant ID
            message: Client message dict
        """
        # Resolve ClientState from websocket
        client: Optional[ClientState] = None
        if tenant_id in self.clients:
            for c in self.clients[tenant_id].values():
                if c.websocket is websocket:
                    client = c
                    break

        msg_type = message.get("type")

        if msg_type == "pong":
            if client:
                client.pong_received = True
            logger.debug(f"Pong received: tenant={tenant_id}")

        elif msg_type == "subscribe":
            filters = message.get("filters", {})
            if client:
                client.filters = filters
            logger.debug(f"Client subscribed with filters: {filters}")
            # Send confirmation via queue so it goes through the sender loop
            if client:
                try:
                    client.queue.put_nowait({
                        "type": "subscribed",
                        "filters": filters
                    })
                except asyncio.QueueFull:
                    pass

        elif msg_type == "reconnect":
            last_seen_id = message.get("last_seen_id")
            if client:
                client.last_seen_id = last_seen_id
            logger.info(
                f"Client reconnecting: tenant={tenant_id}, last_seen_id={last_seen_id}"
            )
            if client:
                try:
                    client.queue.put_nowait({
                        "type": "reconnect_ack",
                        "last_seen_id": last_seen_id,
                        "missed_count": 0,
                    })
                except asyncio.QueueFull:
                    pass

        else:
            logger.warning(f"Unknown message type: {msg_type}")

    def get_connected_count(self, tenant_id: str) -> int:
        """Return number of connected clients for a tenant."""
        return len(self.clients.get(tenant_id, {}))

    def get_client_stats(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get backpressure statistics for all clients of a tenant.

        Returns:
            List of dicts with user_id, queue_size, dropped_count, connected_at, filters
        """
        stats = []
        for user_id, client in self.clients.get(tenant_id, {}).items():
            stats.append({
                "user_id": user_id,
                "queue_size": client.queue.qsize(),
                "dropped_count": client.dropped_count,
                "consecutive_drops": client.consecutive_drops,
                "connected_at": client.connected_at,
                "filters": client.filters,
            })
        return stats

    async def _send_heartbeat(self, client: ClientState):
        """
        Send ping every 30 seconds; disconnect if pong not received within 10 seconds.

        Args:
            client: ClientState for the connected client
        """
        while True:
            try:
                await asyncio.sleep(30)

                # Send ping via queue
                client.pong_received = False
                try:
                    client.queue.put_nowait({
                        "type": "ping",
                        "timestamp": int(time.time())
                    })
                except asyncio.QueueFull:
                    pass

                # Wait up to 10 seconds for pong
                start = asyncio.get_event_loop().time()
                while not client.pong_received:
                    if asyncio.get_event_loop().time() - start > 10:
                        logger.warning(
                            f"Pong timeout: tenant={client.tenant_id}, "
                            f"user={client.user_id}"
                        )
                        await client.websocket.close(
                            code=status.WS_1000_NORMAL_CLOSURE
                        )
                        return
                    await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                logger.debug(
                    f"Heartbeat cancelled: tenant={client.tenant_id}, "
                    f"user={client.user_id}"
                )
                break
            except Exception as e:
                logger.error(
                    f"Heartbeat error: tenant={client.tenant_id}, "
                    f"user={client.user_id}: {e}"
                )
                break


# Global WebSocket manager instance
ws_manager = WebSocketManager()
