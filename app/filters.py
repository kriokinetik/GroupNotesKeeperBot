from aiogram.types import CallbackQuery, Message
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext

from config import admins


class GlobalAdminFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        if message.from_user.id in admins:
            return True
        await message.reply('Недостаточно прав.')
        return False


# class ChatOwnerFilter(Filter):


class DirectMessageFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        if message.from_user.id == message.chat.id:
            return True
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
