from aiogram.fsm.state import StatesGroup, State


class RecordData(StatesGroup):
    group_name = State()
    record_id = State()
    record_content = State()
    edited_record_content = State()
