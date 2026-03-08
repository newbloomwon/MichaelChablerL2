"""Nginx log parser for combined and error log formats."""
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Generator, Dict, Any

logger = logging.getLogger(__name__)

# Regex pattern for Nginx combined log format
NGINX_COMBINED_PATTERN = r'^(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+) (?P<protocol>\S+)" (?P<status>\d+) (?P<size>\d+)'

# Status code to log level mapping
STATUS_LEVEL_MAP = {
    "1": "INFO",
    "2": "INFO",
    "3": "INFO",
    "4": "WARN",
    "5": "ERROR",
}


def parse_nginx_file(
    filepath: Path,
    tenant_id: str,
    source: str
) -> Generator[Dict[str, Any], None, None]:
    """
    Parse Nginx log file (combined format).
    Yields log entry dicts ready for DB insertion.

    Args:
        filepath: Path to the log file
        tenant_id: Tenant ID for the logs
        source: Source identifier for the logs

    Yields:
        Dict with keys: timestamp, tenant_id, source, level, message, metadata, raw_log
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                match = re.match(NGINX_COMBINED_PATTERN, line)
                if not match:
                    logger.warning(f"Line {line_num} does not match Nginx pattern: {line[:50]}")
                    continue

                try:
                    groups = match.groupdict()
                    timestamp = _parse_nginx_timestamp(groups["timestamp"])
                    status_code = int(groups["status"])
                    level = STATUS_LEVEL_MAP.get(str(status_code // 100), "INFO")

                    yield {
                        "timestamp": timestamp,
                        "tenant_id": tenant_id,
                        "source": source,
                        "level": level,
                        "message": f'{groups["method"]} {groups["path"]}',
                        "metadata": {
                            "ip": groups["ip"],
                            "status": status_code,
                            "size": int(groups["size"]),
                            "protocol": groups["protocol"]
                        },
                        "raw_log": line
                    }
                except Exception as e:
                    logger.warning(f"Error processing line {line_num}: {e}")
                    continue

    except Exception as e:
        logger.error(f"Error parsing Nginx file {filepath}: {e}", exc_info=True)
        raise


def _parse_nginx_timestamp(timestamp_str: str) -> int:
    """
    Parse Nginx timestamp format: 'DD/Mon/YYYY:HH:MM:SS +ZZZZ'
    Returns Unix timestamp (integer seconds).
    """
    try:
        # Remove timezone info for parsing
        dt_str = timestamp_str.split(" ")[0]
        dt = datetime.strptime(dt_str, "%d/%b/%Y:%H:%M:%S")
        return int(dt.timestamp())
    except Exception as e:
        logger.warning(f"Failed to parse Nginx timestamp '{timestamp_str}': {e}")
        return int(datetime.utcnow().timestamp())
