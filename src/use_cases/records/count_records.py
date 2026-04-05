"""Use case for counting records inside a group."""

from repositories import StorageProtocol


class CountRecordsUseCase:
    """Return the number of records stored in a group."""

    def __init__(self, storage: StorageProtocol) -> None:
        self.storage = storage

    async def __call__(self, chat_id: int, group_name: str) -> int:
        """Count records in the given group."""

        return await self.storage.record.count(chat_id, group_name)
