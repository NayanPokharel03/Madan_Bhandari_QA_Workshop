"""Pydantic models for the `/keys` endpoint."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import KeyDataType

MAX_LEN = 200


class KeyRequest(BaseModel):
    """A single input record submitted to `POST /keys`."""

    Id: int = Field(..., description="Unique integer identifier for the record.")
    Data: str = Field(
        ...,
        min_length=1,
        max_length=MAX_LEN,
        description="Name or address to hash into keys.",
    )
    DataType: KeyDataType = Field(..., description="'A' for address, 'N' for name.")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"Id": 20, "Data": "42 Elm Street", "DataType": "A"},
                {"Id": 1, "Data": "BRUCE WAYNE", "DataType": "N"},
            ]
        },
    )


class KeyPatch(BaseModel):
    """Partial update payload for `PATCH /keys/{id}`."""

    Data: Optional[str] = Field(None, min_length=1, max_length=MAX_LEN)
    DataType: Optional[KeyDataType] = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"Data": "Bruce W. Wayne"}]},
    )


class KeyResponse(BaseModel):
    """A single response record returned by `POST /keys`."""

    Keys: List[str] = Field(..., description="Generated keys for the input record.")
    Id: int
    Data: str
    DataType: KeyDataType

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "Keys": ["OZKKK$$$", "SC>$-QLA"],
                    "Id": 20,
                    "Data": "42 Elm Street",
                    "DataType": "A",
                }
            ]
        }
    )
