"""
Seed test users required by test_api.py integration tests.

Usage:
    python -m scripts.seed_test_users

Requires DATABASE_URL environment variable or .env file.
"""
import asyncio
import sys
import uuid

import asyncpg

from app.config import settings
from app.core.auth import get_password_hash

TEST_USERS = [
    {"username": "test_user_a", "password": "testpass123", "tenant_id": "tenant_a"},
    {"username": "test_user_b", "password": "testpass123", "tenant_id": "tenant_b"},
]


async def seed():
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        for user in TEST_USERS:
            existing = await conn.fetchval(
                "SELECT id FROM users WHERE username = $1", user["username"]
            )
            if existing:
                print(f"  skip  {user['username']} (already exists)")
                continue

            user_id = str(uuid.uuid4())
            password_hash = get_password_hash(user["password"])
            await conn.execute(
                "INSERT INTO users (id, username, password_hash, tenant_id) VALUES ($1, $2, $3, $4)",
                user_id, user["username"], password_hash, user["tenant_id"],
            )
            print(f"  created {user['username']} (tenant: {user['tenant_id']})")
    finally:
        await conn.close()


if __name__ == "__main__":
    print("Seeding test users...")
    asyncio.run(seed())
    print("Done.")
