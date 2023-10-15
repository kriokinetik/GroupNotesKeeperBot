from aiogram.fsm.state import StatesGroup, State


class ShameData(StatesGroup):
    group_name = State()
    shame_id = State()
    message_datetime = State()
    description = State()
    start_message = State()
