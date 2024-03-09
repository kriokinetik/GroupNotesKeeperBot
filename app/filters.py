from aiogram.types import CallbackQuery, Message, ChatMemberOwner
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext

from config import global_admins


class AdminFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        chat_type = message.chat.type
        chat_id = message.chat.id
        user_id = message.from_user.id

        if chat_type == 'private':
            return True

        if user_id in global_admins:
            return True

        if chat_type == 'group':
            chat_creator = await message.bot.get_chat_member(chat_id, user_id)
            if isinstance(chat_creator, ChatMemberOwner):
                return True

        await message.reply('Недостаточно прав.')
        return False


class CallbackAccessFilter(Filter):
    async def __call__(self, callback: CallbackQuery, state: FSMContext) -> bool:
        data = await state.get_data()
        if data and data.get('interaction_right') == callback.message.message_id:
            return True
        await callback.answer()
        return False


class MessageAccessFilter(Filter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        data = await state.get_data()
        if data and message.reply_to_message:
            if data.get('interaction_right') == message.reply_to_message.message_id:
                return True
        return False
