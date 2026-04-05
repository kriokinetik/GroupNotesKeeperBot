"""Shared repository-level contracts."""

from abc import ABC

from repositories.abstracts import (
    AbstractAdminRepository,
    AbstractGroupRepository,
    AbstractRecordRepository,
)


class StorageProtocol(ABC):
    """Aggregate interface exposing all repositories used by the app."""

    admin: AbstractAdminRepository
    group: AbstractGroupRepository
    record: AbstractRecordRepository
