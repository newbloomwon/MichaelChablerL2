from fastapi import FastAPI, Request, WebSocket, WebSocketException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import auth, ingest
from app.middleware.tenant import tenant_middleware
from app.core.database import db
from app.core.auth import decode_token
from app.core.exceptions import PunktError
from app.core.error_handlers import punkt_error_handler
from app.ws import ws_manager
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME)

# Register global exception handler for PunktError (resolves I-08 response consistency)
app.add_exception_handler(PunktError, punkt_error_handler)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up tenant middleware
@app.middleware("http")
async def add_tenant_middleware(request: Request, call_next):
    return await tenant_middleware(request, call_next)

# Import Redis manager
from app.core.redis import redis_manager

# Database and Redis lifecycle management
@app.on_event("startup")
async def startup():
    await db.connect()
    # On startup, ensure partitions exist for current and next 2 months
    async with db.pool.acquire() as conn:
        await conn.execute("SELECT create_monthly_partition(CURRENT_DATE);")
        await conn.execute("SELECT create_monthly_partition((CURRENT_DATE + INTERVAL '1 month')::DATE);")
        await conn.execute("SELECT create_monthly_partition((CURRENT_DATE + INTERVAL '2 months')::DATE);")
    logger.info("Application started and database partitions verified")

    # Initialize Redis connection
    try:
        await redis_manager.connect()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed (optional): {e}")

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()
    logger.info("Application shutdown")

    # Disconnect Redis
    try:
        await redis_manager.disconnect()
        logger.info("Redis disconnected")
    except Exception as e:
        logger.warning(f"Error disconnecting Redis: {e}")

# Include routers
app.include_router(auth.router)
app.include_router(ingest.router)

# Import and register upload, search, stats, and sources routers
from app.api import upload, search, stats, sources
app.include_router(upload.router, prefix="/api", tags=["ingest"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(stats.router, prefix="/api", tags=["stats"])
app.include_router(sources.router, prefix="/api", tags=["sources"])

logger.info("All routers registered")


@app.websocket("/ws/{tenant_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str, token: str = None):
    """
    WebSocket endpoint for real-time log streaming.

    Requires JWT token in query parameter: ws://host/ws/{tenant_id}?token={jwt}
    Browser WebSocket API cannot set custom headers, so token is passed as query param.
    """
    try:
        # Extract JWT from query parameter
        if not token:
            logger.warning(f"WebSocket auth failed: missing token query param for tenant={tenant_id}")
            await websocket.close(code=1008, reason="Missing token query parameter")
            return

        # Decode and validate JWT
        payload = decode_token(token)
        if not payload:
            logger.warning(f"WebSocket auth failed: invalid token for tenant={tenant_id}")
            await websocket.close(code=1008, reason="Invalid or expired token")
            return

        # Extract user_id from JWT payload
        user_id = payload.get("sub")
        token_tenant_id = payload.get("tenant_id")

        if not user_id:
            logger.warning(f"WebSocket auth failed: no user_id in token for tenant={tenant_id}")
            await websocket.close(code=1008, reason="Invalid token payload")
            return

        # Verify tenant_id matches
        if token_tenant_id != tenant_id:
            logger.warning(
                f"WebSocket auth failed: tenant mismatch "
                f"(path={tenant_id}, token={token_tenant_id})"
            )
            await websocket.close(code=1008, reason="Tenant mismatch")
            return

        # Connect via WebSocket manager
        connected = await ws_manager.connect(websocket, tenant_id, user_id)
        if not connected:
            await websocket.close(code=1008, reason="Connection failed")
            return

        logger.info(f"WebSocket connected: tenant={tenant_id}, user={user_id}")

        # Listen for client messages
        try:
            while True:
                message = await websocket.receive_json()
                await ws_manager.handle_client_message(websocket, tenant_id, message)
        except WebSocketException as e:
            logger.warning(f"WebSocket disconnected: {e}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    except Exception as e:
        logger.error(f"WebSocket endpoint error: {e}")

    finally:
        await ws_manager.disconnect(websocket, tenant_id)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
