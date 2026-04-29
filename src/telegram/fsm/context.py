"""Keys used to store temporary Telegram UI state in FSM context."""

from enum import Enum


class InteractionContextKeys(str, Enum):
    """Well-known keys stored in FSM data across handlers."""

    INTERACTION_IDS = "interaction_ids"
    ACTION = "action"
    ADMIN = "admin"
    GROUPS = "groups"
    GROUP_NAME = "group_name"
    RECORD_ID = "record_id"
    VIEW_MESSAGE_ID = "view_message_id"
