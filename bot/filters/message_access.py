from aiogram.types import Message
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext


class MessageAccessFilter(Filter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        data = await state.get_data()
        if data and message.reply_to_message:
            if data.get('interaction_right') == message.reply_to_message.message_id:
                return True
        return False
