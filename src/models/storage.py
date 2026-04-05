"""Pydantic models describing the persisted JSON storage schema."""

from datetime import datetime as DateTime, timedelta, timezone

from pydantic import BaseModel, Field, field_validator


class Record(BaseModel):
    """Single note stored inside a group."""

    datetime: DateTime = Field(..., description="Record datetime in ISO 8601 format with timezone offset")
    content: str = Field(..., description="Content of the record")
    content_html: str | None = Field(
        default=None,
        description="Content of the record with Telegram HTML formatting preserved",
    )
    creator: str | None = Field(default=None, description="Creator Telegram username")

    @field_validator("datetime", mode="before")
    @classmethod
    def parse_legacy_datetime(cls, value: object) -> object:
        """Convert legacy naive datetime strings into timezone-aware datetimes."""

        if not isinstance(value, str):
            return value

        formats = (
            "%d.%m.%y %H:%M",
            "%d.%m.%Y %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        )
        tz_moscow = timezone(timedelta(hours=3))

        for fmt in formats:
            try:
                dt = DateTime.strptime(value.strip(), fmt)
                return dt.replace(tzinfo=tz_moscow)
            except ValueError:
                continue

        return value


class Group(BaseModel):
    """Named collection of records inside a chat."""

    name: str = Field(..., description="Group name")
    records: list[Record] = Field(default_factory=list, description="Records assigned to this group")


class ChatData(BaseModel):
    """Per-chat persisted data."""

    admins: list[str] = Field(
        default_factory=list,
        description="Chat administrators as Telegram user ID strings",
    )
    groups: list[Group] = Field(default_factory=list, description="Groups available in the chat")


class StorageData(BaseModel):
    """Top-level JSON storage document."""

    schema_version: int = Field(default=1, description="Storage schema version")
    chats: dict[str, ChatData] = Field(default_factory=dict, description="Chat storage indexed by chat ID")
