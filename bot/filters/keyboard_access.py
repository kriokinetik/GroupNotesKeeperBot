from aiogram.types import CallbackQuery
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext


class KeyboardAccessFilter(Filter):
    async def __call__(self, callback: CallbackQuery, state: FSMContext) -> bool:
        data = await state.get_data()
        if data and data.get('interaction_right') == callback.message.message_id:
            return True
        await callback.answer('Нет доступа к этому сообщению.')
        return False
