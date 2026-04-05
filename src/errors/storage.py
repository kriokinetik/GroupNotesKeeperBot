"""Exceptions raised by the storage and repository layers."""


class StorageError(Exception):
    """Base exception for storage-related errors."""


class StorageDataError(StorageError):
    """Raised when the JSON storage file cannot be parsed or validated."""

    def __init__(self, path: str, reason: str):
        self.path = path
        self.reason = reason
        super().__init__(path, reason)

    def __str__(self) -> str:
        return f"Storage data at {self.path} is invalid: {self.reason}."


class ChatNotFoundError(StorageError):
    """Raised when no storage entry exists for the requested chat."""

    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        super().__init__(chat_id)

    def __str__(self) -> str:
        return f"No data found for chat {self.chat_id}."


class RecordNotFoundError(StorageError):
    """Raised when a record index does not exist in a group."""

    def __init__(self, record_id: int):
        self.record_id = record_id
        super().__init__(record_id)

    def __str__(self) -> str:
        return f"No record found at index {self.record_id}."
