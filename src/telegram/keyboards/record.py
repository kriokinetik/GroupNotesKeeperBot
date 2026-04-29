"""Inline keyboards used while browsing and editing records."""

from aiogram.types import InlineKeyboardMarkup

from .buttons import RecordButtons


class RecordKeyboard:
    """Factory for record history navigation keyboards."""

    @staticmethod
    def navigate(
        *, is_admin: bool = False, can_navigate: bool = True
    ) -> InlineKeyboardMarkup:
        """Build a history navigation keyboard with optional admin actions."""

        keyboard = []

        if can_navigate:
            keyboard.append([RecordButtons.prev(), RecordButtons.next()])

        keyboard.append([RecordButtons.back()])

        if is_admin:
            keyboard.append([RecordButtons.edit(), RecordButtons.delete()])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)
