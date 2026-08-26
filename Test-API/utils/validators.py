"""Request-level validators that Pydantic cannot express directly."""

from __future__ import annotations

from typing import Any, Iterable, List

from fastapi import status

from utils import file_storage
from utils.errors import APIError

MAX_STRING_LENGTH = 200


def ensure_non_empty(items: List[Any]) -> None:
    if not items:
        raise APIError(
            "Request body must be a non-empty JSON array.",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"received_items": 0},
        )


def ensure_unique_ids(ids: Iterable[int]) -> None:
    seen: set[int] = set()
    duplicates: set[int] = set()
    for record_id in ids:
        if record_id in seen:
            duplicates.add(record_id)
        seen.add(record_id)
    if duplicates:
        raise APIError(
            "Duplicate Ids within request body.",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"duplicate_ids": sorted(duplicates)},
        )


def ensure_ids_are_new(store_name: str, ids: Iterable[int]) -> None:
    conflicting = [rid for rid in ids if file_storage.exists(store_name, rid)]
    if conflicting:
        raise APIError(
            f"Id(s) already stored for '{store_name}'.",
            status_code=status.HTTP_409_CONFLICT,
            details={"conflicting_ids": sorted(conflicting)},
        )


def ensure_ids_are_new_or_identical(
    store_name: str, records: List[Any], content_keys: Iterable[str]
) -> None:
    """Idempotent POST guard: allow re-posting an existing Id only when every
    business field in `content_keys` matches the stored payload exactly; raise
    409 when the Id exists with different content."""
    keys = tuple(content_keys)
    conflicts: list[dict] = []
    for record in records:
        stored = file_storage.get(store_name, record.Id)
        if stored is None:
            continue
        mismatched: dict[str, dict] = {}
        for key in keys:
            new_value = getattr(record, key, None)
            # Unwrap Enum members so their JSON value is compared, not the object.
            new_value = getattr(new_value, "value", new_value)
            stored_value = stored.get(key)
            if stored_value != new_value:
                mismatched[key] = {"stored": stored_value, "incoming": new_value}
        if mismatched:
            conflicts.append({"id": record.Id, "fields": mismatched})
    if conflicts:
        raise APIError(
            f"Id(s) already stored for '{store_name}' with different content.",
            status_code=status.HTTP_409_CONFLICT,
            details={"conflicts": conflicts},
        )


def ensure_string_length(field: str, value: str) -> None:
    if len(value) > MAX_STRING_LENGTH:
        raise APIError(
            f"'{field}' exceeds maximum length of {MAX_STRING_LENGTH}.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field": field, "length": len(value), "max": MAX_STRING_LENGTH},
        )


def ensure_no_duplicate_content(records: List[Any], keys: Iterable[str]) -> None:
    """Fail when two records in the same request carry identical business fields."""
    seen: dict[tuple, int] = {}
    duplicates: list[dict] = []
    for record in records:
        signature = []
        for key in keys:
            value = getattr(record, key, None)
            if isinstance(value, str):
                signature.append(value.strip().upper())
            else:
                signature.append(value)
        sig_tuple = tuple(signature)
        if sig_tuple in seen:
            duplicates.append(
                {"first_id": seen[sig_tuple], "duplicate_id": record.Id}
            )
        else:
            seen[sig_tuple] = record.Id
    if duplicates:
        raise APIError(
            "Duplicate records detected (same content, different Ids).",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"duplicates": duplicates},
        )


def ensure_exists(store_name: str, record_id: int) -> dict:
    stored = file_storage.get(store_name, record_id)
    if stored is None:
        raise APIError(
            f"No stored '{store_name}' request for Id={record_id}.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"id": record_id, "store": store_name},
        )
    return stored
