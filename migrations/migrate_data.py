"""CLI for storage migrations (alembic-like upgrade/downgrade)."""

import argparse
import logging
from pathlib import Path

from migrations import downgrade_storage, latest_schema_version, upgrade_storage

DEFAULT_INPUT_FILE = "data.json"
DEFAULT_TIMEZONE = "Europe/Moscow"
logger = logging.getLogger(__name__)


def _parse_tag_list(raw: str | None) -> set[str] | None:
    if raw is None:
        return None
    tags = {item.strip() for item in raw.split(",") if item.strip()}
    return tags or None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run JSON storage migrations (upgrade/downgrade)."
    )
    parser.add_argument(
        "command",
        choices=("upgrade", "downgrade"),
        help="Migration direction.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="head",
        help="Target schema version number, or 'head' for latest.",
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_FILE,
        help=f"Path to storage JSON file. Defaults to {DEFAULT_INPUT_FILE!r}.",
    )
    parser.add_argument(
        "--timezone",
        default=DEFAULT_TIMEZONE,
        help=f"IANA timezone name for datetime conversion. Defaults to {DEFAULT_TIMEZONE!r}.",
    )
    parser.add_argument(
        "--tags",
        default=None,
        help="Comma-separated migration tags filter (for example: json,storage).",
    )
    return parser.parse_args()


def _resolve_target(raw_target: str) -> int:
    if raw_target == "head":
        return latest_schema_version()
    return int(raw_target)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    include_tags = _parse_tag_list(args.tags)
    target = _resolve_target(args.target)
    logger.debug(
        "Running migration CLI command=%s input=%s target=%s timezone=%s tags=%s",
        args.command,
        input_path,
        target,
        args.timezone,
        include_tags,
    )

    if args.command == "upgrade":
        changed = upgrade_storage(
            input_path,
            target_version=target,
            timezone_name=args.timezone,
            include_tags=include_tags,
        )
        status = "applied" if changed else "already up-to-date"
        print(f"Upgrade {status}: {input_path} -> schema_version {target}")
        return

    changed = downgrade_storage(
        input_path,
        target_version=target,
        timezone_name=args.timezone,
        include_tags=include_tags,
    )
    status = "applied" if changed else "already at target"
    print(f"Downgrade {status}: {input_path} -> schema_version {target}")


if __name__ == "__main__":
    main()
