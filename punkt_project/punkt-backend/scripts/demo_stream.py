#!/usr/bin/env python3
"""
Demo ingestion script for Punkt Live Feed.

Continuously streams synthetic logs to the backend via /api/ingest/json,
allowing the Live Feed to show logs in real time during demos.

Usage:
    cd punkt-backend
    python -m scripts.demo_stream

The script will prompt for confirmation once connected, then stream
batches of logs every 2 seconds. Press Ctrl+C to stop.
"""
import json
import random
import time
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

BASE_URL = "http://localhost:8000"
USERNAME = "demo@acme.com"
PASSWORD = "demo123"

# Reuse constants from generate_test_data.py
SOURCES = [
    "/var/log/nginx/access.log",
    "/var/log/app/api.log",
    "/var/log/app/worker.log",
    "/var/log/auth.log",
]

LEVELS = ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]
LEVEL_WEIGHTS = [10, 60, 20, 8, 2]

MESSAGES = {
    "DEBUG": ["Cache hit for key", "Query executed in {ms}ms", "Request payload: {size} bytes"],
    "INFO": ["User logged in", "Request completed", "Background job finished", "File uploaded"],
    "WARN": ["Slow query detected", "Rate limit approaching", "Disk usage at 80%"],
    "ERROR": ["Connection timeout", "Database error", "Invalid request format"],
    "CRITICAL": ["Out of memory", "Database connection lost", "Service unavailable"],
}


def login() -> Optional[str]:
    """Login and return access_token, or None on failure."""
    try:
        with httpx.Client() as client:
            resp = client.post(
                f"{BASE_URL}/api/auth/login",
                json={"username": USERNAME, "password": PASSWORD},
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    return data["data"]["access_token"]
            print(f"Login failed: {resp.status_code} {resp.text}")
            return None
    except httpx.RequestError as e:
        print(f"Login error: {e}")
        return None


def make_batch(size: int) -> List[Dict[str, Any]]:
    """Generate a batch of random logs with current timestamps."""
    logs = []
    for _ in range(size):
        level = random.choices(LEVELS, weights=LEVEL_WEIGHTS)[0]
        message = random.choice(MESSAGES[level]).format(
            ms=random.randint(10, 5000),
            size=random.randint(100, 10000)
        )
        log = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "source": random.choice(SOURCES),
            "message": message,
            "metadata": {
                "host": f"server-{random.randint(1, 5):02d}",
                "request_id": f"req-{random.randint(10000, 99999)}",
                "user_id": f"user-{random.randint(1, 100)}" if random.random() > 0.3 else None
            }
        }
        logs.append(log)
    return logs


def stream(token: str) -> None:
    """Stream logs to the backend every 2 seconds."""
    headers = {"Authorization": f"Bearer {token}"}
    count = 0

    print(f"\n✓ Connected. Streaming logs every 2 seconds. Press Ctrl+C to stop.\n")

    try:
        with httpx.Client() as client:
            while True:
                # Generate 3–8 logs per batch
                batch_size = random.randint(3, 8)
                logs = make_batch(batch_size)

                # Count by level for summary
                level_counts = {}
                for log in logs:
                    level = log["level"]
                    level_counts[level] = level_counts.get(level, 0) + 1

                # POST to backend
                try:
                    resp = client.post(
                        f"{BASE_URL}/api/ingest/json",
                        json={"logs": logs},
                        headers=headers,
                        timeout=5
                    )
                    if resp.status_code != 200:
                        print(f"Warning: ingest returned {resp.status_code}")
                except httpx.RequestError as e:
                    print(f"Error posting logs: {e}")
                    break

                # Print summary
                count += batch_size
                level_str = " ".join(f"{level}×{level_counts[level]}" for level in LEVELS if level in level_counts)
                print(f"[+{batch_size} logs] {level_str} (total: {count})")

                time.sleep(2)

    except KeyboardInterrupt:
        print(f"\n\n✓ Stream stopped. ({count} logs sent)")


if __name__ == "__main__":
    print("Punkt Demo Log Stream")
    print(f"Target: {BASE_URL}")
    print(f"User: {USERNAME}\n")

    token = login()
    if not token:
        print("Failed to authenticate. Make sure the backend is running at {BASE_URL}")
        sys.exit(1)

    print(f"✓ Logged in as {USERNAME}")

    stream(token)
