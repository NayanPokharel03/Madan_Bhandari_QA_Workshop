"""Intentionally buggy endpoints for defect-hunting exercises.

These endpoints look almost identical to the real ones but each hides
a common QA-worthy defect. Students should discover and document them.

Do **not** enable these on real systems. They are only for teaching.

Defect index (also documented in POSTMAN_EXERCISES.md):
    /buggy/keys        POST  → accepts an empty array and returns []
    /buggy/matchscore  POST  → swaps Data1/Data2 in the response
    /buggy/matchscore/{id} GET → returns 200 with an empty array when missing
    /buggy/ranges/{id} DELETE → says success even when the Id does not exist
    /buggy/echo        GET  → leaks internals in the message (info disclosure)
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, status

from models.keys import KeyRequest
from models.matchscore import MatchScoreRequest
from services.key_generator import generate_keys
from services.matcher import score
from utils import file_storage

router = APIRouter(prefix="/buggy", tags=["buggy (intentional defects)"])


@router.post("/keys", status_code=status.HTTP_201_CREATED)
def buggy_create_keys(records: List[KeyRequest]) -> List[Dict[str, Any]]:
    # BUG: no non-empty check → returns [] for empty arrays instead of 400.
    return [
        {
            "Keys": generate_keys(r.Data, r.DataType.value),
            "Id": r.Id,
            "Data": r.Data,
            "DataType": r.DataType.value,
        }
        for r in records
    ]


@router.post("/matchscore", status_code=status.HTTP_201_CREATED)
def buggy_matchscore(records: List[MatchScoreRequest]) -> List[Dict[str, Any]]:
    results = []
    for r in records:
        value, decision = score(r.Data1, r.Data2, r.DataType.value)
        # BUG: Data1 and Data2 are swapped in the response body.
        results.append(
            {
                "Score": value,
                "Decision": decision,
                "Id": r.Id,
                "Data1": r.Data2,
                "Data2": r.Data1,
                "DataType": r.DataType.value,
            }
        )
    return results


@router.get("/matchscore/{record_id}")
def buggy_get_matchscore(record_id: int) -> List[Dict[str, Any]]:
    stored = file_storage.get("matchscore", record_id)
    # BUG: silently returns [] with 200 instead of 404 when missing.
    return [stored] if stored else []


@router.delete("/ranges/{record_id}")
def buggy_delete_range(record_id: int) -> List[Dict[str, Any]]:
    file_storage.delete("ranges", record_id)
    # BUG: always reports success, even when nothing was deleted.
    return [{"deleted": True, "Id": record_id, "store": "ranges"}]


@router.get("/echo")
def buggy_echo() -> List[Dict[str, Any]]:
    # BUG: information disclosure — leaks internal paths and secrets.
    return [
        {
            "status": "Healthy",
            "message": "Health check passed",
            "storage_path": str(file_storage._STORAGE_DIR),  # noqa: SLF001
            "debug_token": "SUPER-SECRET-DO-NOT-EXPOSE",
        }
    ]
