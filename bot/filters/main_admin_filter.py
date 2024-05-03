from aiogram.types import Message, ChatMemberOwner
from aiogram.filters import Filter

from config import global_admins


class MainAdminFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        chat_type = message.chat.type
        chat_id = message.chat.id
        user_id = message.from_user.id

        if chat_type == 'private':
            await message.reply('Команда не доступна в приватных диалогах.')
            return False

        if user_id in global_admins:
            return True

        if chat_type == 'group':
            chat_creator = await message.bot.get_chat_member(chat_id, user_id)
            if isinstance(chat_creator, ChatMemberOwner):
                return True

        await message.reply('Недостаточно прав.')
        return False
