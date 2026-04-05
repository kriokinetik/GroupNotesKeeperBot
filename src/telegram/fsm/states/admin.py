"""FSM states used by admin management flows."""

from aiogram.fsm.state import State, StatesGroup


class AdminManage(StatesGroup):
    """State group for adding admins via user input."""

    waiting_target = State()
