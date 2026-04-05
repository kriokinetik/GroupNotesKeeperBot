"""Use case for revoking chat admin access in a chat."""

from repositories import StorageProtocol


class RevokeAdminUseCase:
    """Remove a user from the chat's admin list."""

    def __init__(self, storage: StorageProtocol) -> None:
        self.storage = storage

    async def __call__(self, chat_id: int, user_id: int) -> None:
        """Persist removal of the user from chat admins."""

        await self.storage.admin.remove(chat_id, user_id)
