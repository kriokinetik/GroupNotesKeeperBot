"""Migration runner for sequential schema upgrades and downgrades."""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from migrations.base import Migration
from migrations.versions import MIGRATIONS

DEFAULT_TIMEZONE = "Europe/Moscow"
logger = logging.getLogger(__name__)


class MigrationError(RuntimeError):
    """Raised when migration chain or payload state is invalid."""


def _validate_registry(migrations: list[Migration]) -> None:
    if not migrations:
        logger.debug("Migration registry is empty")
        return

    seen_revisions: set[str] = set()
    for migration in migrations:
        if migration.revision in seen_revisions:
            raise MigrationError(f"Duplicate migration revision: {migration.revision}")
        seen_revisions.add(migration.revision)

    ordered = sorted(migrations, key=lambda item: item.from_version)
    for idx, migration in enumerate(ordered):
        if migration.to_version <= migration.from_version:
            raise MigrationError(
                f"Invalid version step in {migration.revision}: " f"{migration.from_version} -> {migration.to_version}"
            )
        if idx == 0:
            if migration.down_revision is not None:
                raise MigrationError(f"First migration {migration.revision} must have down_revision=None.")
            continue
        prev = ordered[idx - 1]
        if migration.down_revision != prev.revision:
            raise MigrationError(
                f"Revision chain mismatch: {migration.revision}.down_revision="
                f"{migration.down_revision!r}, expected {prev.revision!r}."
            )
        if migration.from_version != prev.to_version:
            raise MigrationError(
                "Migrations must form a continuous chain by schema_version. "
                f"Gap between {prev.revision} and {migration.revision}."
            )


def latest_schema_version() -> int:
    """Return latest schema version produced by the registry."""

    _validate_registry(MIGRATIONS)
    if not MIGRATIONS:
        logger.debug("No migrations registered, latest schema version defaults to v0")
        return 0
    return max(migration.to_version for migration in MIGRATIONS)


def _read_payload(path: Path) -> dict[str, Any]:
    # utf-8-sig keeps compatibility with files that accidentally contain BOM.
    # noinspection PyArgumentEqualDefault
    with path.open("r", encoding="utf-8-sig") as file:
        payload = json.load(file)
    if not isinstance(payload, dict):
        raise MigrationError(f"Storage root must be a JSON object: {path}")
    return payload


