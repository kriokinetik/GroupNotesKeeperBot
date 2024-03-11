from aiogram.fsm.state import StatesGroup, State


class RecordData(StatesGroup):
    record_id = State()
    record_content = State()


class AdminData(StatesGroup):
    edited_record_content = State()


class UserData(StatesGroup):
    initial_message = State()
    interaction_right = State()
    action = State()
    group_name = State()
    admin = State()
