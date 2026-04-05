"""JSON-backed implementation of the record repository."""

import logging

from errors import ChatNotFoundError, GroupNotFoundError, RecordNotFoundError
from models.storage import Record
from .file_store import JsonFileStore
from ..abstracts import AbstractRecordRepository, CID, RID

logger = logging.getLogger(__name__)


class AsyncJsonRecordRepository(JsonFileStore, AbstractRecordRepository[Record]):
    """Async JSON repository for records."""

    async def add(self, chat_id: CID, group_name: str, record: Record) -> None:
        """Append a record to a group."""

        async with self._lock:
            data = await self._load()
            chat_data = self._get_chat(data, chat_id)
            if not chat_data:
                logger.debug("Record creation failed because chat is missing chat_id=%s", chat_id)
                raise ChatNotFoundError(chat_id)

            group = self._find_group(chat_data, group_name)
            if group is None:
                logger.debug(
                    "Record creation failed because group is missing chat_id=%s group=%r",
                    chat_id,
                    group_name,
                )
                raise GroupNotFoundError(group_name)

            records = group.records
            records.append(record)
            await self._save(data)
            logger.debug(
                "Record persisted chat_id=%s group=%r record_id=%s",
                chat_id,
                group_name,
                len(records) - 1,
            )

    async def get(self, chat_id: CID, group_name: str, record_id: RID) -> Record | None:
        """Return a record by index or ``None`` if it does not exist."""

        data = await self._load()
        chat_data = self._get_chat(data, chat_id)
        if not chat_data:
            logger.debug("Record lookup skipped because chat is missing chat_id=%s", chat_id)
            return None

        group = self._find_group(chat_data, group_name)
        if group is None:
            logger.debug(
                "Record lookup skipped because group is missing chat_id=%s group=%r",
                chat_id,
                group_name,
            )
            return None

        records = group.records
        if not 0 <= record_id < len(records):
            logger.debug(
                "Record lookup skipped because index is out of range chat_id=%s group=%r record_id=%s",
                chat_id,
                group_name,
                record_id,
            )
            return None

        return records[record_id]

    async def edit(self, chat_id: CID, group_name: str, record_id: RID, record: Record) -> None:
        """Update record content by index."""

        async with self._lock:
            data = await self._load()
            chat_data = self._get_chat(data, chat_id)
            if not chat_data:
                logger.debug("Record edit failed because chat is missing chat_id=%s", chat_id)
                raise ChatNotFoundError(chat_id)

            group = self._find_group(chat_data, group_name)
            if group is None:
                logger.debug(
                    "Record edit failed because group is missing chat_id=%s group=%r",
                    chat_id,
                    group_name,
                )
                raise GroupNotFoundError(group_name)

            records = group.records
            if not 0 <= record_id < len(records):
                logger.debug(
                    "Record edit failed because index is out of range chat_id=%s group=%r record_id=%s",
                    chat_id,
                    group_name,
                    record_id,
                )
                raise RecordNotFoundError(record_id)
            records[record_id] = record
            await self._save(data)
            logger.debug(
                "Record content updated chat_id=%s group=%r record_id=%s",
                chat_id,
                group_name,
                record_id,
            )

    async def delete(self, chat_id: CID, group_name: str, record_id: RID) -> None:
        """Delete a record by index."""

        async with self._lock:
            data = await self._load()
            chat_data = self._get_chat(data, chat_id)
            if not chat_data:
                logger.debug("Record deletion failed because chat is missing chat_id=%s", chat_id)
                raise ChatNotFoundError(chat_id)

            group = self._find_group(chat_data, group_name)
            if group is None:
                logger.debug(
                    "Record deletion failed because group is missing chat_id=%s group=%r",
                    chat_id,
                    group_name,
                )
                raise GroupNotFoundError(group_name)

            records = group.records
            if not 0 <= record_id < len(records):
                logger.debug(
                    "Record deletion failed because index is out of range chat_id=%s group=%r record_id=%s",
                    chat_id,
                    group_name,
                    record_id,
                )
                raise RecordNotFoundError(record_id)
            records.pop(record_id)
            await self._save(data)
            logger.debug(
                "Record removed chat_id=%s group=%r record_id=%s",
                chat_id,
                group_name,
                record_id,
            )

    async def exists(self, chat_id: CID, group_name: str) -> bool:
        """Return whether a group contains at least one record."""

        return await self.count(chat_id, group_name) > 0

    async def count(self, chat_id: CID, group_name: str) -> int:
        """Return the number of records in a group."""

        data = await self._load()
        chat_data = self._get_chat(data, chat_id)
        if not chat_data:
            return 0

        group = self._find_group(chat_data, group_name)
        if group is None:
            return 0

        return len(group.records)
