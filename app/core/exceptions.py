import structlog
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger()

# ==========================================
# Custom Exception Classes
# ==========================================

class AppException(Exception):
    """
    Base exception for all custom application errors.
    Allows passing a specific error code, HTTP status code, and additional details.
    """
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "bad_request",
        details: Any = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class ResourceNotFoundException(AppException):
    #Raised when a requested resource is not found.
    def __init__(self, message: str = "Resource not found", details: Any = None):
        super().__init__(
            message=message,
            status_code=404,
            error_code="resource_not_found",
            details=details,
        )


class BadRequestException(AppException):
    #Raised for general bad requests and business logic violations
    def __init__(self, message: str = "Bad request", details: Any = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="bad_request",
            details=details,
        )

# ==========================================
# FastAPI Exception Handlers
# ==========================================

def _build_error_response(
    status_code: int, error_code: str, message: str, details: Any = None
) -> JSONResponse:
    #Helper to ensure all API errors follow the exact same JSON structure
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": error_code,
                "message": message,
                "details": details,
            }
        },
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Registers exception handlers to the FastAPI app to ensure
    all errors return a consistent JSON structure.
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "Application error",
            error_code=exc.error_code,
            status_code=exc.status_code,
            path=request.url.path,
        )
        return _build_error_response(exc.status_code, exc.error_code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.info("Request validation error", path=request.url.path)
        return _build_error_response(
            status_code=422,
            error_code="validation_error",
            message="Invalid request data",
            details=exc.errors(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        logger.warning("HTTP error", status_code=exc.status_code, path=request.url.path)
        return _build_error_response(exc.status_code, "http_error", exc.detail)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server error", path=request.url.path)
        return _build_error_response(
            status_code=500,
            error_code="internal_server_error",
            message="An unexpected error occurred.",
        )