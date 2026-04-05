"""Use case for listing groups that may contain records."""

from repositories import StorageProtocol

from use_cases.groups.ensure_chat import EnsureChatUseCase


class ListRecordGroupsUseCase:
    """Return chat groups for record-related flows."""

    def __init__(self, storage: StorageProtocol) -> None:
        self.storage = storage
        self.ensure_chat = EnsureChatUseCase(storage)

    async def __call__(self, chat_id: int) -> tuple[str, ...]:
        """Ensure chat storage exists and then list groups."""

        await self.ensure_chat(chat_id)
        return await self.storage.group.get(chat_id)
