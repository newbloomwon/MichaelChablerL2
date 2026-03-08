"""Sources API for listing available log sources."""
import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db_conn
from app.models.api import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=APIResponse)
async def list_sources(conn=Depends(get_db_conn)) -> APIResponse:
    """
    List all distinct log sources with metadata for the current tenant.

    Returns each source with:
    - source: Source name/path
    - log_count: Number of logs ingested from this source
    - last_seen: ISO timestamp of the most recent log from this source

    Sources are ordered by log_count descending (busiest sources first).
    """
    try:
        tenant_id = getattr(conn, "tenant_id", None)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context missing"
            )

        rows = await conn.fetch(
            """
            SELECT
                source,
                COUNT(*) AS log_count,
                MAX(timestamp) AS last_seen
            FROM log_entries
            WHERE tenant_id = $1
            GROUP BY source
            ORDER BY log_count DESC
            """,
            tenant_id
        )

        sources: List[Dict[str, Any]] = []
        for idx, row in enumerate(rows):
            last_seen = row["last_seen"]
            # Normalise to ISO string regardless of whether the DB returns a
            # datetime object or a numeric Unix timestamp.
            if isinstance(last_seen, datetime):
                last_seen_dt = last_seen
                last_seen_str = last_seen.isoformat()
            elif last_seen is not None:
                try:
                    last_seen_dt = datetime.utcfromtimestamp(float(last_seen))
                    last_seen_str = last_seen_dt.isoformat()
                except (ValueError, TypeError):
                    last_seen_dt = None
                    last_seen_str = str(last_seen)
            else:
                last_seen_dt = None
                last_seen_str = None

            # Determine status: active if last log was within 24 hours
            if last_seen_dt:
                age_hours = (datetime.utcnow() - last_seen_dt.replace(tzinfo=None)).total_seconds() / 3600
                source_status = "active" if age_hours < 24 else "inactive"
            else:
                source_status = "inactive"

            # Infer format from source path
            source_name = row["source"]
            source_format = "nginx" if "nginx" in source_name.lower() else "json"

            sources.append({
                "id": str(idx + 1),
                "name": source_name,
                "log_count": row["log_count"],
                "last_log_at": last_seen_str,
                "last_seen": last_seen_str,
                "status": source_status,
                "format": source_format,
            })

        return APIResponse(
            success=True,
            data=sources,
            timestamp=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sources list error: {e}")
        return APIResponse(
            success=False,
            error={"code": "SOURCES_ERROR", "message": str(e)},
            timestamp=datetime.utcnow()
        )
