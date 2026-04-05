"""Callback and flow namespaces used across Telegram interactions."""

from enum import StrEnum


class NamespaceEnum(StrEnum):
    """Stable namespaces for callback payloads and confirmation flows."""

    GROUPS = "groups"
    ADMINS = "admins"
    ADMINS_DELETE = "admins_delete"
    RECORDS_DELETE = "records_delete"
