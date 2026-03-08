"""Data models for search API."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SearchFilter(BaseModel):
    """Filter criteria for log search."""
    field: str
    operator: str  # eq, ne, gt, gte, lt, lte, in, contains
    value: Any


class SearchRequest(BaseModel):
    """Request to search logs."""
    query: Optional[str] = None
    filters: Optional[List[SearchFilter]] = None
    source: Optional[str] = None
    level: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="timestamp")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class LogEntry(BaseModel):
    """A single log entry response."""
    id: Optional[str] = None
    timestamp: int
    level: str
    source: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    raw_log: Optional[str] = None


class SearchResponse(BaseModel):
    """Response with search results."""
    total_count: int
    returned_count: int
    offset: int
    limit: int
    results: List[LogEntry]
    execution_time_ms: float
