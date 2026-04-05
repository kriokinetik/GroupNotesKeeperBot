"""Use case for deleting groups from a chat."""

from repositories import StorageProtocol


class DeleteGroupUseCase:
    """Delete an existing group from a chat."""

    def __init__(self, storage: StorageProtocol) -> None:
        self.storage = storage

    async def __call__(self, chat_id: int, group_name: str) -> None:
        """Remove the named group from storage."""

        await self.storage.group.delete(chat_id, group_name)
