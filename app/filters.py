from aiogram.types import CallbackQuery, Message
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext

from config import admins


class Admin(Filter):  # verification
    async def __call__(self, message: Message) -> bool:
        if message.from_user.id in admins:
            return True
        else:
            await message.reply(text='Недостаточно прав.')
            return False


class CallbackAccess(Filter):
    async def __call__(self, callback: CallbackQuery, state: FSMContext) -> bool:
        data = await state.get_data()
        if data:
            if data['message_access'] and callback.message.message_id == data['message_access']:
                return True
            else:
                await callback.answer()
                return False
        else:
            await callback.answer()
            return False


class MessageAccess(Filter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        data = await state.get_data()
        if data and message.reply_to_message is not None:
            if data['message_access'] and message.reply_to_message.message_id == data['message_access']:
                return True
            else:
                return False
        else:
            return False
