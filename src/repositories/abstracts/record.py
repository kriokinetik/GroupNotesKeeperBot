"""Abstract contract for record persistence."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

CID = int  # Chat ID
RID = int  # Record ID
T = TypeVar("T")  # Generic type for records


class AbstractRecordRepository(ABC, Generic[T]):
    """Abstract repository for CRUD operations on records within groups."""

    @abstractmethod
    async def add(self, chat_id: CID, group_name: str, record: T) -> None:
        """Add a new record to a specific group."""

    @abstractmethod
    async def get(self, chat_id: CID, group_name: str, record_id: RID) -> T | None:
        """Retrieve a record by its ID from a specific group."""

    @abstractmethod
    async def edit(
        self, chat_id: CID, group_name: str, record_id: RID, new_record: T
    ) -> None:
        """Update an existing record in a specific group."""

    @abstractmethod
    async def delete(self, chat_id: CID, group_name: str, record_id: RID) -> None:
        """Delete a record by its ID from a specific group."""

    @abstractmethod
    async def exists(self, chat_id: CID, group_name: str) -> bool:
        """Check if there are any records in a specific group."""

    @abstractmethod
    async def count(self, chat_id: CID, group_name: str) -> int:
        """Return the number of records in a specific group."""
