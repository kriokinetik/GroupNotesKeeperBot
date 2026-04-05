"""Exceptions related to group management."""

from .storage import StorageError


class GroupError(StorageError):
    """Base exception for group-related errors."""


class GroupAlreadyExistsError(GroupError):
    """Raised when a group with the same name already exists."""

    def __init__(self, group_name: str):
        self.group_name = group_name
        super().__init__(group_name)

    def __str__(self) -> str:
        return f'Group "{self.group_name}" already exists.'


class GroupNotFoundError(GroupError):
    """Raised when a requested group does not exist."""

    def __init__(self, group_name: str):
        self.group_name = group_name
        super().__init__(group_name)

    def __str__(self) -> str:
        return f'Group "{self.group_name}" not found.'


class GroupLimitExceededError(GroupError):
    """Raised when the chat reached its configured group limit."""

    def __init__(self, limit: int):
        self.limit = limit
        super().__init__(limit)

    def __str__(self) -> str:
        return f"Maximum number of groups ({self.limit}) exceeded."
