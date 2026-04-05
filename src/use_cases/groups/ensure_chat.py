"""Use case for ensuring a chat entry exists in storage."""

from repositories import StorageProtocol


class EnsureChatUseCase:
    """Initialize chat storage if it has not been created yet."""

    def __init__(self, storage: StorageProtocol) -> None:
        self.storage = storage

    async def __call__(self, chat_id: int) -> None:
        """Create the chat entry in storage when missing."""

        await self.storage.admin.initialize(chat_id)
