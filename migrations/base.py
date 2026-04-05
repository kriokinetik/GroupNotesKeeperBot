"""Migration metadata and callable types."""

from dataclasses import dataclass
from typing import Any, Callable

MigrationPayload = dict[str, Any]
MigrationFunc = Callable[[MigrationPayload, str], MigrationPayload]


@dataclass(frozen=True, slots=True)
class Migration:
    """Single schema migration definition."""

    revision: str
    down_revision: str | None
    from_version: int
    to_version: int
    tags: tuple[str, ...]
    upgrade: MigrationFunc
    downgrade: MigrationFunc
