from aiogram.types import CallbackQuery, Message
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext

from config import admin


class Admin(Filter):  # verification
    async def __call__(self, callback: CallbackQuery) -> bool:
        if callback.from_user.id == admin:
            return True
        else:
            return False


class CallbackAccess(Filter):
    async def __call__(self, callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        if data:
            if data["message_access"] and callback.message.message_id == data["message_access"]:
                return True
            else:
                await callback.answer()
                return False
        else:
            await callback.answer()
            return False


class MessageAccess(Filter):
    async def __call__(self, message: Message, state: FSMContext):
        data = await state.get_data()
        if data:
            if data["message_access"] and message.reply_to_message.message_id == data["message_access"]:
                return True
            else:
                return False
        else:
            return False
