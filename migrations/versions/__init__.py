"""Registered schema migrations in execution order."""

from .v0001_v0_to_v1 import migration as v0001_v0_to_v1

MIGRATIONS = [
    v0001_v0_to_v1,
]

__all__ = [
    "MIGRATIONS",
]
