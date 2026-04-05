"""Schema migration: v0 legacy JSON -> v1 storage document."""

from datetime import datetime, timedelta, timezone, tzinfo
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from migrations.base import Migration

FALLBACK_OFFSETS = {
    "Europe/Moscow": timezone(timedelta(hours=3)),
}


def _resolve_timezone(timezone_name: str) -> tzinfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        if timezone_name in FALLBACK_OFFSETS:
            return FALLBACK_OFFSETS[timezone_name]
        raise


def _convert_to_iso(value: Any, timezone_info: tzinfo) -> Any:
    if not isinstance(value, str):
        return value

    raw = value.strip()
    formats = (
        "%d.%m.%y %H:%M",
        "%d.%m.%Y %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    )

    for date_format in formats:
        try:
            parsed = datetime.strptime(raw, date_format)
            return parsed.replace(tzinfo=timezone_info).isoformat()
        except ValueError:
            continue

    return raw


def _convert_to_legacy(value: Any, timezone_info: tzinfo) -> Any:
    if not isinstance(value, str):
        return value

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone_info)
    else:
        parsed = parsed.astimezone(timezone_info)
    return parsed.strftime("%d.%m.%y %H:%M")


def upgrade(payload: dict[str, Any], timezone_name: str) -> dict[str, Any]:
    """Upgrade storage payload from schema v0 to schema v1."""

    timezone_info = _resolve_timezone(timezone_name)
    new_chats: dict[str, dict[str, Any]] = {}

    for chat_id, chat_data in payload.items():
        chat_payload = chat_data if isinstance(chat_data, dict) else {}
        admins = [str(admin_id) for admin_id in chat_payload.get("admins", [])]
        old_records = chat_payload.get("records", {})
        groups: list[dict[str, Any]] = []

        if isinstance(old_records, dict):
            for group_name, records_list in old_records.items():
                migrated_records: list[dict[str, Any]] = []
                if isinstance(records_list, list):
                    for record in records_list:
                        record_payload = record if isinstance(record, dict) else {}
                        migrated_records.append(
                            {
                                "datetime": _convert_to_iso(
                                    record_payload.get("datetime", ""),
                                    timezone_info,
                                ),
                                "content": record_payload.get("content", ""),
                                # Legacy v0 never stored rendered Telegram HTML.
                                "content_html": None,
                                "creator": record_payload.get("creator"),
                            }
                        )

                groups.append(
                    {
                        "name": str(group_name),
                        "records": migrated_records,
                    }
                )

        new_chats[str(chat_id)] = {
            "admins": admins,
            "groups": groups,
        }

    return {
        "schema_version": 1,
        "chats": new_chats,
    }


def downgrade(payload: dict[str, Any], timezone_name: str) -> dict[str, Any]:
    """Downgrade storage payload from schema v1 to legacy v0 layout."""

    timezone_info = _resolve_timezone(timezone_name)
    chats = payload.get("chats", {})
    if not isinstance(chats, dict):
        chats = {}

    old_root: dict[str, Any] = {}
    for chat_id, chat_data in chats.items():
        chat_payload = chat_data if isinstance(chat_data, dict) else {}
        admins = chat_payload.get("admins", [])
        groups = chat_payload.get("groups", [])
        records: dict[str, list[dict[str, Any]]] = {}

        if isinstance(groups, list):
            for group in groups:
                group_payload = group if isinstance(group, dict) else {}
                group_name = str(group_payload.get("name", ""))
                group_records = group_payload.get("records", [])
                migrated_records: list[dict[str, Any]] = []
                if isinstance(group_records, list):
                    for record in group_records:
                        record_payload = record if isinstance(record, dict) else {}
                        migrated_records.append(
                            {
                                "datetime": _convert_to_legacy(
                                    record_payload.get("datetime", ""),
                                    timezone_info,
                                ),
                                "content": record_payload.get("content", ""),
                            }
                        )
                records[group_name] = migrated_records

        old_root[str(chat_id)] = {
            "admins": admins,
            "records": records,
        }

    return old_root


migration = Migration(
    revision="0001_v0_to_v1",
    down_revision=None,
    from_version=0,
    to_version=1,
    tags=("json", "storage", "bootstrap"),
    upgrade=upgrade,
    downgrade=downgrade,
)
