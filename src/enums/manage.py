"""Generic management actions for inline keyboards and callbacks."""

from enum import StrEnum


class ManageEnum(StrEnum):
    """Supported add/delete/select actions."""

    ADD = "add"
    DELETE = "delete"
    SELECT = "select"
