"""FastAPI application factory and uvicorn entry point."""

from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from routes import admin, buggy, health, keys, matchscore, ranges
from utils.errors import error_body, register_error_handlers
from utils.logging_config import get_logger

logger = get_logger()

REQUIRED_HEADER_NAME = "workshop"
REQUIRED_HEADER_VALUE = "MadanBhandari"
_HEADER_EXEMPT_PATHS = {"/docs", "/redoc", "/openapi.json"}


DESCRIPTION = """
Teaching REST API for the **QA Automation Workshop**.

Every response is a **JSON array**. Every failure returns a standard
error envelope:

```
{
  "error": true,
  "message": "...",
  "details": "...",
  "timestamp": "...",
  "status": 4xx | 5xx,
  "path": "/endpoint"
}
```

Use `/docs` for interactive Swagger, `/redoc` for ReDoc, and the
`postman/` folder for a ready-made collection.
"""


def create_app() -> FastAPI:
    app = FastAPI(
        title="Test-API — QA Workshop",
        version="2.0.0",
        description=DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    register_error_handlers(app)

    @app.middleware("http")
    async def _require_workshop_header(request: Request, call_next):
        if request.url.path not in _HEADER_EXEMPT_PATHS:
            if request.headers.get(REQUIRED_HEADER_NAME) != REQUIRED_HEADER_VALUE:
                return JSONResponse(
                    status_code=401,
                    content=error_body(
                        message=(
                            f"Missing or invalid '{REQUIRED_HEADER_NAME}' header."
                        ),
                        status_code=401,
                        details=(
                            f"Send header '{REQUIRED_HEADER_NAME}: "
                            f"{REQUIRED_HEADER_VALUE}'."
                        ),
                        path=request.url.path,
                    ),
                )
        return await call_next(request)

    @app.middleware("http")
    async def _log_requests(request: Request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "%s %s -> unhandled exception in %.1fms",
                request.method,
                request.url.path,
                elapsed_ms,
            )
            raise
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s in %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    @app.get("/", include_in_schema=False)
    def root() -> JSONResponse:
        return JSONResponse(
            [
                {
                    "message": "Welcome to the QA Workshop Test-API.",
                    "docs": "/docs",
                    "redoc": "/redoc",
                    "health": "/healthcheck",
                    "version": "/version",
                }
            ]
        )

    app.include_router(keys.router)
    app.include_router(ranges.router)
    app.include_router(matchscore.router)
    app.include_router(health.router)
    app.include_router(admin.router)
    app.include_router(buggy.router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
