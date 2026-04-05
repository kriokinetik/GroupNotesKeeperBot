"""Use case for listing groups available in a chat."""

from repositories import StorageProtocol

from .ensure_chat import EnsureChatUseCase


class ListGroupsUseCase:
    """Return all group names for a chat."""

    def __init__(self, storage: StorageProtocol) -> None:
        self.storage = storage
        self.ensure_chat = EnsureChatUseCase(storage)

    async def __call__(self, chat_id: int) -> tuple[str, ...]:
        """Ensure chat storage exists and then list groups."""

        await self.ensure_chat(chat_id)
        return await self.storage.group.get(chat_id)
