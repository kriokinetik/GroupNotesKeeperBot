"""JSON-backed implementation of the admin repository."""

import logging

from errors import AdminAlreadyExistsError, AdminNotFoundError, ChatNotFoundError
from .file_store import JsonFileStore
from ..abstracts import AbstractAdminRepository, CID, UID

logger = logging.getLogger(__name__)


class AsyncJsonAdminRepository(JsonFileStore, AbstractAdminRepository):
    """Async JSON repository for managing chat administrators."""

    async def add(self, chat_id: CID, user_id: UID) -> None:
        """Persist a new chat admin for the chat."""

        async with self._lock:
            data = await self._load()
            chat_data = self._ensure_chat(data, chat_id)
            admins = chat_data.admins
            user_id_str = str(user_id)

            if user_id_str in admins:
                logger.debug("Admin already exists chat_id=%s user_id=%s", chat_id, user_id)
                raise AdminAlreadyExistsError(user_id)

            admins.append(user_id_str)
            await self._save(data)
            logger.debug("Admin persisted chat_id=%s user_id=%s", chat_id, user_id)

    async def remove(self, chat_id: CID, user_id: UID) -> None:
        """Remove a chat admin from the chat."""

        async with self._lock:
            data = await self._load()
            chat_data = self._get_chat(data, chat_id)

            if not chat_data:
                logger.debug("Admin removal failed because chat is missing chat_id=%s", chat_id)
                raise ChatNotFoundError(chat_id)

            admins = chat_data.admins
            user_id_str = str(user_id)

            if user_id_str not in admins:
                logger.debug(
                    "Admin removal failed because user is missing chat_id=%s user_id=%s",
                    chat_id,
                    user_id,
                )
                raise AdminNotFoundError(user_id)

            admins.remove(user_id_str)
            await self._save(data)
            logger.debug("Admin removed chat_id=%s user_id=%s", chat_id, user_id)

    async def get(self, chat_id: CID) -> tuple[UID]:
        """Return all chat admin IDs for the chat."""

        data = await self._load()
        chat_data = self._get_chat(data, chat_id)

        if not chat_data:
            logger.debug("Admin lookup failed because chat is missing chat_id=%s", chat_id)
            raise ChatNotFoundError(chat_id)

        return tuple(int(admin_id) for admin_id in chat_data.admins)

    async def initialize(self, chat_id: CID) -> None:
        """Ensure the chat exists in storage."""

        async with self._lock:
            data = await self._load()
            existed = self._get_chat(data, chat_id) is not None
            self._ensure_chat(data, chat_id)
            await self._save(data)
            if not existed:
                logger.debug("Chat storage initialized chat_id=%s", chat_id)
