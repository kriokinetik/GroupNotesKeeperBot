"""Abstract contract for chat admin persistence."""

from abc import ABC, abstractmethod

CID = int  # Chat ID
UID = int  # User ID


class AbstractAdminRepository(ABC):
    """Abstract repository for managing chat administrators."""

    @abstractmethod
    async def add(self, chat_id: CID, user_id: UID) -> None:
        """Add a user as an administrator of a chat."""

    @abstractmethod
    async def remove(self, chat_id: CID, user_id: UID) -> None:
        """Remove a user from the chat administrators."""

    @abstractmethod
    async def get(self, chat_id: CID) -> tuple[UID]:
        """Return a list of all administrators in a chat."""

    @abstractmethod
    async def initialize(self, chat_id: CID) -> None:
        """Initialize the chat."""
