"""Application entrypoint for the Telegram bot."""

import asyncio
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.utils.i18n import I18n, gettext as _

from bootstrap import build_dispatcher
from enums import CommandEnum
from migrations import upgrade_storage_if_needed
from settings import JSON_PATH, LOCALES_PATH, configure_logging, settings
from telegram.middlewares import UserLanguageI18nMiddleware

logger = logging.getLogger(__name__)

COMMAND_DESCRIPTIONS = (
    (CommandEnum.HELP, "command_show_help"),
    (CommandEnum.GROUPS, "command_manage_groups"),
    (CommandEnum.ADD, "command_add_entry"),
    (CommandEnum.HISTORY, "command_show_entry_history"),
    (CommandEnum.DELETE, "command_delete_replied_message"),
    (CommandEnum.ADMIN, "command_manage_admins"),
)


def build_commands() -> list[BotCommand]:
    """Build the localized bot command list for the active locale."""

    return [BotCommand(command=command, description=_(description)) for command, description in COMMAND_DESCRIPTIONS]


async def set_commands(bot: Bot, i18n: I18n) -> None:
    """Register localized bot commands for supported locales."""

    logger.debug("Registering localized bot commands")
    with i18n.context():
        for locale in ("en", "ru"):
            with i18n.use_locale(locale):
                commands = build_commands()
            await bot.set_my_commands(commands, language_code=locale)
            logger.debug("Registered bot commands locale=%s count=%s", locale, len(commands))

        with i18n.use_locale(i18n.default_locale):
            default_commands = build_commands()
        await bot.set_my_commands(default_commands)
        logger.debug(
            "Registered default bot commands locale=%s count=%s",
            i18n.default_locale,
            len(default_commands),
        )


async def main() -> None:
    """Configure bot services and start polling."""

    logger.info("Starting bot application")
    storage_upgraded = upgrade_storage_if_needed(JSON_PATH)
    logger.info("Storage migration check completed upgraded=%s path=%s", storage_upgraded, JSON_PATH)

    dp = build_dispatcher()
    i18n = I18n(path=LOCALES_PATH, default_locale=settings.default_language)
    UserLanguageI18nMiddleware(i18n=i18n).setup(dp)
    logger.debug("I18n configured default_locale=%s locales_path=%s", settings.default_language, LOCALES_PATH)

    bot = Bot(
        token=settings.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await set_commands(bot, i18n)
    logger.info("Starting polling")
    await dp.start_polling(bot)


def run() -> None:
    """Run the application using configured logging."""

    configure_logging(settings.log_level)
    asyncio.run(main())


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        logger.info("Polling stopped by keyboard interrupt")
