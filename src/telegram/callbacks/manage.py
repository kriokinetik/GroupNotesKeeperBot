"""Callback payloads for generic add/delete management buttons."""

from aiogram.filters.callback_data import CallbackData


class ManageCallback(CallbackData, prefix="manage"):
    """Callback data for management actions within a namespace."""

    namespace: str
    action: str
