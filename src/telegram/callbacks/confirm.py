"""Callback payloads for generic confirmation dialogs."""

from aiogram.filters.callback_data import CallbackData


class ConfirmCallback(CallbackData, prefix="confirm"):
    """Callback factory for Yes/No buttons with context for deletion."""

    namespace: str
    target: str
    decision: str
