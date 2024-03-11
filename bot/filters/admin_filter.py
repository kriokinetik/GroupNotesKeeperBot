from aiogram.types import CallbackQuery, Message, ChatMemberOwner
from aiogram.filters import Filter

from bot.config import global_admins


class AdminFilter(Filter):
    def __init__(self, with_reply: bool) -> None:
        self.with_reply = with_reply

    async def __call__(self, obj: Message | CallbackQuery) -> bool:
        if isinstance(obj, CallbackQuery):
            chat_type = obj.message.chat.type
            chat_id = obj.message.chat.id
        else:
            chat_type = obj.chat.type
            chat_id = obj.chat.id
        user_id = obj.from_user.id
        if chat_type == 'private':
            return True

        if user_id in global_admins:
            return True

        if chat_type == 'group':
            chat_creator = await obj.bot.get_chat_member(chat_id, user_id)
            if isinstance(chat_creator, ChatMemberOwner):
                return True

        if self.with_reply:
            if isinstance(obj, CallbackQuery):
                await obj.message.reply('Недостаточно прав.')
                await obj.answer()
            else:
                await obj.reply('Недостаточно прав.')

        return False
