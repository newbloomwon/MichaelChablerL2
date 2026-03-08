from fastapi import Request, HTTPException, status
from app.core.auth import decode_token
import logging

logger = logging.getLogger(__name__)

async def tenant_middleware(request: Request, call_next):
    # Skip CORS preflight requests — they don't carry auth headers
    if request.method == "OPTIONS":
        return await call_next(request)

    # Skip middleware for non-API routes or public routes
    public_paths = ["/health", "/api/auth/login", "/docs", "/openapi.json"]
    if any(request.url.path.startswith(p) for p in public_paths):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token"
        )

    token = auth_header.split(" ")[1]
    payload = decode_token(token)
    
    if not payload or "tenant_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or missing tenant information"
        )

    # Set the tenant context in the request state for use by dependencies
    request.state.tenant_id = payload["tenant_id"]
    request.state.user_id = payload.get("sub")

    return await call_next(request)
