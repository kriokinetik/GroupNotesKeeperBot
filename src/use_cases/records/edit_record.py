"""Use case for editing the content of an existing record."""

from errors import RecordNotFoundError
from repositories import StorageProtocol


class EditRecordUseCase:
    """Update the content of a stored record."""

    def __init__(self, storage: StorageProtocol) -> None:
        self.storage = storage

    async def __call__(
        self,
        chat_id: int,
        group_name: str,
        record_id: int,
        content: str,
        content_html: str | None,
    ) -> None:
        """Persist the new record content."""

        record = await self.storage.record.get(chat_id, group_name, record_id)
        if record is None:
            raise RecordNotFoundError(record_id)

        record.content = content
        record.content_html = content_html
        await self.storage.record.edit(chat_id, group_name, record_id, record)
