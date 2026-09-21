"""Structured direction and immutable resolved scene contracts."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SceneBrief:
    character_id: str
    activity: str | None = None
    location: str | None = None
    atmosphere: str | None = None
    wardrobe_style: str | None = None
    hair_style: str | None = None
    pose: str | None = None
    expression: str | None = None
    lighting: str | None = None
    season: str | None = None
    framing: str | None = None
    image_style: str = "natural"
    seed: int = 0
    locks: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class ResolvedScene:
    brief: SceneBrief
    selections: dict[str, str]
    identity_anchors: tuple[str, ...]
    negative_constraints: tuple[str, ...]
