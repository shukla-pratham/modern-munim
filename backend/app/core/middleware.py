"""
Custom middleware for error handling and request validation.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import os

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors with standardized format.
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation failed",
            "detail": errors
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions with standardized format.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "An error occurred",
            "status_code": exc.status_code
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions.
    Logs the error and returns a generic message to client.
    In development, include exception message in response to aid debugging.
    """
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    is_dev = os.getenv("ENVIRONMENT", "development") == "development"
    content = {
        "error": "Internal server error",
        "status_code": 500,
    }
    if is_dev:
        content["detail"] = str(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content
    )
