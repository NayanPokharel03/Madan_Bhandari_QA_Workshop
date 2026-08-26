"""Shared enums and helpers used across request/response models."""

from __future__ import annotations

from enum import Enum


class KeyDataType(str, Enum):
    """Allowed `DataType` values for `/keys` and `/ranges`."""

    ADDRESS = "A"
    NAME = "N"


class MatchDataType(str, Enum):
    """Allowed `DataType` values for `/matchscore`."""

    ADDRESS = "A"
    NAME = "Name"
