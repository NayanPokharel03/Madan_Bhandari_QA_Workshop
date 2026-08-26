"""Pydantic model for the `/healthcheck` endpoint."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    message: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"status": "Healthy", "message": "Health check passed"}]
        }
    )
