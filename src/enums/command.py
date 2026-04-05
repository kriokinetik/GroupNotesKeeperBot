"""Telegram bot command names."""

from enum import StrEnum


class CommandEnum(StrEnum):
    """Supported bot commands."""

    START = "start"
    HELP = "help"
    GROUPS = "groups"
    ADD = "add"
    HISTORY = "history"
    DELETE = "delete"
    ADMIN = "admin"
