"""Deterministic resolver for scene details; it never changes identity."""

from __future__ import annotations

import random
from collections.abc import Mapping

from engine.scene_models import ResolvedScene, SceneBrief
from engine.scoring import preferred_entries
from pool_models import PoolEntry
from pools.registry import entries_for, find


def _pick(
    category: str,
    requested: str | None,
    rng: random.Random,
    affinities: Mapping[str, int],
) -> PoolEntry:
    matched = find(requested, category=category)
    if matched:
        return matched
    options = entries_for(category)
    if not options:
        raise ValueError(f"No registered options for scene category '{category}'.")
    ranked = preferred_entries(options, affinities)
    return ranked[rng.randrange(len(ranked))]


def resolve_scene(
    brief: SceneBrief,
    identity_profile,
    affinities: Mapping[str, int] | None = None,
) -> ResolvedScene:
    """Resolve a brief into auditable choices using its seed.

    Free-text direction remains attached to the brief. Registered selections
    are used only for categories the studio owns, allowing the UI to expose
    stable IDs while preserving a director's wording for activities.
    """
    if not brief.character_id.strip():
        raise ValueError("A scene brief needs a character_id.")
    rng = random.Random(brief.seed)
    affinities = affinities or {}
    selections = {
        "location": _pick("location", brief.location, rng, affinities).text,
        "atmosphere": _pick("atmosphere", brief.atmosphere, rng, affinities).text,
        "wardrobe": _pick("style", brief.wardrobe_style, rng, affinities).text,
        "pose": _pick("base_pose", brief.pose, rng, affinities).text,
        "lighting": _pick("lighting_setup", brief.lighting, rng, affinities).text,
        "framing": _pick("framing", brief.framing, rng, affinities).text,
    }
    if brief.hair_style:
        selections["hair_style"] = brief.hair_style
    if brief.expression:
        selections["expression"] = brief.expression
    if brief.season:
        selections["season"] = brief.season
    if brief.activity:
        selections["activity"] = brief.activity
    return ResolvedScene(
        brief=brief,
        selections=selections,
        identity_anchors=identity_profile.anchors,
        negative_constraints=identity_profile.negative_constraints,
    )
