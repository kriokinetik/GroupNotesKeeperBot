"""Concrete storage facade built from JSON repositories."""

import logging
from pathlib import Path

from repositories import StorageProtocol
from repositories.json import (
    AsyncJsonAdminRepository,
    AsyncJsonGroupRepository,
    AsyncJsonRecordRepository,
)
from repositories.json.file_store import JsonFileStore

logger = logging.getLogger(__name__)


class JsonStorage(StorageProtocol):
    """Repository aggregate backed by the JSON storage file."""

    def __init__(self, path: Path):
        """Create repository instances bound to the same JSON file."""

        logger.debug("Initializing JsonStorage path=%s", path)
        self.admin = AsyncJsonAdminRepository(path)
        self.group = AsyncJsonGroupRepository(path)
        self.record = AsyncJsonRecordRepository(path)


async def ensure_json_storage(path: Path) -> None:
    """Create the JSON storage file eagerly if it does not exist yet."""

    # Startup creates the file eagerly so the bot fails fast on invalid JSON/schema.
    logger.debug("Ensuring JSON storage path=%s", path)
    # noinspection PyProtectedMember
    await JsonFileStore(path)._load()
    logger.debug("JSON storage is ready path=%s", path)
