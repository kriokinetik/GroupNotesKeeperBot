"""Exceptions related to chat admin management."""


class AdminError(Exception):
    """Base exception for admin-related errors."""


class AdminAlreadyExistsError(AdminError):
    """Raised when a user is already present in the chat admin list."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User {user_id} is already an administrator.")


class AdminNotFoundError(AdminError):
    """Raised when a user is missing from the chat admin list."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User {user_id} is not an administrator.")
