"""Global exception handlers for Punkt API."""
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import PunktError
from app.models.api import APIResponse, ErrorDetail

logger = logging.getLogger(__name__)


async def punkt_error_handler(request: Request, exc: PunktError) -> JSONResponse:
    """
    Global exception handler for PunktError and all subclasses.

    Converts PunktError exceptions into the standardized APIResponse format
    and returns the appropriate HTTP status code. All error details are
    surfaced via the ErrorDetail schema so clients receive consistent
    machine-readable codes alongside human-readable messages.

    Args:
        request: The incoming FastAPI request (unused but required by FastAPI).
        exc: The PunktError (or subclass) that was raised.

    Returns:
        JSONResponse with the serialized APIResponse payload and the
        HTTP status code carried by the exception.
    """
    logger.warning(
        "PunktError: code=%s status=%s path=%s message=%s",
        exc.code,
        exc.status_code,
        request.url.path,
        exc.message,
    )

    response_body = APIResponse(
        success=False,
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
        ),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response_body.dict(),
    )
