"""Structured direction and immutable resolved scene contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Mapping

from engine.versions import RESOLVED_SCENE_VERSION, SCENE_BRIEF_VERSION


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
    locked_selections: Mapping[str, str] = field(default_factory=dict)
    schema_version: str = SCENE_BRIEF_VERSION

    def to_dict(self) -> dict:
        data = asdict(self)
        data["locks"] = sorted(self.locks)
        data["locked_selections"] = dict(self.locked_selections)
        return data


@dataclass(frozen=True)
class ResolvedScene:
    schema_version: str
    brief: SceneBrief
    selection_ids: dict[str, str]
    selections: dict[str, str]
    identity_anchors: tuple[str, ...]
    negative_constraints: tuple[str, ...]
    resolver_version: str = "nexus_studio.resolver.v1"

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "brief": self.brief.to_dict(),
            "selection_ids": self.selection_ids,
            "selections": self.selections,
            "identity_anchors": list(self.identity_anchors),
            "negative_constraints": list(self.negative_constraints),
            "resolver_version": self.resolver_version,
        }
