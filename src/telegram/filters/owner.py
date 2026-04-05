"""Custom filter that grants access only to configured owners or chat owners."""

from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Filter
from aiogram.types import CallbackQuery, ChatMemberOwner, Message

from enums import ChatTypes


class IsOwner(Filter):
    """Allow access only for configured owners or the chat owner."""

    async def __call__(self, event: Message | CallbackQuery, owners: list[int]) -> bool:
        """Check whether the current user should be treated as an owner."""

        message = event if isinstance(event, Message) else event.message
        user = event.from_user

        if message.chat.type == ChatTypes.PRIVATE:
            return False

        if user.id in owners:
            return True

        try:
            chat_member = await message.bot.get_chat_member(message.chat.id, user.id)
        except TelegramAPIError:
            return False
        return isinstance(chat_member, ChatMemberOwner)
