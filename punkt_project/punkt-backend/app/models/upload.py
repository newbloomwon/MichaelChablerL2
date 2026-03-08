"""Data models for file upload API."""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class UploadInitRequest(BaseModel):
    """Request to initiate a file upload."""
    filename: str = Field(..., min_length=1)
    file_size: int = Field(..., gt=0)
    chunk_count: int = Field(..., gt=0)
    format: Literal["json", "nginx"]
    source: str = Field(..., min_length=1)


class UploadInitResponse(BaseModel):
    """Response from upload initialization."""
    upload_id: str
    filename: str
    chunk_count: int
    upload_url_template: str


class ChunkUploadRequest(BaseModel):
    """Request to upload a file chunk."""
    chunk_number: int = Field(..., ge=0)
    chunk_data: bytes


class UploadCompleteRequest(BaseModel):
    """Request to mark upload as complete and start processing."""
    upload_id: str


class UploadStatusResponse(BaseModel):
    """Response with upload status."""
    upload_id: str
    status: str  # pending, processing, completed, failed
    filename: str
    format: str
    source: str
    chunks_received: int
    total_chunks: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
