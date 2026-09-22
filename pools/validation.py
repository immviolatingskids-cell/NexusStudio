"""Validation for pool definitions, kept separate from selection logic."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from pool_models import PoolEntry
from tags import is_valid_tag_name


class PoolValidationError(ValueError):
    """Raised when reusable vocabulary violates its public contract."""


def validate_pools(
    pools: Mapping[str, Iterable[PoolEntry]], *, allowed_tags: frozenset[str], allow_empty: bool = False
) -> None:
    """Validate entries without normalizing or repairing any vocabulary."""
    seen_ids: set[str] = set()
    for pool_name, entries in pools.items():
        entries = tuple(entries)
        if not entries and not allow_empty:
            raise PoolValidationError(f"{pool_name}: pool must not be empty")
        for entry in entries:
            location = f"{pool_name}.{getattr(entry, 'id', '<unknown>')}"
            if not isinstance(entry, PoolEntry):
                raise PoolValidationError(f"{location}: expected PoolEntry")
            if entry.id in seen_ids:
                raise PoolValidationError(f"{location}: duplicate PoolEntry id")
            seen_ids.add(entry.id)
            unknown = sorted(tag for tag in entry.tags if tag not in allowed_tags)
            if unknown:
                raise PoolValidationError(f"{location}: unknown tag '{unknown[0]}'")
            invalid = sorted(tag for tag in entry.tags if not is_valid_tag_name(tag))
            if invalid:
                raise PoolValidationError(f"{location}: invalid tag name '{invalid[0]}'")
