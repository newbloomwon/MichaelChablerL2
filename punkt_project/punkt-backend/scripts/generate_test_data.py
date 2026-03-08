#!/usr/bin/env python3
"""Generate test log data for Punkt development and testing."""

import json
import random
import argparse
from datetime import datetime, timedelta
from typing import Generator

SOURCES = [
    "/var/log/nginx/access.log",
    "/var/log/app/api.log",
    "/var/log/app/worker.log",
    "/var/log/auth.log",
]

LEVELS = ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]
LEVEL_WEIGHTS = [10, 60, 20, 8, 2]  # Realistic distribution

MESSAGES = {
    "DEBUG": ["Cache hit for key", "Query executed in {ms}ms", "Request payload: {size} bytes"],
    "INFO": ["User logged in", "Request completed", "Background job finished", "File uploaded"],
    "WARN": ["Slow query detected", "Rate limit approaching", "Disk usage at 80%"],
    "ERROR": ["Connection timeout", "Database error", "Invalid request format"],
    "CRITICAL": ["Out of memory", "Database connection lost", "Service unavailable"],
}

def generate_json_logs(count: int, tenant_id: str) -> Generator[dict, None, None]:
    """Generate JSON format logs."""
    base_time = datetime.utcnow() - timedelta(hours=24)
    
    for i in range(count):
        level = random.choices(LEVELS, weights=LEVEL_WEIGHTS)[0]
        source = random.choice(SOURCES)
        timestamp = base_time + timedelta(seconds=i * (86400 / count))
        
        yield {
            "timestamp": timestamp.isoformat() + "Z",
            "level": level,
            "source": source,
            "message": random.choice(MESSAGES[level]).format(
                ms=random.randint(10, 5000),
                size=random.randint(100, 10000)
            ),
            "metadata": {
                "host": f"server-{random.randint(1, 5):02d}",
                "request_id": f"req-{random.randint(10000, 99999)}",
                "user_id": f"user-{random.randint(1, 100)}" if random.random() > 0.3 else None
            }
        }

def generate_nginx_logs(count: int) -> Generator[str, None, None]:
    """Generate nginx access log format."""
    base_time = datetime.utcnow() - timedelta(hours=24)
    methods = ["GET", "POST", "PUT", "DELETE"]
    paths = ["/api/users", "/api/logs", "/api/search", "/health", "/static/app.js"]
    statuses = [200, 200, 200, 201, 204, 400, 401, 404, 500]
    
    for i in range(count):
        timestamp = base_time + timedelta(seconds=i * (86400 / count))
        formatted_time = timestamp.strftime("%d/%b/%Y:%H:%M:%S +0000")
        
        yield (
            f"192.168.1.{random.randint(1, 255)} - - [{formatted_time}] "
            f'"{random.choice(methods)} {random.choice(paths)} HTTP/1.1" '
            f"{random.choice(statuses)} {random.randint(100, 50000)} "
            f'"-" "Mozilla/5.0"'
        )

def main():
    parser = argparse.ArgumentParser(description="Generate test log data")
    parser.add_argument("--count", type=int, default=1000, help="Number of logs")
    parser.add_argument("--format", choices=["json", "nginx"], default="json")
    parser.add_argument("--tenant", default="tenant_acme", help="Tenant ID")
    parser.add_argument("--output", default="-", help="Output file (- for stdout)")
    
    args = parser.parse_args()
    
    if args.format == "json":
        logs = list(generate_json_logs(args.count, args.tenant))
        output = json.dumps({"logs": logs}, indent=2)
    else:
        output = "\n".join(generate_nginx_logs(args.count))
    
    if args.output == "-":
        print(output)
    else:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Generated {args.count} {args.format} logs to {args.output}")

if __name__ == "__main__":
    main()
