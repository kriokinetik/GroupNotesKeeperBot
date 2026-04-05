"""Use case for listing chat admins in a chat."""

from repositories import StorageProtocol
from use_cases.groups.ensure_chat import EnsureChatUseCase


class ListAdminsUseCase:
    """Return chat admin IDs for a chat, creating chat storage if needed."""

    def __init__(self, storage: StorageProtocol) -> None:
        self.storage = storage
        self.ensure_chat = EnsureChatUseCase(storage)

    async def __call__(self, chat_id: int) -> tuple[int, ...]:
        """Return all configured chat admin IDs for the chat."""

        await self.ensure_chat(chat_id)
        return await self.storage.admin.get(chat_id)
