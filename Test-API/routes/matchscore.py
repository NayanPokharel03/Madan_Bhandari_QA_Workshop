"""Routes for `/matchscore` (POST, GET all, GET/PUT/PATCH/DELETE by Id)."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, status

from models.matchscore import MatchScorePatch, MatchScoreRequest, MatchScoreResponse
from services.matcher import score
from utils import file_storage
from utils.errors import APIError
from utils.validators import (
    ensure_exists,
    ensure_ids_are_new_or_identical,
    ensure_no_duplicate_content,
    ensure_non_empty,
    ensure_unique_ids,
)

router = APIRouter(tags=["matchscore"])
_STORE = "matchscore"


def _build_response(record: MatchScoreRequest) -> Dict[str, Any]:
    value, decision = score(record.Data1, record.Data2, record.DataType.value)
    return {
        "Score": value,
        "Decision": decision,
        "Id": record.Id,
        "Data1": record.Data1,
        "Data2": record.Data2,
        "DataType": record.DataType.value,
    }


@router.post(
    "/matchscore",
    response_model=List[MatchScoreResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Compute match score and decision for one or more comparisons",
)
def create_matchscore(records: List[MatchScoreRequest]) -> List[Dict[str, Any]]:
    ensure_non_empty(records)
    ids = [record.Id for record in records]
    ensure_unique_ids(ids)
    ensure_no_duplicate_content(records, keys=("Data1", "Data2", "DataType"))
    ensure_ids_are_new_or_identical(_STORE, records, content_keys=("Data1", "Data2", "DataType"))

    responses: List[Dict[str, Any]] = []
    for record in records:
        file_storage.save(_STORE, record.Id, record.model_dump(mode="json"))
        responses.append(_build_response(record))
    return responses


@router.get(
    "/matchscore",
    response_model=List[MatchScoreRequest],
    summary="List every stored /matchscore request",
)
def list_matchscore() -> List[Dict[str, Any]]:
    return file_storage.list_all(_STORE)


@router.get(
    "/matchscore/{record_id}",
    response_model=List[MatchScoreRequest],
    summary="Retrieve the stored /matchscore request for the given Id",
)
def get_matchscore(record_id: int) -> List[Dict[str, Any]]:
    return [ensure_exists(_STORE, record_id)]


@router.put(
    "/matchscore/{record_id}",
    response_model=List[MatchScoreResponse],
    summary="Replace the stored /matchscore record for the given Id",
)
def replace_matchscore(
    record_id: int, record: MatchScoreRequest
) -> List[Dict[str, Any]]:
    ensure_exists(_STORE, record_id)
    if record.Id != record_id:
        raise APIError(
            "Path Id and body Id must match.",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"path_id": record_id, "body_id": record.Id},
        )
    file_storage.save(_STORE, record_id, record.model_dump(mode="json"))
    return [_build_response(record)]


@router.patch(
    "/matchscore/{record_id}",
    response_model=List[MatchScoreResponse],
    summary="Partially update the stored /matchscore record",
)
def patch_matchscore(
    record_id: int, patch: MatchScorePatch
) -> List[Dict[str, Any]]:
    stored = ensure_exists(_STORE, record_id)
    updated = {**stored, **patch.model_dump(exclude_unset=True, mode="json")}
    record = MatchScoreRequest.model_validate(updated)
    file_storage.save(_STORE, record_id, record.model_dump(mode="json"))
    return [_build_response(record)]


@router.delete(
    "/matchscore/{record_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete the stored /matchscore record for the given Id",
)
def delete_matchscore(record_id: int) -> List[Dict[str, Any]]:
    ensure_exists(_STORE, record_id)
    file_storage.delete(_STORE, record_id)
    return [{"deleted": True, "Id": record_id, "store": _STORE}]
