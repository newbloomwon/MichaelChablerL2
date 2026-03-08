"""Custom exceptions for Punkt API."""


class PunktError(Exception):
    """Base exception class for Punkt-specific errors."""

    def __init__(self, message: str, code: str, status_code: int = 500):
        """
        Initialize PunktError.

        Args:
            message: Human-readable error message
            code: Machine-readable error code (e.g., "QUERY_TIMEOUT")
            status_code: HTTP status code (default 500)
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class QueryTimeoutError(PunktError):
    """Raised when query execution exceeds the allowed timeout (HTTP 408)."""

    def __init__(self, message: str = "Query execution timed out"):
        super().__init__(message, "QUERY_TIMEOUT", 408)


class QueryParseError(PunktError):
    """Raised when the submitted query string has invalid syntax (HTTP 400)."""

    def __init__(self, message: str = "Invalid query syntax"):
        super().__init__(message, "QUERY_PARSE_ERROR", 400)


class TenantContextError(PunktError):
    """Raised when the tenant context is missing or cannot be resolved (HTTP 400)."""

    def __init__(self, message: str = "Tenant context missing"):
        super().__init__(message, "TENANT_CONTEXT_ERROR", 400)


class UploadError(PunktError):
    """Raised when a file upload operation fails (HTTP 400)."""

    def __init__(self, message: str = "Upload failed"):
        super().__init__(message, "UPLOAD_ERROR", 400)


class AuthenticationError(PunktError):
    """Raised when authentication fails or credentials are invalid (HTTP 401)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR", 401)
