from aiogram.fsm.state import StatesGroup, State


class UserData(StatesGroup):
    initial_message = State()
    interaction_right = State()
    action = State()
    admin = State()
