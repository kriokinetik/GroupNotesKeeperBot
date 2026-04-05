"""Transient flow actions used in record-related FSM state."""

from enum import StrEnum


class RecordFlowEnum(StrEnum):
    """Supported record flow modes."""

    ADD = "add"
    HISTORY = "history"
