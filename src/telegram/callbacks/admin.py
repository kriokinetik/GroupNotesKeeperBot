"""Callback payloads for admin selection buttons."""

from aiogram.filters.callback_data import CallbackData


class AdminCallback(CallbackData, prefix="admin"):
    """Callback data for selecting a concrete admin user."""

    user_id: int
    action: str
