"""I18n middleware that resolves locale from the Telegram user profile."""

from aiogram.types import TelegramObject, User
from aiogram.utils.i18n.middleware import I18nMiddleware


class UserLanguageI18nMiddleware(I18nMiddleware):
    """Select locale from ``event_from_user.language_code`` when available."""

    async def get_locale(self, event: TelegramObject, data: dict) -> str:
        """Return a supported locale or fall back to the configured default."""

        event_from_user: User | None = data.get("event_from_user")
        if event_from_user is None or not event_from_user.language_code:
            return self.i18n.default_locale

        locale = event_from_user.language_code.lower().split("-")[0]
        if locale not in self.i18n.available_locales:
            return self.i18n.default_locale

        return locale
