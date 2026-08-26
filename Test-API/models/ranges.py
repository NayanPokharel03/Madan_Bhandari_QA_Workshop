"""Pydantic models for the `/ranges` endpoint."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import KeyDataType

MAX_LEN = 200


class RangeEntry(BaseModel):
    """A single `{Key, Value}` range pair."""

    Key: str = Field(..., description="Lower bound of the range.")
    Value: str = Field(..., description="Upper bound of the range.")


class RangeRequest(BaseModel):
    """A single input record submitted to `POST /ranges`."""

    Id: int = Field(..., description="Unique integer identifier for the record.")
    Data: str = Field(..., min_length=1, max_length=MAX_LEN)
    DataType: KeyDataType

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"Id": 1, "Data": "BRUCE WAYNE", "DataType": "N"}]
        },
    )


class RangePatch(BaseModel):
    """Partial update payload for `PATCH /ranges/{id}`."""

    Data: Optional[str] = Field(None, min_length=1, max_length=MAX_LEN)
    DataType: Optional[KeyDataType] = None

    model_config = ConfigDict(extra="forbid")


class RangeResponse(BaseModel):
    """A single response record returned by `POST /ranges`."""

    Ranges: List[RangeEntry]
    Id: int
    Data: str
    DataType: KeyDataType

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "Ranges": [
                        {"Key": "ZI/$$$$$", "Value": "ZI//ZZZZ"},
                        {"Key": "LXYC$$$$", "Value": "LXYFZZZZ"},
                    ],
                    "Id": 1,
                    "Data": "BRUCE WAYNE",
                    "DataType": "N",
                }
            ]
        }
    )
