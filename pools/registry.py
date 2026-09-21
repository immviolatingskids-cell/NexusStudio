"""Registry for the deliberate, production-facing scene vocabulary."""

from __future__ import annotations

from collections.abc import Iterable

from pool_models import PoolEntry
from pools import capture, environment, fashion, lighting, pose, realism


def _all_entries() -> tuple[PoolEntry, ...]:
    return (
        *environment.POOL,
        *fashion.POOL,
        *lighting.POOL,
        *pose.POOL,
        *capture.POOL,
        *realism.POOL,
    )


ENTRIES = _all_entries()
BY_ID = {entry.id: entry for entry in ENTRIES}

if len(BY_ID) != len(ENTRIES):
    raise RuntimeError("Scene pool IDs must be unique.")


def entries_for(category: str) -> tuple[PoolEntry, ...]:
    return tuple(entry for entry in ENTRIES if entry.metadata.get("category") == category)


def find(value: str | None, *, category: str | None = None) -> PoolEntry | None:
    """Resolve an ID, label, or tag to one unambiguous vocabulary entry."""
    if not value:
        return None
    needle = value.strip().lower().replace("-", "_").replace(" ", "_")
    candidates: Iterable[PoolEntry] = ENTRIES
    if category:
        candidates = (entry for entry in candidates if entry.metadata.get("category") == category)
    matches = [
        entry for entry in candidates
        if entry.id == needle
        or entry.text.lower().replace(" ", "_") == needle
        or needle in entry.tags
    ]
    return matches[0] if len(matches) == 1 else None
