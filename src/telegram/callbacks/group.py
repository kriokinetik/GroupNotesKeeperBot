"""Callback payloads for group-related inline buttons."""

from aiogram.filters.callback_data import CallbackData


class GroupCallback(CallbackData, prefix="group"):
    """Callback data for selecting a group and requested action."""

    name: str
    action: str
