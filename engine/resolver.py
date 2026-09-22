"""Deterministic resolver for scene details; it never changes identity."""

from __future__ import annotations

import random
from collections.abc import Mapping

from dataclasses import replace

from engine.scene_models import ResolvedScene, SceneBrief
from engine.character_resolution import resolve_character as _resolve_character
from engine.character_resolution import resolution_diagnostics
from engine.loader import load_all_characters, load_character
from engine.identity import find_identity_conflicts
from engine.scoring import preferred_entries
from engine.versions import RESOLVED_SCENE_VERSION
from pool_models import PoolEntry
from pools.registry import BY_ID, entries_for, find_display


def resolve_character(character):
    """Resolve canonical appearance into vocabulary entries without scene selection."""
    return _resolve_character(character)


def resolve_character_by_id(character_id: str):
    """Load through the canonical gateway, then resolve its appearance vocabulary."""
    return resolve_character(load_character(character_id))


def resolve_all_characters():
    """Resolve every canonical character in stable loader order."""
    return tuple(resolve_character(character) for character in load_all_characters())


def _pick(
    category: str,
    requested: str | None,
    rng: random.Random,
    affinities: Mapping[str, int],
) -> PoolEntry:
    matched = find_display(requested, category=category)
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
    identity_text = " ".join(value for value in (
        brief.activity, brief.location, brief.atmosphere, brief.wardrobe_style,
        brief.hair_style, brief.expression, brief.pose, brief.lighting,
        brief.season, brief.framing, brief.image_style,
    ) if value)
    conflicts = find_identity_conflicts(brief.character_id, identity_text)
    if conflicts:
        raise ValueError("; ".join(conflicts))
    rng = random.Random(brief.seed)
    affinities = affinities or {}
    requested = {"location": brief.location, "atmosphere": brief.atmosphere, "wardrobe": brief.wardrobe_style, "pose": brief.pose, "lighting": brief.lighting, "framing": brief.framing}
    categories = {"location": "location", "atmosphere": "atmosphere", "wardrobe": "style", "pose": "base_pose", "lighting": "lighting_setup", "framing": "framing"}
    entries: dict[str, PoolEntry] = {}
    for key, category in categories.items():
        locked_id = brief.locked_selections.get(key)
        if locked_id:
            entry = BY_ID.get(locked_id)
            if entry is None or entry.metadata.get("category") != category:
                raise ValueError(f"Locked selection '{locked_id}' is invalid for {key}.")
        else:
            entry = _pick(category, requested[key], rng, affinities)
        entries[key] = entry
    selections = {key: entry.text for key, entry in entries.items()}
    selection_ids = {key: entry.id for key, entry in entries.items()}
    if brief.hair_style:
        selections["hair_style"] = brief.hair_style
    if brief.expression:
        selections["expression"] = brief.expression
    if brief.season:
        selections["season"] = brief.season
    if brief.activity:
        selections["activity"] = brief.activity
    return ResolvedScene(
        schema_version=RESOLVED_SCENE_VERSION,
        brief=brief,
        selection_ids=selection_ids,
        selections=selections,
        identity_anchors=identity_profile.anchors,
        negative_constraints=identity_profile.negative_constraints,
    )


def reroll_scene(scene: ResolvedScene, identity_profile, affinities: Mapping[str, int] | None = None, *, dimension: str | None = None) -> ResolvedScene:
    """Advance a seed while retaining explicit locks and, optionally, all but one dimension."""
    valid = set(scene.selection_ids)
    if dimension is not None and dimension not in valid:
        raise ValueError(f"Unknown reroll dimension '{dimension}'.")
    if dimension in scene.brief.locks:
        raise ValueError(f"Cannot reroll locked dimension '{dimension}'.")
    locked = {key: scene.selection_ids[key] for key in scene.brief.locks if key in scene.selection_ids}
    if dimension is not None:
        locked.update({key: value for key, value in scene.selection_ids.items() if key != dimension})
    brief = replace(scene.brief, seed=scene.brief.seed + 1, locked_selections=locked)
    return resolve_scene(brief, identity_profile, affinities)
