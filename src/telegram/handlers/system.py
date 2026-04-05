"""System-level Telegram handlers such as start, help, and global errors."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, ErrorEvent, Message
from aiogram.utils.i18n import gettext as _

from enums import CommandEnum
from errors import StorageDataError

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command(CommandEnum.START))
async def start_message(message: Message) -> None:
    """Send the introductory message for the bot."""

    await message.answer(_("system_start_message"))


@router.message(Command(CommandEnum.HELP))
async def help_message(message: Message) -> None:
    """Send the command reference."""

    await message.reply(_("system_help_message"))


@router.error()
async def handle_storage_error(event: ErrorEvent) -> bool:
    """Handle storage validation failures and unexpected errors."""

    update = event.update
    if isinstance(event.exception, StorageDataError):
        logger.exception("Storage data error", exc_info=event.exception)

        if update.message is not None:
            await update.message.reply(_("system_storage_invalid"))
            return True

        callback: CallbackQuery | None = update.callback_query
        if callback is not None and callback.message is not None:
            await callback.answer()
            await callback.message.reply(_("system_storage_invalid"))
            return True

        return True

    logger.exception("Unhandled Telegram update error", exc_info=event.exception)

    if update.message is not None:
        await update.message.reply("Internal error")
        return True

    callback = update.callback_query
    if callback is not None and callback.message is not None:
        await callback.answer()
        await callback.message.reply("Internal error")
        return True

    return False
