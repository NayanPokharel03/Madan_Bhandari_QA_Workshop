"""Routes for `/keys` (POST, GET all, GET/PUT/PATCH/DELETE by Id)."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, status

from models.keys import KeyPatch, KeyRequest, KeyResponse
from services.key_generator import generate_keys
from utils import file_storage
from utils.validators import (
    ensure_exists,
    ensure_ids_are_new_or_identical,
    ensure_no_duplicate_content,
    ensure_non_empty,
    ensure_unique_ids,
)

router = APIRouter(tags=["keys"])
_STORE = "keys"


def _build_response(record: KeyRequest) -> Dict[str, Any]:
    return {
        "Keys": generate_keys(record.Data, record.DataType.value),
        "Id": record.Id,
        "Data": record.Data,
        "DataType": record.DataType.value,
    }


@router.post(
    "/keys",
    response_model=List[KeyResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Generate keys for one or more records",
)
def create_keys(records: List[KeyRequest]) -> List[Dict[str, Any]]:
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
    "/keys",
    response_model=List[KeyRequest],
    summary="List every stored /keys request",
)
def list_keys() -> List[Dict[str, Any]]:
    return file_storage.list_all(_STORE)


@router.get(
    "/keys/{record_id}",
    response_model=List[KeyRequest],
    summary="Retrieve the stored /keys request for the given Id",
)
def get_key(record_id: int) -> List[Dict[str, Any]]:
    return [ensure_exists(_STORE, record_id)]


@router.put(
    "/keys/{record_id}",
    response_model=List[KeyResponse],
    summary="Replace the stored /keys record for the given Id",
)
def replace_key(record_id: int, record: KeyRequest) -> List[Dict[str, Any]]:
    ensure_exists(_STORE, record_id)
    if record.Id != record_id:
        from utils.errors import APIError

        raise APIError(
            "Path Id and body Id must match.",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"path_id": record_id, "body_id": record.Id},
        )
    file_storage.save(_STORE, record_id, record.model_dump(mode="json"))
    return [_build_response(record)]


@router.patch(
    "/keys/{record_id}",
    response_model=List[KeyResponse],
    summary="Partially update the stored /keys record",
)
def patch_key(record_id: int, patch: KeyPatch) -> List[Dict[str, Any]]:
    stored = ensure_exists(_STORE, record_id)
    updated = {**stored, **patch.model_dump(exclude_unset=True, mode="json")}
    record = KeyRequest.model_validate(updated)
    file_storage.save(_STORE, record_id, record.model_dump(mode="json"))
    return [_build_response(record)]


@router.delete(
    "/keys/{record_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete the stored /keys record for the given Id",
)
def delete_key(record_id: int) -> List[Dict[str, Any]]:
    ensure_exists(_STORE, record_id)
    file_storage.delete(_STORE, record_id)
    return [{"deleted": True, "Id": record_id, "store": _STORE}]
