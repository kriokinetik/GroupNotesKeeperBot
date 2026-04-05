"""Inline keyboards used by group selection flows."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from repositories import StorageProtocol
from telegram.callbacks import GroupCallback


class GroupKeyboard:
    """Factory for keyboards listing groups from storage."""

    @staticmethod
    async def groups(action: str, chat_id: int, storage: StorageProtocol) -> InlineKeyboardMarkup:
        """Return an inline keyboard with chat groups arranged in one column."""
        groups = await storage.group.get(chat_id)
        keyboard = [
            [
                InlineKeyboardButton(
                    text=name,
                    callback_data=GroupCallback(name=name, action=action).pack(),
                )
            ]
            for name in groups
        ]

        return InlineKeyboardMarkup(inline_keyboard=keyboard)
