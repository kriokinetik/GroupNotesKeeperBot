"""Use case for checking whether a chat reached its group limit."""

from repositories import StorageProtocol


class ValidateGroupLimitUseCase:
    """Check if no more groups may be created in the chat."""

    def __init__(self, storage: StorageProtocol) -> None:
        self.storage = storage

    async def __call__(self, chat_id: int, limit: int) -> bool:
        """Return whether the chat already reached the group limit."""

        return await self.storage.group.at_limit(chat_id, limit)
