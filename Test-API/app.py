"""Convenience re-export so `uvicorn app:app` also works."""

from main import app

__all__ = ["app"]
