"""Reusable inline keyboards shared across multiple flows."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _

from enums import ConfirmEnum, ManageEnum
from telegram.callbacks import ConfirmCallback
from telegram.callbacks.manage import ManageCallback


class CommonKeyboard:
    """Factory for generic management and confirmation keyboards."""

    @staticmethod
    def confirm(namespace: str, target: str) -> InlineKeyboardMarkup:
        """Build a yes/no confirmation keyboard."""

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_("common_yes"),
                        callback_data=ConfirmCallback(
                            namespace=namespace,
                            target=target,
                            decision=ConfirmEnum.YES,
                        ).pack(),
                    ),
                    InlineKeyboardButton(
                        text=_("common_no"),
                        callback_data=ConfirmCallback(
                            namespace=namespace,
                            target=target,
                            decision=ConfirmEnum.NO,
                        ).pack(),
                    ),
                ]
            ]
        )

    @staticmethod
    def manage(namespace: str) -> InlineKeyboardMarkup:
        """Build a simple add/delete management keyboard."""

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_("common_add"),
                        callback_data=ManageCallback(namespace=namespace, action=ManageEnum.ADD).pack(),
                    ),
                    InlineKeyboardButton(
                        text=_("common_delete"),
                        callback_data=ManageCallback(namespace=namespace, action=ManageEnum.DELETE).pack(),
                    ),
                ]
            ]
        )
