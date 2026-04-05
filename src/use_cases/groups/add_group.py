"""Use case for creating groups inside a chat."""

from repositories import StorageProtocol


class AddGroupUseCase:
    """Create a new group in a chat."""

    def __init__(self, storage: StorageProtocol) -> None:
        self.storage = storage

    async def __call__(self, chat_id: int, group_name: str, limit: int) -> None:
        """Add a group while respecting the configured group limit."""

        await self.storage.group.add(chat_id, group_name, limit)
