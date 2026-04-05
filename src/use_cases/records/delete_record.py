"""Use case for deleting a record from a group."""

from repositories import StorageProtocol


class DeleteRecordUseCase:
    """Delete a record by index from the target group."""

    def __init__(self, storage: StorageProtocol) -> None:
        self.storage = storage

    async def __call__(self, chat_id: int, group_name: str, record_id: int) -> None:
        """Remove the record from storage."""

        await self.storage.record.delete(chat_id, group_name, record_id)
