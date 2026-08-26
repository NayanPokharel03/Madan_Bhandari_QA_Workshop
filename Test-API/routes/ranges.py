"""Routes for `/ranges` (POST, GET all, GET/PUT/PATCH/DELETE by Id)."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, status

from models.ranges import RangePatch, RangeRequest, RangeResponse
from services.range_generator import generate_ranges
from utils import file_storage
from utils.errors import APIError
from utils.validators import (
    ensure_exists,
    ensure_ids_are_new_or_identical,
    ensure_no_duplicate_content,
    ensure_non_empty,
    ensure_unique_ids,
)

router = APIRouter(tags=["ranges"])
_STORE = "ranges"


def _build_response(record: RangeRequest) -> Dict[str, Any]:
    return {
        "Ranges": generate_ranges(record.Data, record.DataType.value),
        "Id": record.Id,
        "Data": record.Data,
        "DataType": record.DataType.value,
    }


@router.post(
    "/ranges",
    response_model=List[RangeResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Generate ranges for one or more records",
)
def create_ranges(records: List[RangeRequest]) -> List[Dict[str, Any]]:
    ensure_non_empty(records)
    ids = [record.Id for record in records]
    ensure_unique_ids(ids)
    ensure_no_duplicate_content(records, keys=("Data", "DataType"))
    ensure_ids_are_new_or_identical(_STORE, records, content_keys=("Data", "DataType"))

    responses: List[Dict[str, Any]] = []
    for record in records:
        file_storage.save(_STORE, record.Id, record.model_dump(mode="json"))
        responses.append(_build_response(record))
    return responses


@router.get(
    "/ranges",
    response_model=List[RangeRequest],
    summary="List every stored /ranges request",
)
def list_ranges() -> List[Dict[str, Any]]:
    return file_storage.list_all(_STORE)


@router.get(
    "/ranges/{record_id}",
    response_model=List[RangeRequest],
    summary="Retrieve the stored /ranges request for the given Id",
)
def get_range(record_id: int) -> List[Dict[str, Any]]:
    return [ensure_exists(_STORE, record_id)]


@router.put(
    "/ranges/{record_id}",
    response_model=List[RangeResponse],
    summary="Replace the stored /ranges record for the given Id",
)
def replace_range(record_id: int, record: RangeRequest) -> List[Dict[str, Any]]:
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
    "/ranges/{record_id}",
    response_model=List[RangeResponse],
    summary="Partially update the stored /ranges record",
)
def patch_range(record_id: int, patch: RangePatch) -> List[Dict[str, Any]]:
    stored = ensure_exists(_STORE, record_id)
    updated = {**stored, **patch.model_dump(exclude_unset=True, mode="json")}
    record = RangeRequest.model_validate(updated)
    file_storage.save(_STORE, record_id, record.model_dump(mode="json"))
    return [_build_response(record)]


@router.delete(
    "/ranges/{record_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete the stored /ranges record for the given Id",
)
def delete_range(record_id: int) -> List[Dict[str, Any]]:
    ensure_exists(_STORE, record_id)
    file_storage.delete(_STORE, record_id)
    return [{"deleted": True, "Id": record_id, "store": _STORE}]
