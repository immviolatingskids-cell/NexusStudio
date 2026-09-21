"""Affinity-aware ranking for presentation choices, never for identity."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from pool_models import PoolEntry


def score_entry(entry: PoolEntry, affinities: Mapping[str, int]) -> int:
    """Return the compatible affinity score for a scene-only pool entry."""
    return sum(affinities.get(tag, 0) for tag in entry.tags)


def preferred_entries(
    entries: Iterable[PoolEntry], affinities: Mapping[str, int]) -> tuple[PoolEntry, ...]:
    """Return all top-scoring entries so seeded selection can break ties."""
    candidates = tuple(entries)
    if not candidates:
        return ()
    scored = tuple((entry, score_entry(entry, affinities)) for entry in candidates)
    best = max(score for _, score in scored)
    return tuple(entry for entry, score in scored if score == best)
