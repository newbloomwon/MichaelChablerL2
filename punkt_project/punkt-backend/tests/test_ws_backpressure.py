"""Tests for WebSocket backpressure handling."""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ws.manager import (
    MAX_CONSECUTIVE_DROPS,
    MAX_QUEUE_SIZE,
    QUEUE_WARNING_THRESHOLD,
    WebSocketManager,
)


def _make_mock_ws():
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.mark.asyncio
async def test_connect_creates_client_state():
    """connect() should register ClientState with a bounded queue."""
    manager = WebSocketManager()
    ws = _make_mock_ws()

    result = await manager.connect(ws, "t1", "u1")

    assert result is True
    assert "t1" in manager.clients
    assert "u1" in manager.clients["t1"]
    client = manager.clients["t1"]["u1"]
    assert client.queue.maxsize == MAX_QUEUE_SIZE
    assert client.sender_task is not None
    assert client.heartbeat_task is not None

    # Cleanup
    client.sender_task.cancel()
    client.heartbeat_task.cancel()


@pytest.mark.asyncio
async def test_broadcast_queues_message():
    """broadcast() should enqueue messages for connected clients."""
    manager = WebSocketManager()
    ws = _make_mock_ws()
    await manager.connect(ws, "t1", "u1")

    client = manager.clients["t1"]["u1"]
    # Drain the initial "subscribed" confirmation
    while not client.queue.empty():
        client.queue.get_nowait()
        client.queue.task_done()

    await manager.broadcast("t1", {"type": "log", "data": {"msg": "hello"}})

    assert client.queue.qsize() == 1
    msg = client.queue.get_nowait()
    assert msg == {"type": "log", "data": {"msg": "hello"}}

    client.sender_task.cancel()
    client.heartbeat_task.cancel()


@pytest.mark.asyncio
async def test_broadcast_no_op_for_unknown_tenant():
    """broadcast() for a tenant with no connections should be a no-op."""
    manager = WebSocketManager()
    # Should not raise
    await manager.broadcast("unknown_tenant", {"type": "log", "data": {}})


@pytest.mark.asyncio
async def test_backpressure_drops_oldest_on_full_queue():
    """When the queue is full, the oldest message is dropped and dropped_count increments."""
    manager = WebSocketManager()
    ws = _make_mock_ws()
    await manager.connect(ws, "t1", "u1")

    client = manager.clients["t1"]["u1"]
    # Fill queue to capacity with sentinel messages
    while not client.queue.full():
        client.queue.put_nowait({"type": "old", "seq": client.queue.qsize()})

    assert client.queue.full()
    assert client.dropped_count == 0

    # Trigger backpressure
    await manager.broadcast("t1", {"type": "new_msg"})

    assert client.dropped_count == 1
    assert client.consecutive_drops == 1

    client.sender_task.cancel()
    client.heartbeat_task.cancel()


@pytest.mark.asyncio
async def test_backpressure_queues_slow_client_warning():
    """A SLOW_CLIENT warning should be queued when a message is dropped."""
    manager = WebSocketManager()
    ws = _make_mock_ws()
    await manager.connect(ws, "t1", "u1")

    client = manager.clients["t1"]["u1"]
    while not client.queue.full():
        client.queue.put_nowait({"type": "filler"})

    await manager.broadcast("t1", {"type": "new_msg"})

    # Drain the queue and look for a warning
    messages = []
    while not client.queue.empty():
        messages.append(client.queue.get_nowait())

    warning_types = [m.get("code") for m in messages]
    assert "SLOW_CLIENT" in warning_types

    client.sender_task.cancel()
    client.heartbeat_task.cancel()


@pytest.mark.asyncio
async def test_slow_client_disconnected_after_max_consecutive_drops():
    """Client should be disconnected after MAX_CONSECUTIVE_DROPS consecutive drops."""
    manager = WebSocketManager()
    ws = _make_mock_ws()
    await manager.connect(ws, "t1", "u1")

    client = manager.clients["t1"]["u1"]

    # Simulate MAX_CONSECUTIVE_DROPS - 1 already counted
    client.consecutive_drops = MAX_CONSECUTIVE_DROPS - 1

    # Fill queue so next broadcast triggers a drop
    while not client.queue.full():
        client.queue.put_nowait({"type": "filler"})

    await manager.broadcast("t1", {"type": "log", "data": {}})

    # Client should have been disconnected
    ws.close.assert_called_once()
    assert "t1" not in manager.clients or "u1" not in manager.clients.get("t1", {})


@pytest.mark.asyncio
async def test_disconnect_cleans_up_tasks_and_state():
    """disconnect() should cancel tasks and remove client from tracking."""
    manager = WebSocketManager()
    ws = _make_mock_ws()
    await manager.connect(ws, "t1", "u1")

    assert "u1" in manager.clients.get("t1", {})

    await manager.disconnect(ws, "t1")

    assert "t1" not in manager.clients


@pytest.mark.asyncio
async def test_get_client_stats_returns_metrics():
    """get_client_stats() should return per-client backpressure info."""
    manager = WebSocketManager()
    ws = _make_mock_ws()
    await manager.connect(ws, "t1", "u1")

    client = manager.clients["t1"]["u1"]
    client.dropped_count = 5

    stats = manager.get_client_stats("t1")

    assert len(stats) == 1
    assert stats[0]["user_id"] == "u1"
    assert stats[0]["dropped_count"] == 5
    assert "queue_size" in stats[0]

    client.sender_task.cancel()
    client.heartbeat_task.cancel()


@pytest.mark.asyncio
async def test_handle_client_message_pong_updates_state():
    """Pong message should set pong_received = True on the client."""
    manager = WebSocketManager()
    ws = _make_mock_ws()
    await manager.connect(ws, "t1", "u1")

    client = manager.clients["t1"]["u1"]
    client.pong_received = False

    await manager.handle_client_message(ws, "t1", {"type": "pong"})

    assert client.pong_received is True

    client.sender_task.cancel()
    client.heartbeat_task.cancel()


@pytest.mark.asyncio
async def test_handle_client_message_reconnect_ack():
    """Reconnect message should queue a reconnect_ack response."""
    manager = WebSocketManager()
    ws = _make_mock_ws()
    await manager.connect(ws, "t1", "u1")

    client = manager.clients["t1"]["u1"]
    # Drain the initial subscribed confirmation
    while not client.queue.empty():
        client.queue.get_nowait()
        client.queue.task_done()

    await manager.handle_client_message(ws, "t1", {"type": "reconnect", "last_seen_id": "abc123"})

    assert client.last_seen_id == "abc123"
    msg = client.queue.get_nowait()
    assert msg["type"] == "reconnect_ack"
    assert msg["last_seen_id"] == "abc123"

    client.sender_task.cancel()
    client.heartbeat_task.cancel()
