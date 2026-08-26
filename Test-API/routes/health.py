"""Route for `/healthcheck`."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter

from models.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/healthcheck",
    response_model=List[HealthResponse],
    summary="Liveness probe",
)
def healthcheck() -> List[HealthResponse]:
    return [HealthResponse(status="Healthy", message="Health check passed")]
