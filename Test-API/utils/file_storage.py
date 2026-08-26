"""JSON-file backed storage for API requests.

Every endpoint owns a JSON file under `storage/` mapping the record
`Id` (as string) to the exact request payload originally received.
Writes are guarded by a per-file lock so concurrent requests within a
single process cannot corrupt the file.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

_STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

_LOCKS: Dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def _lock_for(name: str) -> threading.Lock:
    with _LOCKS_GUARD:
        lock = _LOCKS.get(name)
        if lock is None:
            lock = threading.Lock()
            _LOCKS[name] = lock
        return lock


def _path_for(name: str) -> Path:
    return _STORAGE_DIR / f"{name}.json"


def _load(name: str) -> Dict[str, Any]:
    path = _path_for(name)
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _dump(name: str, data: Dict[str, Any]) -> None:
    path = _path_for(name)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    tmp.replace(path)


def exists(name: str, record_id: int) -> bool:
    with _lock_for(name):
        return str(record_id) in _load(name)


def save(name: str, record_id: int, payload: Dict[str, Any]) -> None:
    """Persist a single request payload keyed by its `Id`."""
    with _lock_for(name):
        data = _load(name)
        data[str(record_id)] = payload
        _dump(name, data)


def get(name: str, record_id: int) -> Optional[Dict[str, Any]]:
    with _lock_for(name):
        return _load(name).get(str(record_id))


def list_all(name: str) -> List[Dict[str, Any]]:
    with _lock_for(name):
        data = _load(name)
    return sorted(data.values(), key=lambda item: item.get("Id", 0))


def delete(name: str, record_id: int) -> bool:
    with _lock_for(name):
        data = _load(name)
        removed = data.pop(str(record_id), None)
        if removed is None:
            return False
        _dump(name, data)
        return True


def clear(name: str) -> int:
    with _lock_for(name):
        data = _load(name)
        removed = len(data)
        _dump(name, {})
        return removed


def count(name: str) -> int:
    with _lock_for(name):
        return len(_load(name))
