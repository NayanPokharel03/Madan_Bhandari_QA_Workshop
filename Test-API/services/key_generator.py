"""Deterministic key generator.

Produces fixed-length pseudo-keys derived from the input string. Two
different inputs practically never produce identical keys thanks to a
SHA-256 mix, while the same input always yields the same keys. The
implementation is intentionally isolated so it can be swapped with a
production-grade algorithm (Soundex, NYSIIS, phonex, ...).
"""

from __future__ import annotations

import hashlib
from typing import List

_KEY_LENGTH = 8
_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$-/><.,"
_PAD = "$"


def _normalize(data: str) -> str:
    return "".join(ch for ch in data.upper() if ch.isalnum() or ch.isspace()).strip()


def _hash_key(data: str, salt: str) -> str:
    digest = hashlib.sha256(f"{salt}|{data}".encode("utf-8")).digest()
    chars = [_ALPHABET[b % len(_ALPHABET)] for b in digest[:_KEY_LENGTH]]
    return "".join(chars)


def _prefix_key(data: str) -> str:
    """Build a readable prefix key from the first characters of each token."""
    tokens = _normalize(data).split()
    prefix = "".join(t[0] for t in tokens if t)[:_KEY_LENGTH]
    if not prefix:
        prefix = "X"
    return (prefix + _PAD * _KEY_LENGTH)[:_KEY_LENGTH]


def generate_keys(data: str, data_type: str) -> List[str]:
    """Return a list of unique keys for a single input record."""
    normalized = _normalize(data)
    keys = [
        _prefix_key(normalized),
        _hash_key(normalized, salt=f"KEY|{data_type}"),
    ]
    # Preserve order while removing duplicates.
    seen: set[str] = set()
    unique_keys: List[str] = []
    for key in keys:
        if key not in seen:
            seen.add(key)
            unique_keys.append(key)
    return unique_keys
