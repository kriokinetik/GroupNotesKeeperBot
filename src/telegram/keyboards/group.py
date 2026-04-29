"""Inline keyboards used by group selection flows."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from repositories import StorageProtocol
from telegram.callbacks import GroupCallback

MAX_GROUP_BUTTON_TEXT_LENGTH = 64


def _group_button_text(name: str) -> str:
    """Return a Telegram-safe button label for a group name."""

    if len(name) <= MAX_GROUP_BUTTON_TEXT_LENGTH:
        return name
    return f"{name[: MAX_GROUP_BUTTON_TEXT_LENGTH - 3]}..."


class GroupKeyboard:
    """Factory for keyboards listing groups from storage."""

    @staticmethod
    async def groups(
        action: str,
        chat_id: int,
        storage: StorageProtocol,
        groups: tuple[str, ...] | None = None,
    ) -> InlineKeyboardMarkup:
        """Return an inline keyboard with chat groups arranged in one column."""

        groups = groups if groups is not None else await storage.group.get(chat_id)
        keyboard = [
            [
                InlineKeyboardButton(
                    text=_group_button_text(name),
                    callback_data=GroupCallback(index=index, action=action).pack(),
                )
            ]
            for index, name in enumerate(groups)
        ]

        return InlineKeyboardMarkup(inline_keyboard=keyboard)
