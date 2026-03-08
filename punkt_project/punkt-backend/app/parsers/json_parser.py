"""JSON log parser for handling NDJSON and JSON array formats."""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Generator, Dict, Any

logger = logging.getLogger(__name__)


def parse_json_file(
    filepath: Path,
    tenant_id: str,
    source: str
) -> Generator[Dict[str, Any], None, None]:
    """
    Parse JSON log file (NDJSON or JSON array format).
    Yields log entry dicts ready for DB insertion.

    Args:
        filepath: Path to the log file
        tenant_id: Tenant ID for the logs
        source: Source identifier for the logs

    Yields:
        Dict with keys: timestamp, tenant_id, source, level, message, metadata, raw_log
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content:
            return

        # Try to parse as JSON array first
        if content.startswith('['):
            try:
                logs = json.loads(content)
                if isinstance(logs, list):
                    for log_entry in logs:
                        yield _normalize_log_entry(log_entry, tenant_id, source)
                    return
            except json.JSONDecodeError:
                pass

        # Parse as NDJSON (newline-delimited)
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    log_data = json.loads(line)
                    yield _normalize_log_entry(log_data, tenant_id, source)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON at line {line_num}: {e}")
                    continue

    except Exception as e:
        logger.error(f"Error parsing JSON file {filepath}: {e}", exc_info=True)
        raise


def _normalize_log_entry(log_data: Dict[str, Any], tenant_id: str, source: str) -> Dict[str, Any]:
    """Normalize a log entry to the standard schema."""
    if not isinstance(log_data, dict):
        log_data = {"message": str(log_data)}

    # Extract timestamp
    timestamp = _parse_timestamp(log_data.get("timestamp", datetime.utcnow().isoformat()))

    # Extract or infer level
    level = log_data.get("level") or log_data.get("severity") or "INFO"
    level = level.upper()
    if level not in ["DEBUG", "INFO", "WARN", "ERROR"]:
        level = "INFO"

    # Extract message
    message = log_data.get("message") or log_data.get("msg") or str(log_data)

    # Collect metadata (exclude core fields)
    core_fields = {"timestamp", "level", "severity", "message", "msg"}
    metadata = {k: v for k, v in log_data.items() if k not in core_fields}

    return {
        "timestamp": timestamp,
        "tenant_id": tenant_id,
        "source": source,
        "level": level,
        "message": str(message),
        "metadata": metadata,
        "raw_log": json.dumps(log_data)
    }


def _parse_timestamp(ts: Any) -> int:
    """Parse timestamp to Unix timestamp (integer seconds)."""
    try:
        if isinstance(ts, int):
            return ts
        elif isinstance(ts, float):
            return int(ts)
        elif isinstance(ts, str):
            try:
                # Try ISO 8601 format
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                try:
                    # Try other common formats
                    dt = datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    logger.warning(f"Could not parse timestamp: {ts}")
                    return int(datetime.utcnow().timestamp())
            return int(dt.timestamp())
        else:
            return int(datetime.utcnow().timestamp())
    except Exception as e:
        logger.warning(f"Error parsing timestamp {ts}: {e}")
        return int(datetime.utcnow().timestamp())
