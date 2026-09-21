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
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", frozenset(self.tags))
        object.__setattr__(self, "metadata", dict(self.metadata))
