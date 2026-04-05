"""FSM states used by record creation and editing flows."""

from aiogram.fsm.state import StatesGroup, State


class RecordCreate(StatesGroup):
    """State group for creating a record."""

    waiting_content = State()


class RecordEdit(StatesGroup):
    """State group for editing an existing record."""

    waiting_new_content = State()
