"""Custom filter for binding replies and callbacks to an active FSM interaction."""

from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message


class IsInteractionOwner(Filter):
    """
    Allows interaction only with messages bound to the current FSM session.

    For message-based flows, the user must reply to one of the tracked bot messages.
    For callback-based flows, the callback must come from one of the tracked bot messages.
    """

    async def __call__(self, event: Message | CallbackQuery, state: FSMContext) -> bool:
        """Validate that the event belongs to the currently tracked interaction."""

        data = await state.get_data()
        raw_interaction_ids = data.get("interaction_ids")
        if raw_interaction_ids is None:
            return False

        if isinstance(raw_interaction_ids, (list, tuple, set)):
            interaction_ids = set(raw_interaction_ids)
        else:
            interaction_ids = {raw_interaction_ids}

        if isinstance(event, Message):
            return bool(event.reply_to_message and event.reply_to_message.message_id in interaction_ids)

        if isinstance(event, CallbackQuery):
            return event.message.message_id in interaction_ids

        return False
