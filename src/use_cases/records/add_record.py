"""Use case for creating records inside a group."""

from datetime import datetime, timedelta, timezone

from models.storage import Record
from repositories import StorageProtocol


class AddRecordUseCase:
    """Create and persist a timezone-aware record."""

    def __init__(self, storage: StorageProtocol) -> None:
        self.storage = storage

    async def __call__(
        self,
        chat_id: int,
        group_name: str,
        content: str,
        content_html: str | None,
        created_at: datetime,
        creator: str | None = None,
    ) -> None:
        """Persist a new record in the target group."""

        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        record_datetime = created_at.astimezone(timezone(timedelta(hours=3)))
        await self.storage.record.add(
            chat_id,
            group_name,
            Record(
                datetime=record_datetime,
                content=content,
                content_html=content_html,
                creator=creator,
            ),
        )
