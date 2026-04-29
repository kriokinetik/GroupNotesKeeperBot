"""Use case for creating groups inside a chat."""

from errors import GroupNameTooLongError
from repositories import StorageProtocol

MAX_GROUP_NAME_LENGTH = 64


class AddGroupUseCase:
    """Create a new group in a chat."""

    def __init__(self, storage: StorageProtocol) -> None:
        self.storage = storage

    async def __call__(self, chat_id: int, group_name: str, limit: int) -> None:
        """Add a group while respecting the configured group limit."""

        if len(group_name) > MAX_GROUP_NAME_LENGTH:
            raise GroupNameTooLongError(MAX_GROUP_NAME_LENGTH)

        await self.storage.group.add(chat_id, group_name, limit)
