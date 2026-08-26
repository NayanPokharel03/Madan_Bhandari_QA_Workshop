"""Pydantic models for the `/matchscore` endpoint."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import MatchDataType

MAX_LEN = 200


class MatchScoreRequest(BaseModel):
    """A single comparison record submitted to `POST /matchscore`."""

    Id: int
    Data1: str = Field(..., min_length=1, max_length=MAX_LEN)
    Data2: str = Field(..., min_length=1, max_length=MAX_LEN)
    DataType: MatchDataType

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "Id": 1,
                    "Data1": "Bruce Wayne",
                    "Data2": "Bruce Wayne",
                    "DataType": "Name",
                },
                {
                    "Id": 21,
                    "Data1": "100 Park Avenue",
                    "Data2": "100 Park Ave",
                    "DataType": "A",
                },
            ]
        },
    )


class MatchScorePatch(BaseModel):
    """Partial update payload for `PATCH /matchscore/{id}`."""

    Data1: Optional[str] = Field(None, min_length=1, max_length=MAX_LEN)
    Data2: Optional[str] = Field(None, min_length=1, max_length=MAX_LEN)
    DataType: Optional[MatchDataType] = None

    model_config = ConfigDict(extra="forbid")


class MatchScoreResponse(BaseModel):
    """A single response record returned by `POST /matchscore`."""

    Score: int = Field(..., ge=0, le=100)
    Decision: str = Field(..., description="'A' = accept, 'R' = reject.")
    Id: int
    Data1: str
    Data2: str
    DataType: MatchDataType

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "Score": 100,
                    "Decision": "A",
                    "Id": 1,
                    "Data1": "Bruce Wayne",
                    "Data2": "Bruce Wayne",
                    "DataType": "Name",
                }
            ]
        }
    )