def _write_payload(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def _backup_path(path: Path, suffix: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return path.with_name(f"{path.stem}.{suffix}.{timestamp}{path.suffix}")


def _detect_schema_version(payload: dict[str, Any]) -> int:
    version = payload.get("schema_version")
    if version is None:
        # Legacy payloads do not declare schema_version and are treated as v0.
        return 0
    if not isinstance(version, int):
        raise MigrationError(f"schema_version must be int, got: {type(version).__name__}")
    if version < 0:
        raise MigrationError(f"schema_version must be >= 0, got: {version}")
    return version


def _select_upgrade(from_version: int, include_tags: set[str] | None) -> Migration | None:
    candidates = [item for item in MIGRATIONS if item.from_version == from_version]
    if include_tags is None:
        return candidates[0] if candidates else None
    tagged = [item for item in candidates if include_tags.intersection(item.tags)]
    return tagged[0] if tagged else None


def _select_downgrade(from_version: int, include_tags: set[str] | None) -> Migration | None:
    candidates = [item for item in MIGRATIONS if item.to_version == from_version]
    if include_tags is None:
        return candidates[0] if candidates else None
    tagged = [item for item in candidates if include_tags.intersection(item.tags)]
    return tagged[0] if tagged else None


def upgrade_storage(
    path: Path,
    *,
    target_version: int | None = None,
    timezone_name: str = DEFAULT_TIMEZONE,
    include_tags: set[str] | None = None,
) -> bool:
    """Upgrade storage to target schema version sequentially."""

    if not path.exists():
        logger.info("Upgrade skipped because storage file does not exist path=%s", path)
        return False

    _validate_registry(MIGRATIONS)
    latest_version = latest_schema_version()
    requested_target = latest_version if target_version is None else target_version
    if requested_target > latest_version:
        raise MigrationError(f"Target schema version {requested_target} is above latest {latest_version}.")

    payload = _read_payload(path)
    current_version = _detect_schema_version(payload)
    logger.info(
        "Starting storage upgrade path=%s current_version=%s target_version=%s",
        path,
        current_version,
        requested_target,
    )
    if current_version > latest_version:
        raise MigrationError(f"Storage schema version {current_version} is newer than known {latest_version}.")
    if current_version == requested_target:
        logger.info("Upgrade skipped because storage is already at target path=%s version=%s", path, current_version)
        return False
    if current_version > requested_target:
        raise MigrationError(
            f"Current schema version {current_version} is above target {requested_target}. " "Use downgrade instead."
        )

    original_version = current_version
    while current_version < requested_target:
        migration = _select_upgrade(current_version, include_tags)
        if migration is None:
            raise MigrationError(f"Missing migration step for schema version {current_version}.")
        if migration.from_version != current_version:
            raise MigrationError(
                f"Migration chain mismatch on {migration.revision}: " f"expected from_version={current_version}."
            )

        logger.info(
            "Applying upgrade migration revision=%s from_version=%s to_version=%s",
            migration.revision,
            migration.from_version,
            migration.to_version,
        )
        payload = migration.upgrade(payload, timezone_name)
        if not isinstance(payload, dict):
            raise MigrationError(f"Migration {migration.revision} returned non-object payload.")
        next_version = _detect_schema_version(payload)
        if next_version != migration.to_version:
            raise MigrationError(
                f"Migration {migration.revision} must set schema_version="
                f"{migration.to_version}, got {next_version}."
            )
        current_version = next_version

    backup_path = _backup_path(path, f"backup_v{original_version}")
    shutil.copy2(path, backup_path)
    _write_payload(path, payload)
    logger.info(
        "Storage upgrade completed path=%s backup=%s from_version=%s to_version=%s",
        path,
        backup_path,
        original_version,
        current_version,
    )
    return True


def downgrade_storage(
    path: Path,
    *,
    target_version: int,
    timezone_name: str = DEFAULT_TIMEZONE,
    include_tags: set[str] | None = None,
) -> bool:
    """Downgrade storage to target schema version sequentially."""

    if not path.exists():
        logger.info("Downgrade skipped because storage file does not exist path=%s", path)
        return False

    _validate_registry(MIGRATIONS)
    if target_version < 0:
        raise MigrationError("Target schema version must be >= 0.")

    payload = _read_payload(path)
    current_version = _detect_schema_version(payload)
    logger.info(
        "Starting storage downgrade path=%s current_version=%s target_version=%s",
        path,
        current_version,
        target_version,
    )
    if current_version == target_version:
        logger.info("Downgrade skipped because storage is already at target path=%s version=%s", path, current_version)
        return False
    if current_version < target_version:
        raise MigrationError(
            f"Current schema version {current_version} is below target {target_version}. " "Use upgrade instead."
        )

    original_version = current_version
    while current_version > target_version:
        migration = _select_downgrade(current_version, include_tags)
        if migration is None:
            raise MigrationError(f"Missing downgrade step for schema version {current_version}.")
        if migration.to_version != current_version:
            raise MigrationError(
                f"Migration chain mismatch on {migration.revision}: " f"expected to_version={current_version}."
            )

        logger.info(
            "Applying downgrade migration revision=%s from_version=%s to_version=%s",
            migration.revision,
            migration.from_version,
            migration.to_version,
        )
        payload = migration.downgrade(payload, timezone_name)
        if not isinstance(payload, dict):
            raise MigrationError(f"Migration {migration.revision} returned non-object payload.")
        expected_version = migration.from_version
        actual_version = _detect_schema_version(payload)
        if expected_version == 0 and "schema_version" not in payload:
            actual_version = 0
        if actual_version != expected_version:
            raise MigrationError(
                f"Migration {migration.revision} must result in schema_version="
                f"{expected_version}, got {actual_version}."
            )
        current_version = expected_version

    backup_path = _backup_path(path, f"backup_v{original_version}")
    shutil.copy2(path, backup_path)
    _write_payload(path, payload)
    logger.info(
        "Storage downgrade completed path=%s backup=%s from_version=%s to_version=%s",
        path,
        backup_path,
        original_version,
        current_version,
    )
    return True


def upgrade_storage_if_needed(path: Path, *, timezone_name: str = DEFAULT_TIMEZONE) -> bool:
    """Upgrade storage to latest version only if it is outdated."""

    return upgrade_storage(path, timezone_name=timezone_name)
