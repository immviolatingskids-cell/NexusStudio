"""Inspectable result contracts for canonical-character vocabulary resolution."""

from __future__ import annotations

from dataclasses import dataclass, field

from pool_models import PoolEntry


@dataclass(frozen=True)
class ResolvedEntry:
    source_path: str
    source_value: str
    entry: PoolEntry
    match_method: str

    def to_dict(self) -> dict:
        return {"source_path": self.source_path, "source_value": self.source_value, "entry_id": self.entry.id, "entry_text": self.entry.text, "match_method": self.match_method}


@dataclass(frozen=True)
class UnresolvedTrait:
    source_path: str
    source_value: str
    reason: str

    def to_dict(self) -> dict:
        return {"source_path": self.source_path, "source_value": self.source_value, "reason": self.reason}


@dataclass(frozen=True)
class ResolutionResult:
    character_id: str
    resolved_entries: tuple[ResolvedEntry, ...]
    unresolved_traits: tuple[UnresolvedTrait, ...]
    skipped_traits: tuple[str, ...] = field(default_factory=tuple)

    @property
    def coverage_percent(self) -> int:
        total = len(self.resolved_entries) + len(self.unresolved_traits)
        return round(100 * len(self.resolved_entries) / total) if total else 100

    def to_dict(self) -> dict:
        return {"character_id": self.character_id, "resolved_entries": [item.to_dict() for item in self.resolved_entries], "unresolved_traits": [item.to_dict() for item in self.unresolved_traits], "skipped_traits": list(self.skipped_traits), "coverage_percent": self.coverage_percent}
