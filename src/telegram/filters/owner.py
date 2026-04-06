"""Custom filter that grants access only to configured owners or chat owners."""

import logging

from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Filter
from aiogram.types import CallbackQuery, ChatMemberOwner, Message

from enums import ChatTypes

logger = logging.getLogger(__name__)


class IsOwner(Filter):
    """Allow access only for configured owners or the chat owner."""

    async def __call__(self, event: Message | CallbackQuery, owners: list[int]) -> bool:
        """Check whether the current user should be treated as an owner."""

        message = event if isinstance(event, Message) else event.message
        bot = message.bot
        user = event.from_user

        if message.chat.type == ChatTypes.PRIVATE:
            return False

        if user.id in owners:
            return True

        try:
            chat_member = await bot.get_chat_member(message.chat.id, user.id)
        except TelegramAPIError:
            logger.warning(
                "Owner filter denied because chat member lookup failed chat_id=%s user_id=%s",
                message.chat.id,
                user.id,
            )
            return False
        return isinstance(chat_member, ChatMemberOwner)
