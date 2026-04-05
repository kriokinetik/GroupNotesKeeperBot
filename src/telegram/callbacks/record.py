"""Callback payloads for record history navigation and actions."""

from aiogram.filters.callback_data import CallbackData


class RecordCallback(CallbackData, prefix="record"):
    """Callback data used by record history controls."""

    action: str
    group_name: str | None = None
    record_id: int | None = None
