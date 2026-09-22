"""Deterministic scene context layered on, never into, visual identity."""

from __future__ import annotations

from engine.character_composer import compose_character, compose_character_by_id
from engine.composer_models import DescriptionSection
from engine.loader import load_character
from engine.scene_context_models import SceneContext, SceneDescription
from engine.scene_defaults import MODE_DEFAULTS, SCENE_MODES


CONTEXT_FIELDS = ("activity", "environment", "wardrobe", "pose", "camera", "lighting", "mood")


def _character_context(character, mode: str) -> dict[str, str]:
    if mode == "workplace" and character.occupation.primary:
        return {"activity": f"working as a {character.occupation.primary}", "environment": f"a practical {character.occupation.primary} workspace"}
    if mode == "hobby" and character.hobbies:
        hobby = character.hobbies[0]
        return {"activity": f"enjoying {hobby}", "environment": f"a setting suited to {hobby}"}
    if mode in {"lifestyle", "environmental"} and character.identity.home:
        return {"environment": f"an everyday setting in {character.identity.home}"}
    return {}


def _context_for(character, mode: str, overrides: dict[str, str] | None) -> tuple[SceneContext, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    if mode not in MODE_DEFAULTS:
        raise ValueError(f"Unknown scene mode '{mode}'. Available modes: {', '.join(SCENE_MODES)}")
    overrides = overrides or {}
    unknown = sorted(set(overrides) - set(CONTEXT_FIELDS))
    if unknown:
        raise ValueError(f"Unknown scene override field(s): {', '.join(unknown)}")
    defaults = MODE_DEFAULTS[mode]
    awareness = _character_context(character, mode)
    values: dict[str, str | None] = {}
    defaulted: list[str] = []
    character_fields: list[str] = []
    override_fields: list[str] = []
    for field in CONTEXT_FIELDS:
        if field in overrides:
            values[field] = overrides[field]
            override_fields.append(field)
        elif field in awareness:
            values[field] = awareness[field]
            character_fields.append(field)
        else:
            values[field] = defaults.get(field)
            if values[field] is not None:
                defaulted.append(field)
    return SceneContext(mode=mode, **values), tuple(defaulted), tuple(character_fields), tuple(override_fields)


def compose_scene(character, mode: str, overrides: dict[str, str] | None = None) -> SceneDescription:
    description = compose_character(character)
    context, defaulted, character_fields, override_fields = _context_for(character, mode, overrides)
    return compose_scene_from_description(description, context, character=character, source=(defaulted, character_fields, override_fields))


def compose_scene_by_id(character_id: str, mode: str, overrides: dict[str, str] | None = None) -> SceneDescription:
    return compose_scene(load_character(character_id), mode, overrides)


def compose_scene_from_description(description, context: SceneContext, *, character=None, source: tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]] | None = None) -> SceneDescription:
    """Compose a scene from an existing visual description and explicit context."""
    if character is None:
        character = load_character(description.character_id)
    defaulted, character_fields, override_fields = source or ((), (), ())
    scene_text = f"Scene: She is {context.activity or 'shown naturally'} in {context.environment or 'an unobtrusive setting'}, wearing {context.wardrobe or 'simple everyday clothing'}. Her pose is {context.pose or 'relaxed'}, with {context.camera or 'eye-level framing'}, lit by {context.lighting or 'soft light'} in a {context.mood or 'calm'} atmosphere."
    sections = (*description.sections, DescriptionSection("scene", "Scene", scene_text, source_paths=CONTEXT_FIELDS))
    return SceneDescription(description.character_id, context.mode, description, context, sections, defaulted, character_fields, override_fields)
