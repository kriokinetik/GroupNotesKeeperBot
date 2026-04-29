"""Helpers for loading and saving the JSON storage file."""

import asyncio
import json
import logging
from pathlib import Path

import aiofiles
from pydantic import ValidationError

from errors import StorageDataError
from models import ChatData, Group, StorageData

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1


class JsonFileStore:
    """Base class with common JSON file access helpers for repositories."""

    _locks: dict[str, asyncio.Lock] = {}

    def __init__(self, path: Path):
        self.path = path
        self._lock = self._locks.setdefault(str(path.resolve()), asyncio.Lock())

    @staticmethod
    def _default_root() -> StorageData:
        """Return an empty storage document for the current schema version."""

        return StorageData(schema_version=SCHEMA_VERSION)

    async def _save(self, data: StorageData) -> None:
        """Persist storage data without replacing the mounted file."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data.model_dump(mode="json"), ensure_ascii=False, indent=4)
        mode = "r+" if self.path.exists() else "w+"
        async with aiofiles.open(self.path, mode=mode, encoding="utf-8") as f:
            await f.seek(0)
            await f.write(payload)
            await f.write("\n")
            await f.truncate()
            await f.flush()

    async def _load(self) -> StorageData:
        """Load and validate the JSON storage file."""

        if not self.path.exists():
            data = self._default_root()
            await self._save(data)
            return data

        async with aiofiles.open(self.path, encoding="utf-8-sig") as f:
            content = await f.read()
            if not content.strip():
                logger.error("Storage file is empty path=%s", self.path)
                raise StorageDataError(str(self.path), "file is empty")
            try:
                raw_data = json.loads(content)
            except json.JSONDecodeError:
                logger.exception(
                    "Storage file contains invalid JSON path=%s", self.path
                )
                raise StorageDataError(str(self.path), "invalid JSON")

        if not isinstance(raw_data, dict):
            logger.error("Storage root is not an object path=%s", self.path)
            raise StorageDataError(str(self.path), "root is not a JSON object")

        try:
            data = StorageData.model_validate(raw_data)
        except ValidationError:
            logger.exception("Storage file does not match schema path=%s", self.path)
            raise StorageDataError(str(self.path), "schema validation failed")

        if data.schema_version != SCHEMA_VERSION:
            logger.error(
                "Storage schema version mismatch path=%s expected=%s actual=%s",
                self.path,
                SCHEMA_VERSION,
                data.schema_version,
            )
            raise StorageDataError(
                str(self.path),
                f"expected schema version {SCHEMA_VERSION}, got {data.schema_version}",
            )

        return data

    @staticmethod
    def _get_chats(data: StorageData) -> dict[str, ChatData]:
        """Return the mutable chat mapping from the storage document."""

        return data.chats

    def _get_chat(self, data: StorageData, chat_id: int) -> ChatData | None:
        """Return chat data if it already exists in storage."""

        chats = self._get_chats(data)
        return chats.get(str(chat_id))

    def _ensure_chat(self, data: StorageData, chat_id: int) -> ChatData:
        """Return existing chat data or create an empty chat entry."""

        chats = self._get_chats(data)
        return chats.setdefault(str(chat_id), ChatData())

    @staticmethod
    def _find_group(chat_data: ChatData, group_name: str) -> Group | None:
        """Find a group by name in the given chat data."""

        groups = chat_data.groups
        for group in groups:
            if group.name == group_name:
                return group
        return None
