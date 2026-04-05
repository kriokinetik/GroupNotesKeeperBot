"""Use case for reading a record from a group."""

from models.storage import Record
from repositories import StorageProtocol


class GetRecordUseCase:
    """Fetch a record by index from the target group."""

    def __init__(self, storage: StorageProtocol) -> None:
        self.storage = storage

    async def __call__(self, chat_id: int, group_name: str, record_id: int) -> Record | None:
        """Return the record or ``None`` when it does not exist."""

        return await self.storage.record.get(chat_id, group_name, record_id)
