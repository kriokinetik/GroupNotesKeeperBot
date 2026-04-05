"""FSM states used by group management flows."""

from aiogram.fsm.state import State, StatesGroup


class GroupCreate(StatesGroup):
    """State group for creating a new group."""

    waiting_group_name = State()
