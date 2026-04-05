"""Exports for concrete storage implementations."""

from .storage import JsonStorage, ensure_json_storage

__all__ = [
    "JsonStorage",
    "ensure_json_storage",
]
