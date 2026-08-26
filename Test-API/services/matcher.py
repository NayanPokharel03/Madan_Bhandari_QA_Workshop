"""Match scoring service.

`score` returns an integer 0..100 and a decision letter. Replace the
scoring implementation without touching the routes.

Decision rules:
    Score >= 85 -> "A"  (accept)
    otherwise   -> "R"  (reject)
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Tuple

ACCEPT_THRESHOLD = 85


def _normalize(value: str) -> str:
    return " ".join(value.upper().split())


def _similarity(a: str, b: str) -> int:
    ratio = SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()
    return round(ratio * 100)


def decide(score: int) -> str:
    return "A" if score >= ACCEPT_THRESHOLD else "R"


def score(data1: str, data2: str, data_type: str) -> Tuple[int, str]:
    """Compute (score, decision) for a single comparison."""
    value = _similarity(data1, data2)
    return value, decide(value)
