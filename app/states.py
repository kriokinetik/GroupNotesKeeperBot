from aiogram.fsm.state import StatesGroup, State


class ShameData(StatesGroup):
    shame_id = State()
    message_datetime = State()
    description = State()


class AdminData(StatesGroup):
    edited_description = State()


class UserData(StatesGroup):
    start_message = State()
    message_access = State()
    action = State()
    group_name = State()
