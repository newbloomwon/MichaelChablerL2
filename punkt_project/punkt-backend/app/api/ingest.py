import logging
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.database import get_db_conn
from app.models.api import APIResponse
from app.ws.broadcaster import broadcast_log

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])

class LogInput(BaseModel):
    timestamp: datetime
    level: str = Field(..., pattern="^(DEBUG|INFO|WARN|ERROR|CRITICAL)$")
    source: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

class BatchLogInput(BaseModel):
    logs: List[LogInput]

@router.post("/json")
async def ingest_json(
    batch: BatchLogInput,
    conn = Depends(get_db_conn)
):
    try:
        tenant_id = getattr(conn, "tenant_id", None)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context missing"
            )

        # Prepare records for bulk insert
        records = [
            (
                log.timestamp,
                tenant_id,
                log.source,
                log.level,
                log.message,
                json.dumps(log.metadata) if log.metadata else None,
                log.message # raw_log (storing message as raw log for simple JSON ingest)
            )
            for log in batch.logs
        ]

        # Use executemany for high performance bulk insert
        await conn.executemany(
            """
            INSERT INTO log_entries (timestamp, tenant_id, source, level, message, metadata, raw_log)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            records
        )

        # Broadcast to connected WebSocket clients (non-fatal)
        try:
            for log in batch.logs:
                await broadcast_log(tenant_id, {
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level,
                    "source": log.source,
                    "message": log.message,
                    "metadata": log.metadata or {},
                })
        except Exception as ws_err:
            logger.warning(f"Failed to broadcast logs to WebSocket: {ws_err}")

        return APIResponse(
            success=True,
            data={
                "accepted": len(batch.logs),
                "rejected": 0,
                "errors": []
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "INGESTION_ERROR",
                "message": str(e)
            },
            timestamp=datetime.utcnow()
        )
