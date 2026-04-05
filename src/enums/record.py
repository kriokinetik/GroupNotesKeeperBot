"""Actions available while navigating record history."""

from enum import StrEnum


class RecordEnum(StrEnum):
    """History navigation and record management actions."""

    PREV = "prev"
    NEXT = "next"
    BACK = "back"
    EDIT = "edit"
    DELETE = "delete"
