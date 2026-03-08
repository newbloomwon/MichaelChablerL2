from fastapi import Request
import asyncpg
from app.config import settings
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(
                    settings.DATABASE_URL,
                    min_size=5,
                    max_size=20
                )
                logger.info("Connected to PostgreSQL pool")
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
                raise

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from PostgreSQL pool")

    async def get_connection(self):
        if not self.pool:
            await self.connect()
        return self.pool.acquire()

db = DatabaseManager()

class ConnectionWithContext:
    """Wrapper for asyncpg connection with tenant context."""
    def __init__(self, conn, tenant_id: Optional[str] = None):
        self._conn = conn
        self.tenant_id = tenant_id

    def __getattr__(self, name):
        return getattr(self._conn, name)

async def get_db_conn(request: Request):
    tenant_id = getattr(request.state, "tenant_id", None)
    async with db.pool.acquire() as conn:
        if tenant_id:
            await conn.execute(f"SET app.current_tenant = '{tenant_id}'")
        # Wrap the connection with tenant context
        yield ConnectionWithContext(conn, tenant_id)
