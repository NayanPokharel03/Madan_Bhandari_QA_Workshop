"""Deterministic range generator.

Emits `{Key, Value}` pairs where `Key` is a lower bound derived from
the input and `Value` is the corresponding upper bound (trailing
pad characters replaced with `Z`). Swap in a production algorithm as
needed; the routes only depend on `generate_ranges`.
"""

from __future__ import annotations

import hashlib
from typing import Dict, List

_KEY_LENGTH = 8
_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$-/><.,"
_LOW_PAD = "$"
_HIGH_PAD = "Z"


def _normalize(data: str) -> str:
    return "".join(ch for ch in data.upper() if ch.isalnum() or ch.isspace()).strip()


def _hash_prefix(data: str, salt: str, prefix_len: int) -> str:
    digest = hashlib.sha256(f"{salt}|{data}".encode("utf-8")).digest()
    return "".join(_ALPHABET[b % len(_ALPHABET)] for b in digest[:prefix_len])


def _range_from_prefix(prefix: str) -> Dict[str, str]:
    prefix = prefix[:_KEY_LENGTH]
    low = (prefix + _LOW_PAD * _KEY_LENGTH)[:_KEY_LENGTH]
    high = (prefix + _HIGH_PAD * _KEY_LENGTH)[:_KEY_LENGTH]
    return {"Key": low, "Value": high}


def generate_ranges(data: str, data_type: str) -> List[Dict[str, str]]:
    """Return a list of `{Key, Value}` ranges for a single input record."""
    normalized = _normalize(data)
    prefixes = [
        _hash_prefix(normalized, salt=f"RANGE-A|{data_type}", prefix_len=3),
        _hash_prefix(normalized, salt=f"RANGE-B|{data_type}", prefix_len=4),
    ]
    ranges: List[Dict[str, str]] = []
    seen: set[str] = set()
    for prefix in prefixes:
        entry = _range_from_prefix(prefix)
        if entry["Key"] in seen:
            continue
        seen.add(entry["Key"])
        ranges.append(entry)
    return ranges
