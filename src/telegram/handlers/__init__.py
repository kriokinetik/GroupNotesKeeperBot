"""Exports for Telegram routers."""

from .admin import router as admin_router
from .group import router as group_router
from .record import router as record_router
from .system import router as system_router

__all__ = [
    "admin_router",
    "group_router",
    "record_router",
    "system_router",
]
