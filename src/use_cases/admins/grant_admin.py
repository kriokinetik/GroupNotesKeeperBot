"""Use case for granting chat admin access in a chat."""

from repositories import StorageProtocol


class GrantAdminUseCase:
    """Grant chat admin access to a user in a chat."""

    def __init__(self, storage: StorageProtocol) -> None:
        self.storage = storage

    async def __call__(self, chat_id: int, user_id: int) -> None:
        """Persist the user as a chat admin for the chat."""

        await self.storage.admin.add(chat_id, user_id)
