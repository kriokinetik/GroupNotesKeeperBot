"""Confirmation decisions used by inline confirmation keyboards."""

from enum import StrEnum


class ConfirmEnum(StrEnum):
    """Possible decisions for confirm dialogs."""

    YES = "yes"
    NO = "no"
