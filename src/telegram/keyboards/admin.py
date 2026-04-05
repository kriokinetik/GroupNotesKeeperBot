"""Inline keyboards used by admin management flows."""

from itertools import zip_longest

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from telegram.callbacks import AdminCallback


class AdminKeyboard:
    """Factory for admin selection keyboards."""

    @staticmethod
    def admins(action: str, admins: tuple[tuple[int, str], ...]) -> InlineKeyboardMarkup:
        """Build a keyboard with admin labels arranged in two columns."""

        keyboard: list[list[InlineKeyboardButton]] = []

        it = iter(admins)
        for pair in zip_longest(it, it):
            row = [
                InlineKeyboardButton(
                    text=label,
                    callback_data=AdminCallback(user_id=user_id, action=action).pack(),
                )
                for admin in pair
                if admin is not None
                for user_id, label in [admin]
            ]
            keyboard.append(row)

        return InlineKeyboardMarkup(inline_keyboard=keyboard)
