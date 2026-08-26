"""Standard error envelope, exception, and FastAPI handlers.

All API errors are serialised to a single shape so students can write
one Postman test that works for every failure:

    {
      "error": true,
      "message": "...",
      "details": "...",
      "timestamp": "2026-08-01T12:34:56.789Z",
      "status": 409,
      "path": "/keys"
    }
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"


def error_body(
    message: str,
    status_code: int,
    details: Any = None,
    path: Optional[str] = None,
) -> dict:
    return {
        "error": True,
        "message": message,
        "details": details,
        "timestamp": _now_iso(),
        "status": status_code,
        "path": path,
    }


class APIError(Exception):
    """Raise this anywhere to emit a standard error response."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def _on_api_error(request: Request, exc: APIError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(
                message=exc.message,
                status_code=exc.status_code,
                details=exc.details,
                path=request.url.path,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def _on_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_body(
                message="Request validation failed.",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                details=exc.errors(),
                path=request.url.path,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _on_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(
                message=str(exc.detail),
                status_code=exc.status_code,
                path=request.url.path,
            ),
        )

    @app.exception_handler(Exception)
    async def _on_unhandled(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_body(
                message="Internal server error.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details=str(exc),
                path=request.url.path,
            ),
        )
