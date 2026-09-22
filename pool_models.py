"""Small, dependency-free vocabulary model shared by scene pools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, FrozenSet, Mapping


@dataclass(frozen=True)
class PoolEntry:
    """One selectable, presentation-level scene detail.

    Pool entries never define a character's identity.  They are only choices
    for a particular take: an environment, pose, garment, or lighting setup.
    """

    id: str
    text: str
    tags: FrozenSet[str]
    weight: float = 1.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("PoolEntry.id must be a non-empty string.")
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("PoolEntry.text must be a non-empty string.")
        if isinstance(self.tags, str):
            raise ValueError("PoolEntry.tags must be a collection of tag strings.")
        object.__setattr__(self, "tags", frozenset(self.tags))
        if not self.tags or not all(isinstance(tag, str) and tag.strip() for tag in self.tags):
            raise ValueError("PoolEntry.tags must contain one or more non-empty strings.")
        if isinstance(self.weight, bool) or not isinstance(self.weight, (int, float)) or self.weight <= 0:
            raise ValueError("PoolEntry.weight must be a positive number.")
        object.__setattr__(self, "weight", float(self.weight))
        object.__setattr__(self, "metadata", dict(self.metadata))
