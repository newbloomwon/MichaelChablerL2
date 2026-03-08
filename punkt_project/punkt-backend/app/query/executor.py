"""Query executor for Punkt search functionality.

Executes parsed queries against PostgreSQL and returns results with stats.
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.query.parser import (
    ParsedQuery,
    FilterNode,
    TextSearch,
    StatsCommand,
    HeadCommand,
    SortCommand,
    QueryParseError
)
from app.core.exceptions import QueryTimeoutError
from app.core.redis import redis_manager

logger = logging.getLogger(__name__)


class QueryExecutionError(Exception):
    """Exception raised when query execution fails."""

    def __init__(self, message: str, query: str = ""):
        self.message = message
        self.query = query
        super().__init__(f"{message}\nQuery: {query}")


@dataclass
class QueryResult:
    """Result of query execution."""
    rows: List[Dict[str, Any]]  # Log entries (empty if aggregation)
    aggregations: List[Dict[str, Any]]  # Aggregation results (empty if filter query)
    total_count: int  # Total matching logs (before LIMIT)
    execution_time_ms: float  # Query execution time


async def execute_query(
    parsed: ParsedQuery,
    tenant_id: str,
    conn,
    limit: int = 100,
    offset: int = 0
) -> QueryResult:
    """
    Execute parsed query against PostgreSQL with caching and timeout protection.

    Args:
        parsed: ParsedQuery from parser
        tenant_id: Tenant ID for RLS filtering
        conn: asyncpg connection with .tenant_id attribute
        limit: Max results per page
        offset: Pagination offset

    Returns:
        QueryResult with rows, aggregations, total_count, execution_time_ms

    Raises:
        QueryExecutionError: If query execution fails
        QueryTimeoutError: If execution exceeds 5 seconds
    """
    start_time = time.time()

    try:
        # Generate cache key from query string (only cache when offset=0, limit=100)
        use_cache = (limit == 100 and offset == 0 and not parsed.pipe_commands)
        cache_key = None
        if use_cache:
            query_hash = hashlib.sha256(parsed.query_string.encode()).hexdigest()
            cache_key = f"query:{tenant_id}:{query_hash}"

            # Check cache first
            cached = await redis_manager.get_cached_query(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for query: {cache_key}")
                cached_result = QueryResult(**cached)
                return cached_result

        # Wrap execution with timeout (5 seconds)
        try:
            # Determine if this is a stats query
            is_stats_query = any(isinstance(cmd, StatsCommand) for cmd in parsed.pipe_commands)

            if is_stats_query:
                # Execute aggregation query
                result = await asyncio.wait_for(_execute_stats(parsed, tenant_id, conn), timeout=5.0)
            else:
                # Execute row query with filters
                result = await asyncio.wait_for(_execute_rows(parsed, tenant_id, conn, limit, offset), timeout=5.0)

            # Get total count (before LIMIT)
            total_count = await asyncio.wait_for(_get_total_count(parsed, tenant_id, conn), timeout=5.0)

        except asyncio.TimeoutError:
            raise QueryTimeoutError("Query execution exceeded 5 second limit")

        execution_time = (time.time() - start_time) * 1000

        final_result = QueryResult(
            rows=result.get("rows", []),
            aggregations=result.get("aggregations", []),
            total_count=total_count,
            execution_time_ms=execution_time
        )

        # Cache the result if we generated a cache key
        if use_cache and cache_key:
            try:
                await redis_manager.cache_query_result(
                    cache_key,
                    {
                        "rows": final_result.rows,
                        "aggregations": final_result.aggregations,
                        "total_count": final_result.total_count,
                        "execution_time_ms": final_result.execution_time_ms,
                    },
                    ttl=300
                )
            except Exception as e:
                # Log caching error but don't fail the query
                logger.warning(f"Failed to cache query result: {str(e)}")

        return final_result

    except QueryExecutionError:
        raise
    except Exception as e:
        raise QueryExecutionError(f"Query execution failed: {str(e)}")


async def _execute_rows(
    parsed: ParsedQuery,
    tenant_id: str,
    conn,
    limit: int,
    offset: int
) -> Dict[str, Any]:
    """Execute a row-returning query."""
    # Build WHERE clause
    where_clauses, params = _build_where_clause(parsed, tenant_id)
    where_str = " AND ".join(where_clauses)

    # Build ORDER BY clause
    order_by = ""
    for cmd in parsed.pipe_commands:
        if isinstance(cmd, SortCommand):
            order_by = f"ORDER BY {cmd.field} {cmd.order.upper()}"
            break

    # Build LIMIT clause
    limit_val = limit
    for cmd in parsed.pipe_commands:
        if isinstance(cmd, HeadCommand):
            limit_val = cmd.count
            break

    # Build final query
    query = f"""
    SELECT id, timestamp, level, source, message, metadata, raw_log
    FROM log_entries
    WHERE {where_str}
    {order_by}
    LIMIT {limit_val} OFFSET {offset}
    """

    try:
        rows = await conn.fetch(query, *params)
        result_rows = [dict(row) for row in rows]
        return {"rows": result_rows}
    except Exception as e:
        raise QueryExecutionError(f"Failed to execute row query: {str(e)}", query)


async def _execute_stats(
    parsed: ParsedQuery,
    tenant_id: str,
    conn
) -> Dict[str, Any]:
    """Execute a stats aggregation query."""
    # Find the stats command
    stats_cmd = None
    for cmd in parsed.pipe_commands:
        if isinstance(cmd, StatsCommand):
            stats_cmd = cmd
            break

    if not stats_cmd:
        return {"aggregations": []}

    # Validate stats command
    _validate_stats_command(stats_cmd)

    # Build WHERE clause
    where_clauses, params = _build_where_clause(parsed, tenant_id)
    where_str = " AND ".join(where_clauses)

    # Build SELECT and GROUP BY
    if stats_cmd.function == "count":
        select_expr = f"COUNT(*) AS count"
    else:
        # sum, avg, min, max
        if not stats_cmd.field:
            raise QueryExecutionError("Non-count functions require a field")
        select_expr = f"{stats_cmd.function.upper()}({stats_cmd.field}) AS {stats_cmd.function}"

    # Build query
    query = f"""
    SELECT {stats_cmd.group_by}, {select_expr}
    FROM log_entries
    WHERE {where_str}
    GROUP BY {stats_cmd.group_by}
    ORDER BY {stats_cmd.function} DESC
    """

    try:
        rows = await conn.fetch(query, *params)
        aggregations = [dict(row) for row in rows]
        return {"aggregations": aggregations}
    except Exception as e:
        raise QueryExecutionError(f"Failed to execute stats query: {str(e)}", query)


async def _get_total_count(
    parsed: ParsedQuery,
    tenant_id: str,
    conn
) -> int:
    """Get total count of matching records (before LIMIT)."""
    where_clauses, params = _build_where_clause(parsed, tenant_id)
    where_str = " AND ".join(where_clauses)

    query = f"SELECT COUNT(*) FROM log_entries WHERE {where_str}"

    try:
        result = await conn.fetchval(query, *params)
        return result or 0
    except Exception as e:
        logger.error(f"Failed to get total count: {str(e)}")
        return 0


def _build_where_clause(
    parsed: ParsedQuery,
    tenant_id: str
) -> tuple:
    """Build WHERE clause from filters and text search."""
    where_clauses = ["tenant_id = $1"]
    params = [tenant_id]
    param_index = 2

    # Add filters
    for filter_node in parsed.filters:
        clause, value = _build_filter_clause(filter_node, param_index)
        where_clauses.append(clause)
        params.append(value)
        param_index += 1

    # Add text search
    if parsed.text_search:
        for term in parsed.text_search.terms:
            where_clauses.append(f"message ILIKE ${param_index}")
            params.append(f"%{term}%")
            param_index += 1

    return where_clauses, params


def _validate_filter_field(field: str) -> None:
    """
    Validate that a filter field is one of the allowed log_entries columns.

    Raises QueryParseError so the caller receives a 400 (not a 500).
    """
    allowed_fields = {"timestamp", "level", "source", "message", "raw_log", "metadata"}
    if field not in allowed_fields:
        raise QueryParseError(
            f"Unknown filter field: '{field}'. "
            f"Allowed fields: {', '.join(sorted(allowed_fields))}"
        )


def _parse_timestamp_value(value: str) -> datetime:
    """
    Parse an ISO 8601 timestamp string into a datetime object.

    Accepts formats such as:
      - 2026-02-10T15:30:45
      - 2026-02-10T15:30:45Z
      - 2026-02-10T15:30:45+00:00
      - 2026-02-10 15:30:45

    Raises QueryParseError with a helpful message on invalid input.
    """
    # Normalise the common 'Z' suffix that fromisoformat doesn't accept
    # on Python < 3.11.
    normalised = value.replace("Z", "+00:00")
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(normalised.replace("+00:00", ""), fmt.replace("%z", "")).replace(
                tzinfo=timezone.utc
            ) if "%z" not in fmt else datetime.strptime(normalised, fmt)
        except ValueError:
            continue
    raise QueryParseError(
        f"Invalid timestamp format: '{value}'. "
        f"Use ISO 8601, e.g. 2026-02-10T15:30:45 or 2026-02-10T15:30:45Z"
    )


def _build_filter_clause(filter_node: FilterNode, param_index: int) -> tuple:
    """Build a single filter clause with field and timestamp validation."""
    field = filter_node.field
    operator = filter_node.operator
    value = filter_node.value

    # Edge Case 4: reject unknown fields before they reach SQL
    _validate_filter_field(field)

    # Edge Case 2: validate timestamp values when filtering on the timestamp column
    if field == "timestamp" and operator in (">", ">=", "<", "<=", "=", "!="):
        parsed_ts = _parse_timestamp_value(value)
        # Pass a tz-aware datetime; asyncpg handles the conversion to DB timestamptz
        if operator == "=":
            return f"{field} = ${param_index}", parsed_ts
        elif operator == "!=":
            return f"{field} != ${param_index}", parsed_ts
        elif operator == ">":
            return f"{field} > ${param_index}", parsed_ts
        elif operator == ">=":
            return f"{field} >= ${param_index}", parsed_ts
        elif operator == "<":
            return f"{field} < ${param_index}", parsed_ts
        elif operator == "<=":
            return f"{field} <= ${param_index}", parsed_ts

    # String / enum fields — pass value as-is (parameterised, injection-safe)
    if operator == "=":
        return f"{field} = ${param_index}", value
    elif operator == "!=":
        return f"{field} != ${param_index}", value
    elif operator == ">":
        return f"{field} > ${param_index}", value
    elif operator == ">=":
        return f"{field} >= ${param_index}", value
    elif operator == "<":
        return f"{field} < ${param_index}", value
    elif operator == "<=":
        return f"{field} <= ${param_index}", value
    else:
        raise QueryExecutionError(f"Unknown operator: {operator}")


def _validate_stats_command(stats_cmd: StatsCommand):
    """Validate a stats command."""
    # Validate function exists
    valid_functions = {"count", "sum", "avg", "min", "max"}
    if stats_cmd.function not in valid_functions:
        raise QueryExecutionError(
            f"Invalid stats function '{stats_cmd.function}'. "
            f"Must be one of: {', '.join(valid_functions)}"
        )

    # Validate that non-numeric aggregations on string fields are rejected
    numeric_functions = {"sum", "avg", "min", "max"}
    if stats_cmd.function in numeric_functions:
        if not stats_cmd.field:
            raise QueryExecutionError(
                f"Stats function '{stats_cmd.function}' requires a field argument"
            )

        # Fields that are known to be non-numeric
        non_numeric_fields = {"level", "source", "message", "raw_log"}
        if stats_cmd.field in non_numeric_fields:
            raise QueryExecutionError(
                f"Cannot use {stats_cmd.function} on non-numeric field '{stats_cmd.field}'"
            )

    # Validate group_by field exists
    valid_fields = {"timestamp", "level", "source", "message", "metadata", "raw_log"}
    if stats_cmd.group_by not in valid_fields:
        raise QueryExecutionError(
            f"Unknown field '{stats_cmd.group_by}' in GROUP BY clause"
        )
