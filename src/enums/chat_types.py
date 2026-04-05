"""Telegram chat type constants used by custom filters."""

from enum import StrEnum


class ChatTypes(StrEnum):
    """Subset of Telegram chat types used in authorization logic."""

    GROUP = "group"
    PRIVATE = "private"
