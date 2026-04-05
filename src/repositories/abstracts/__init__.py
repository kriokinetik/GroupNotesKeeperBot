"""Exports for abstract repository interfaces."""

from .admin import AbstractAdminRepository, UID
from .group import AbstractGroupRepository
from .record import AbstractRecordRepository, CID, RID

__all__ = [
    "AbstractRecordRepository",
    "AbstractGroupRepository",
    "AbstractAdminRepository",
    "CID",
    "RID",
    "UID",
]
