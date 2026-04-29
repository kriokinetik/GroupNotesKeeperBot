"""JSON-backed implementation of the group repository."""

import logging

from errors import (
    ChatNotFoundError,
    GroupAlreadyExistsError,
    GroupLimitExceededError,
    GroupNotFoundError,
)
from models import Group
from .file_store import JsonFileStore
from ..abstracts import AbstractGroupRepository, CID

logger = logging.getLogger(__name__)


class AsyncJsonGroupRepository(JsonFileStore, AbstractGroupRepository):
    """Async JSON repository for groups."""

    async def add(self, chat_id: CID, name: str, limit: int) -> None:
        """Create a new group in storage."""

        async with self._lock:
            data = await self._load()
            chat_data = self._ensure_chat(data, chat_id)
            groups = chat_data.groups

            if self._find_group(chat_data, name) is not None:
                logger.debug("Group already exists chat_id=%s group=%r", chat_id, name)
                raise GroupAlreadyExistsError(name)

            if len(groups) >= limit:
                logger.debug("Group limit exceeded chat_id=%s limit=%s", chat_id, limit)
                raise GroupLimitExceededError(limit)

            groups.append(Group(name=name))
            await self._save(data)
            logger.debug("Group persisted chat_id=%s group=%r", chat_id, name)

    async def get(self, chat_id: CID) -> tuple[str, ...]:
        """Return all group names for the chat."""

        async with self._lock:
            data = await self._load()
        chat_data = self._get_chat(data, chat_id)
        if not chat_data:
            logger.debug(
                "Group lookup failed because chat is missing chat_id=%s", chat_id
            )
            raise ChatNotFoundError(chat_id)

        return tuple(group.name for group in chat_data.groups)

    async def delete(self, chat_id: CID, name: str) -> None:
        """Delete a group from storage."""

        async with self._lock:
            data = await self._load()
            chat_data = self._get_chat(data, chat_id)
            if not chat_data:
                logger.debug(
                    "Group deletion failed because chat is missing chat_id=%s", chat_id
                )
                raise ChatNotFoundError(chat_id)

            group = self._find_group(chat_data, name)
            if group is None:
                logger.debug(
                    "Group deletion failed because group is missing chat_id=%s group=%r",
                    chat_id,
                    name,
                )
                raise GroupNotFoundError(name)

            chat_data.groups.remove(group)
            await self._save(data)
            logger.debug(
                "Group removed from storage chat_id=%s group=%r", chat_id, name
            )

    async def edit(self, chat_id: CID, name: str, new_name: str) -> None:
        """Rename an existing group."""

        async with self._lock:
            data = await self._load()
            chat_data = self._get_chat(data, chat_id)
            if not chat_data:
                raise ChatNotFoundError(chat_id)

            group = self._find_group(chat_data, name)
            if group is None:
                raise GroupNotFoundError(name)

            group.name = new_name
            await self._save(data)
            logger.debug(
                "Group renamed chat_id=%s old=%r new=%r", chat_id, name, new_name
            )

    async def at_limit(self, chat_id: CID, limit: int) -> bool:
        """Return whether the chat already contains the maximum group count."""

        async with self._lock:
            data = await self._load()
        chat_data = self._get_chat(data, chat_id)
        if not chat_data:
            return False

        return len(chat_data.groups) >= limit
