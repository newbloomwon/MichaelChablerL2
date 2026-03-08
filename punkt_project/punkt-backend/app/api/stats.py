"""Stats API for dashboard metrics."""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db_conn
from app.models.api import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview", response_model=APIResponse)
async def get_stats_overview(conn=Depends(get_db_conn)):
    """
    Get aggregated stats overview for the tenant.

    Returns total logs, error/warning/info counts, and sources count.
    """
    try:
        tenant_id = getattr(conn, "tenant_id", None)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context missing"
            )

        # Execute optimized stats query with CASE statements
        stats_query = """
        SELECT
            COUNT(*) as total_logs,
            COUNT(CASE WHEN level = 'ERROR' THEN 1 END) as error_count,
            COUNT(CASE WHEN level = 'WARNING' OR level = 'WARN' THEN 1 END) as warning_count,
            COUNT(CASE WHEN level = 'INFO' THEN 1 END) as info_count,
            COUNT(DISTINCT source) as sources_count
        FROM log_entries
        WHERE tenant_id = $1
        """

        row = await conn.fetchrow(stats_query, tenant_id)

        # Calculate rates and trends (mock for now - will be real in Day 5)
        total_logs = row["total_logs"] or 0
        error_count = row["error_count"] or 0

        # Calculate error rate
        error_rate = f"{(error_count / total_logs * 100):.2f}%" if total_logs > 0 else "0%"

        # Ingestion rate (mock - would need time-series data)
        ingestion_rate = "~1.2k/min"

        return APIResponse(
            success=True,
            data={
                "total_logs": total_logs,
                "error_count": error_count,
                "warning_count": row["warning_count"] or 0,
                "info_count": row["info_count"] or 0,
                "active_sources": row["sources_count"] or 0,
                "error_rate": error_rate,
                "ingestion_rate": ingestion_rate,
                "trends": {
                    "total_logs": {"value": "+12%", "positive": True},
                    "ingestion_rate": {"value": "+5%", "positive": True},
                    "error_rate": {"value": "-3%", "positive": True},
                    "active_sources": {"value": "+2", "positive": True}
                }
            },
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Stats overview error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stats: {str(e)}"
        )
