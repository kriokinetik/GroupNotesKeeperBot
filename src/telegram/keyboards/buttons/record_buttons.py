"""Low-level button factory for record history controls."""

from aiogram.types import InlineKeyboardButton
from aiogram.utils.i18n import gettext as _

from enums import RecordEnum
from telegram.callbacks import RecordCallback


class RecordButtons:
    """Factory for individual record-related inline buttons."""

    @staticmethod
    def prev() -> InlineKeyboardButton:
        """Return the button for navigating to the previous record."""

        return InlineKeyboardButton(text="<", callback_data=RecordCallback(action=RecordEnum.PREV).pack())

    @staticmethod
    def next() -> InlineKeyboardButton:
        """Return the button for navigating to the next record."""

        return InlineKeyboardButton(text=">", callback_data=RecordCallback(action=RecordEnum.NEXT).pack())

    @staticmethod
    def back() -> InlineKeyboardButton:
        """Return the back button."""

        return InlineKeyboardButton(
            text=_("common_back"),
            callback_data=RecordCallback(action=RecordEnum.BACK).pack(),
        )

    @staticmethod
    def edit() -> InlineKeyboardButton:
        """Return the edit button."""

        return InlineKeyboardButton(
            text=_("common_edit"),
            callback_data=RecordCallback(action=RecordEnum.EDIT).pack(),
        )

    @staticmethod
    def delete() -> InlineKeyboardButton:
        """Return the delete button."""

        return InlineKeyboardButton(
            text=_("common_delete"),
            callback_data=RecordCallback(action=RecordEnum.DELETE).pack(),
        )
