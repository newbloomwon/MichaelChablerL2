"""Search API for querying logs."""
import json
import logging
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.database import get_db_conn
from app.core.redis import redis_manager
from app.models.api import APIResponse
from app.models.search import SearchRequest, SearchResponse, LogEntry
from app.query import parse_query, execute_query, QueryParseError, QueryExecutionError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=APIResponse)
async def search_wrapper(
    q: str = "",
    time_range: str = "15m",
    limit: int = 100,
    offset: int = 0,
    conn=Depends(get_db_conn)
):
    """
    GET wrapper for search endpoint (frontend compatibility).

    Accepts query string and time range, converts to query parser format.
    Returns results, stats, and time_series data for frontend visualization.
    """
    try:
        tenant_id = getattr(conn, "tenant_id", None)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context missing"
            )

        # Edge Case 1: empty query string — return the 100 most recent logs
        if not q or not q.strip():
            db_rows = await conn.fetch(
                "SELECT id, timestamp, level, source, message, metadata, raw_log "
                "FROM log_entries WHERE tenant_id = $1 "
                "ORDER BY timestamp DESC LIMIT $2",
                tenant_id, limit
            )
            rows = [
                {
                    "id": str(row["id"]),
                    "timestamp": row["timestamp"],
                    "level": row["level"],
                    "source": row["source"],
                    "message": row["message"],
                    "metadata": row["metadata"],
                    "raw_log": row["raw_log"]
                }
                for row in db_rows
            ]

            # Aggregate top sources for the chart
            source_rows = await conn.fetch(
                "SELECT source, COUNT(*) as count FROM log_entries "
                "WHERE tenant_id = $1 GROUP BY source ORDER BY count DESC LIMIT 10",
                tenant_id
            )
            aggregations = [dict(row) for row in source_rows]

            # Generate time series (count by level per hour for last 24h)
            # Note: timestamp is stored as epoch int, so we use to_timestamp()
            ts_rows = await conn.fetch(
                "SELECT date_trunc('hour', to_timestamp(timestamp)) as bucket, "
                "level, COUNT(*) as count FROM log_entries "
                "WHERE tenant_id = $1 "
                "AND timestamp > extract(epoch from now() - interval '24 hours') "
                "GROUP BY bucket, level ORDER BY bucket",
                tenant_id
            )
            # Pivot into {timestamp, INFO, WARN, ERROR, DEBUG, CRITICAL}
            time_series = _pivot_time_series(ts_rows)

            return APIResponse(
                success=True,
                data={
                    "rows": rows,          # consistent key matching QueryResult schema
                    "aggregations": aggregations,
                    "time_series": time_series,
                    "total_count": len(rows)
                },
                timestamp=datetime.utcnow()
            )

        # Parse and execute query
        try:
            parsed = parse_query(q)
        except QueryParseError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Query parse error: {e.message}"
            )

        try:
            result = await execute_query(
                parsed=parsed,
                tenant_id=tenant_id,
                conn=conn,
                limit=limit,
                offset=offset
            )
        except QueryExecutionError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query execution error: {e.message}"
            )

        # Format response — use "rows" to match QueryResult schema (resolves I-08)
        return APIResponse(
            success=True,
            data={
                "rows": result.rows,
                "aggregations": result.aggregations,
                "time_series": [],
                "total_count": result.total_count,
                "execution_time_ms": result.execution_time_ms
            },
            timestamp=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search wrapper error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/logs", response_model=APIResponse)
async def search_logs(
    request: SearchRequest,
    conn=Depends(get_db_conn)
):
    """Search logs with various filters."""
    try:
        tenant_id = getattr(conn, "tenant_id", None)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context missing"
            )

        start_time = time.time()

        # Build query
        where_clauses = ["tenant_id = $1"]
        params = [tenant_id]
        param_index = 2

        if request.query:
            where_clauses.append(f"(message ILIKE ${param_index} OR raw_log ILIKE ${param_index})")
            params.append(f"%{request.query}%")
            param_index += 1

        if request.source:
            where_clauses.append(f"source = ${param_index}")
            params.append(request.source)
            param_index += 1

        if request.level:
            where_clauses.append(f"level = ${param_index}")
            params.append(request.level.upper())
            param_index += 1

        if request.start_time:
            where_clauses.append(f"timestamp >= ${param_index}")
            params.append(int(request.start_time.timestamp()))
            param_index += 1

        if request.end_time:
            where_clauses.append(f"timestamp <= ${param_index}")
            params.append(int(request.end_time.timestamp()))
            param_index += 1

        where_clause = " AND ".join(where_clauses)

        # Get total count
        count_query = f"SELECT COUNT(*) FROM log_entries WHERE {where_clause}"
        count_result = await conn.fetchval(count_query, *params)
        total_count = count_result or 0

        # Get results
        query = f"""
            SELECT id, timestamp, level, source, message, metadata, raw_log
            FROM log_entries
            WHERE {where_clause}
            ORDER BY {request.sort_by} {request.sort_order.upper()}
            LIMIT ${param_index} OFFSET ${param_index + 1}
        """
        params.append(request.limit)
        params.append(request.offset)

        rows = await conn.fetch(query, *params)

        results = [
            LogEntry(
                id=str(row["id"]),
                timestamp=row["timestamp"],
                level=row["level"],
                source=row["source"],
                message=row["message"],
                metadata=row["metadata"],
                raw_log=row["raw_log"]
            )
            for row in rows
        ]

        execution_time = (time.time() - start_time) * 1000

        return APIResponse(
            success=True,
            data=SearchResponse(
                total_count=total_count,
                returned_count=len(results),
                offset=request.offset,
                limit=request.limit,
                results=results,
                execution_time_ms=execution_time
            ),
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        return APIResponse(
            success=False,
            error={"code": "SEARCH_ERROR", "message": str(e)},
            timestamp=datetime.utcnow()
        )


@router.get("/recent")
async def get_recent_logs(
    limit: int = 100,
    conn=Depends(get_db_conn)
):
    """Get recent logs from cache."""
    try:
        tenant_id = getattr(conn, "tenant_id", None)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context missing"
            )

        # Try to get from Redis cache first
        if redis_manager.client:
            logs_json = await redis_manager.get_recent_logs(tenant_id, limit)
            results = [
                LogEntry(
                    timestamp=log.get("timestamp"),
                    level=log.get("level"),
                    source=log.get("source"),
                    message=log.get("message"),
                    metadata=log.get("metadata"),
                    raw_log=log.get("raw_log")
                )
                for log in logs_json
            ]
        else:
            # Fall back to database query
            rows = await conn.fetch(
                "SELECT id, timestamp, level, source, message, metadata, raw_log "
                "FROM log_entries WHERE tenant_id = $1 "
                "ORDER BY timestamp DESC LIMIT $2",
                tenant_id, limit
            )
            results = [
                LogEntry(
                    id=str(row["id"]),
                    timestamp=row["timestamp"],
                    level=row["level"],
                    source=row["source"],
                    message=row["message"],
                    metadata=row["metadata"],
                    raw_log=row["raw_log"]
                )
                for row in rows
            ]

        return APIResponse(
            success=True,
            data={
                "count": len(results),
                "logs": results
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Recent logs error: {e}")
        return APIResponse(
            success=False,
            error={"code": "RECENT_LOGS_ERROR", "message": str(e)},
            timestamp=datetime.utcnow()
        )


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str


@router.post("/query", response_model=APIResponse)
async def query_logs(
    request: QueryRequest,
    limit: int = 100,
    offset: int = 0,
    conn=Depends(get_db_conn)
):
    """
    Execute a parsed query string against log entries.

    Supports field filters (level=ERROR), text search, and pipe commands.
    Example: "level=ERROR source=nginx | stats count by source | head 50"
    """
    try:
        tenant_id = getattr(conn, "tenant_id", None)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context missing"
            )

        # Parse the query string
        try:
            parsed = parse_query(request.query)
        except QueryParseError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Query parse error: {e.message}"
            )

        # Execute the parsed query
        try:
            result = await execute_query(
                parsed=parsed,
                tenant_id=tenant_id,
                conn=conn,
                limit=limit,
                offset=offset
            )
        except QueryExecutionError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query execution error: {e.message}"
            )

        # Format response
        return APIResponse(
            success=True,
            data={
                "rows": result.rows,
                "aggregations": result.aggregations,
                "total_count": result.total_count,
                "execution_time_ms": result.execution_time_ms
            },
            timestamp=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected query error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

def _pivot_time_series(rows):
    """
    Pivot time-series rows into {timestamp, INFO, WARN, ERROR, DEBUG, CRITICAL} format.
    
    Input: [{bucket: datetime, level: str, count: int}, ...]
    Output: [{timestamp: str, INFO: int, WARN: int, ERROR: int, DEBUG: int, CRITICAL: int}, ...]
    """
    from collections import defaultdict
    
    # Group by bucket
    buckets = defaultdict(lambda: {"INFO": 0, "WARN": 0, "ERROR": 0, "DEBUG": 0, "CRITICAL": 0})
    for row in rows:
        bucket_ts = row["bucket"].isoformat() if row["bucket"] else ""
        level = row["level"]
        count = row["count"]
        buckets[bucket_ts][level] = count
    
    # Convert to list format
    result = []
    for timestamp, levels in sorted(buckets.items()):
        result.append({
            "timestamp": timestamp,
            **levels
        })
    
    return result
