"""Custom filter that grants access to chat admins and configured owners."""

from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Filter
from aiogram.types import CallbackQuery, ChatMemberOwner, Message

from enums import ChatTypes
from errors import ChatNotFoundError
from repositories import StorageProtocol


class IsAdmin(Filter):
    """Allow access for chat owners, configured owners, and chat admins."""

    async def __call__(
        self,
        event: Message | CallbackQuery,
        storage: StorageProtocol,
        owners: list[int],
    ) -> bool:
        """Check whether the current user may perform admin-level actions."""

        message = event if isinstance(event, Message) else event.message
        user = event.from_user

        if message.chat.type == ChatTypes.PRIVATE:
            return True

        if user.id in owners:
            return True

        try:
            chat_member = await message.bot.get_chat_member(message.chat.id, user.id)
        except TelegramAPIError:
            return False
        if isinstance(chat_member, ChatMemberOwner):
            return True

        try:
            admins = await storage.admin.get(message.chat.id)
        except ChatNotFoundError:
            return False

        return user.id in admins
