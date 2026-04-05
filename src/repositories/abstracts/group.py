"""Abstract contract for group persistence."""

from abc import ABC, abstractmethod

CID = int  # Chat ID


class AbstractGroupRepository(ABC):
    """Abstract repository for managing groups within a chat."""

    @abstractmethod
    async def add(self, chat_id: CID, name: str, limit: int) -> None:
        """Create a new group in the chat."""

    @abstractmethod
    async def delete(self, chat_id: CID, name: str) -> None:
        """Delete a group by its name."""

    @abstractmethod
    async def get(self, chat_id: CID) -> tuple[str]:
        """List all groups in a chat."""

    @abstractmethod
    async def edit(self, chat_id: CID, name: str, new_name: str) -> None:
        """Edit the name or data of a group."""

    @abstractmethod
    async def at_limit(self, chat_id: CID, limit: int) -> bool:
        """Return whether the chat has already reached the group limit."""
