"""Exports for project-specific exceptions."""

from .admin import AdminAlreadyExistsError, AdminNotFoundError
from .group import (
    GroupAlreadyExistsError,
    GroupLimitExceededError,
    GroupNameTooLongError,
    GroupNotFoundError,
)
from .storage import ChatNotFoundError, RecordNotFoundError, StorageDataError

__all__ = [
    "AdminAlreadyExistsError",
    "AdminNotFoundError",
    "ChatNotFoundError",
    "RecordNotFoundError",
    "StorageDataError",
    "GroupAlreadyExistsError",
    "GroupLimitExceededError",
    "GroupNameTooLongError",
    "GroupNotFoundError",
]
