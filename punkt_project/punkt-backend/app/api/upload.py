"""Upload API for handling file ingestion."""
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, BackgroundTasks

from app.core.database import get_db_conn
from app.models.api import APIResponse
from app.models.upload import (
    UploadInitRequest, UploadInitResponse, UploadCompleteRequest,
    UploadStatusResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])

# Upload storage directory
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/file/init", response_model=APIResponse)
async def init_upload(
    request: UploadInitRequest,
    conn=Depends(get_db_conn)
):
    """Initialize a file upload session."""
    try:
        tenant_id = getattr(conn, "tenant_id", None)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context missing"
            )

        upload_id = str(uuid.uuid4())
        upload_path = UPLOAD_DIR / upload_id
        upload_path.mkdir(parents=True, exist_ok=True)

        # Store metadata
        metadata = {
            "upload_id": upload_id,
            "tenant_id": tenant_id,
            "filename": request.filename,
            "file_size": request.file_size,
            "chunk_count": request.chunk_count,
            "format": request.format,
            "source": request.source,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }

        metadata_file = upload_path / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f)

        logger.info(f"Upload session initialized: {upload_id}")

        return APIResponse(
            success=True,
            data=UploadInitResponse(
                upload_id=upload_id,
                filename=request.filename,
                chunk_count=request.chunk_count,
                upload_url_template=f"/api/ingest/file/chunk/{upload_id}/{{chunk_number}}"
            ),
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Upload init error: {e}")
        return APIResponse(
            success=False,
            error={"code": "UPLOAD_INIT_ERROR", "message": str(e)},
            timestamp=datetime.utcnow()
        )


@router.post("/file/chunk/{upload_id}/{chunk_number}")
async def upload_chunk(
    upload_id: str,
    chunk_number: int,
    file: UploadFile,
    conn=Depends(get_db_conn)
):
    """Upload a file chunk."""
    try:
        upload_path = UPLOAD_DIR / upload_id
        if not upload_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found"
            )

        chunk_file = upload_path / f"chunk_{chunk_number}"
        content = await file.read()

        with open(chunk_file, "wb") as f:
            f.write(content)

        logger.info(f"Chunk {chunk_number} uploaded for {upload_id}")

        return APIResponse(
            success=True,
            data={"chunk_number": chunk_number, "size": len(content)},
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Chunk upload error: {e}")
        return APIResponse(
            success=False,
            error={"code": "CHUNK_UPLOAD_ERROR", "message": str(e)},
            timestamp=datetime.utcnow()
        )


@router.post("/file/complete")
async def complete_upload(
    request: UploadCompleteRequest,
    background_tasks: BackgroundTasks,
    conn=Depends(get_db_conn)
):
    """Mark upload as complete and start processing."""
    try:
        upload_path = UPLOAD_DIR / request.upload_id
        if not upload_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found"
            )

        # Load metadata
        metadata_file = upload_path / "metadata.json"
        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        # Schedule background processing
        from app.workers.processor import process_uploaded_file
        background_tasks.add_task(
            process_uploaded_file,
            request.upload_id,
            metadata
        )

        logger.info(f"Upload {request.upload_id} marked complete, processing scheduled")

        return APIResponse(
            success=True,
            data={"upload_id": request.upload_id, "status": "processing"},
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Upload complete error: {e}")
        return APIResponse(
            success=False,
            error={"code": "UPLOAD_COMPLETE_ERROR", "message": str(e)},
            timestamp=datetime.utcnow()
        )


@router.get("/file/status/{upload_id}")
async def get_upload_status(
    upload_id: str,
    conn=Depends(get_db_conn)
):
    """Get upload session status."""
    try:
        upload_path = UPLOAD_DIR / upload_id
        if not upload_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found"
            )

        metadata_file = upload_path / "metadata.json"
        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        # Count uploaded chunks
        chunk_count = len(list(upload_path.glob("chunk_*")))

        return APIResponse(
            success=True,
            data=UploadStatusResponse(
                upload_id=upload_id,
                status=metadata.get("status", "unknown"),
                filename=metadata["filename"],
                format=metadata["format"],
                source=metadata["source"],
                chunks_received=chunk_count,
                total_chunks=metadata["chunk_count"],
                created_at=datetime.fromisoformat(metadata["created_at"]),
                error_message=metadata.get("error_message")
            ),
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Upload status error: {e}")
        return APIResponse(
            success=False,
            error={"code": "UPLOAD_STATUS_ERROR", "message": str(e)},
            timestamp=datetime.utcnow()
        )
