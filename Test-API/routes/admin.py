"""Admin / utility endpoints used for QA workshops.

- `/version`          → simple metadata (great for smoke tests)
- `/stats`            → per-store counts
- `/admin/seed`       → populate stores with sample records
- `/admin/reset`      → wipe every store
- `/admin/reset/{store}` → wipe a single store
- `/error/{code}`     → trigger an arbitrary HTTP error for testing
- `/error/boom`       → raise an unhandled exception → real 500
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, status

from utils import file_storage
from utils.errors import APIError

router = APIRouter(tags=["admin"])

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_STORES = ("keys", "ranges", "matchscore")


@router.get("/version", summary="Version / build metadata")
def version() -> List[Dict[str, str]]:
    return [
        {
            "name": "Test-API",
            "version": "2.0.0",
            "purpose": "QA Automation Workshop teaching API",
        }
    ]


@router.get("/stats", summary="Record counts per store")
def stats() -> List[Dict[str, Any]]:
    return [{store: file_storage.count(store) for store in _STORES}]


@router.post(
    "/admin/seed",
    status_code=status.HTTP_201_CREATED,
    summary="Load sample data into every store",
)
def seed_all() -> List[Dict[str, Any]]:
    results = {}
    for store in _STORES:
        results[store] = _seed_store(store)
    return [{"seeded": results}]


@router.post(
    "/admin/reset",
    summary="Clear every store (careful!)",
)
def reset_all() -> List[Dict[str, Any]]:
    return [{store: file_storage.clear(store) for store in _STORES}]


@router.post(
    "/admin/reset/{store}",
    summary="Clear a single store",
)
def reset_store(store: str) -> List[Dict[str, Any]]:
    if store not in _STORES:
        raise APIError(
            f"Unknown store '{store}'.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"allowed_stores": list(_STORES)},
        )
    return [{"cleared": store, "removed": file_storage.clear(store)}]


@router.get("/error/boom", summary="Raise an unhandled exception (real 500)")
def boom() -> None:
    raise RuntimeError("Boom! This is an intentionally unhandled server error.")


@router.get(
    "/error/{code}",
    summary="Return a chosen HTTP error (for status-code exercises)",
)
def raise_status(code: int) -> None:
    if code < 400 or code > 599:
        raise APIError(
            "Only 4xx and 5xx status codes are allowed here.",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"requested": code},
        )
    raise APIError(
        f"Simulated error with status {code}.",
        status_code=code,
        details={"hint": "Use this to practice status-code assertions in Postman."},
    )


def _seed_store(store: str) -> int:
    path = _DATA_DIR / f"sample_{store}.json"
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as fh:
        records = json.load(fh)
    inserted = 0
    for record in records:
        record_id = record.get("Id")
        if record_id is None:
            continue
        if file_storage.exists(store, int(record_id)):
            continue
        file_storage.save(store, int(record_id), record)
        inserted += 1
    return inserted
