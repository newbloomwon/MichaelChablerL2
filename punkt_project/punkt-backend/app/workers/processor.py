"""Background worker for processing uploaded log files."""
import asyncio
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

from app.core.database import db
from app.core.redis import redis_manager
from app.parsers import parse_json_file, parse_nginx_file
from app.ws.broadcaster import broadcast_batch

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("/tmp/uploads")
BATCH_SIZE = 100


async def process_uploaded_file(upload_id: str, upload_metadata: dict):
    """
    Background worker that processes uploaded files.

    Flow:
    1. Load upload metadata
    2. Reassemble chunks from temp storage
    3. Parse file (JSON or Nginx format)
    4. Batch insert into database
    5. Cache recent logs to Redis
    6. Clean up temp files
    7. Update job status
    """
    upload_path = UPLOAD_DIR / upload_id
    temp_file = None

    try:
        logger.info(f"Starting file processing for upload {upload_id}")

        # Extract metadata
        tenant_id = upload_metadata.get("tenant_id")
        filename = upload_metadata.get("filename")
        file_format = upload_metadata.get("format")
        source = upload_metadata.get("source")
        chunk_count = upload_metadata.get("chunk_count")

        if not all([tenant_id, filename, file_format, source, chunk_count]):
            raise ValueError("Missing required metadata fields")

        # Step 1: Reassemble chunks
        logger.info(f"Reassembling {chunk_count} chunks for {upload_id}")
        temp_file = Path(f"/tmp/{upload_id}.log")

        with open(temp_file, "wb") as f:
            for chunk_num in range(chunk_count):
                chunk_file = upload_path / f"chunk_{chunk_num}"
                if not chunk_file.exists():
                    raise FileNotFoundError(f"Missing chunk {chunk_num}")
                with open(chunk_file, "rb") as cf:
                    f.write(cf.read())

        logger.info(f"Chunks reassembled: {temp_file}")

        # Step 2: Parse file based on format
        logger.info(f"Parsing {file_format} file")
        if file_format == "json":
            parser = parse_json_file(temp_file, tenant_id, source)
        elif file_format == "nginx":
            parser = parse_nginx_file(temp_file, tenant_id, source)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

        # Step 3: Batch process and insert logs
        await _batch_insert_logs(tenant_id, parser)

        # Step 4: Update metadata with success
        upload_metadata["status"] = "completed"
        upload_metadata["completed_at"] = datetime.utcnow().isoformat()

        metadata_file = upload_path / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(upload_metadata, f)

        logger.info(f"File processing completed for upload {upload_id}")

    except Exception as e:
        logger.error(f"Error processing upload {upload_id}: {e}", exc_info=True)

        # Update metadata with error
        try:
            upload_metadata["status"] = "failed"
            upload_metadata["error_message"] = str(e)
            upload_metadata["failed_at"] = datetime.utcnow().isoformat()

            metadata_file = upload_path / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(upload_metadata, f)
        except Exception as meta_err:
            logger.error(f"Failed to update metadata: {meta_err}")

    finally:
        # Step 5: Clean up temporary files
        try:
            if temp_file and temp_file.exists():
                temp_file.unlink()
                logger.info(f"Cleaned up temp file: {temp_file}")

            if upload_path.exists():
                shutil.rmtree(upload_path)
                logger.info(f"Cleaned up upload directory: {upload_path}")
        except Exception as cleanup_err:
            logger.warning(f"Error during cleanup: {cleanup_err}")


async def _batch_insert_logs(tenant_id: str, parser_gen):
    """
    Batch insert logs from parser generator into database.
    Also caches recent logs to Redis.
    """
    batch = []
    inserted_count = 0

    try:
        for log_entry in parser_gen:
            batch.append(log_entry)

            if len(batch) >= BATCH_SIZE:
                inserted_count += await _insert_batch(tenant_id, batch)
                batch = []

        # Insert remaining logs
        if batch:
            inserted_count += await _insert_batch(tenant_id, batch)

        logger.info(f"Inserted {inserted_count} logs for tenant {tenant_id}")

    except Exception as e:
        logger.error(f"Error during batch insert: {e}", exc_info=True)
        raise


async def _insert_batch(tenant_id: str, batch: list) -> int:
    """Insert a batch of logs and cache them in Redis."""
    if not batch:
        return 0

    try:
        async with db.pool.acquire() as conn:
            # Prepare records for bulk insert
            records = [
                (
                    log["timestamp"],
                    tenant_id,
                    log["source"],
                    log["level"],
                    log["message"],
                    json.dumps(log.get("metadata", {})),
                    log.get("raw_log", "")
                )
                for log in batch
            ]

            # Batch insert
            await conn.executemany(
                """
                INSERT INTO log_entries (timestamp, tenant_id, source, level, message, metadata, raw_log)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                records
            )

        # Cache recent logs to Redis
        if redis_manager and redis_manager.client:
            for log in batch:
                try:
                    await redis_manager.cache_recent_log(tenant_id, log)
                except Exception as redis_err:
                    logger.warning(f"Failed to cache log to Redis: {redis_err}")

        # Broadcast to connected WebSocket clients (non-fatal)
        try:
            client_count = await broadcast_batch(tenant_id, batch)
            if client_count > 0:
                logger.debug(f"Broadcast batch of {len(batch)} to {client_count} WebSocket clients")
        except Exception as ws_err:
            logger.warning(f"Failed to broadcast batch to WebSocket: {ws_err}")

        return len(batch)

    except Exception as e:
        logger.error(f"Error inserting batch: {e}", exc_info=True)
        raise
