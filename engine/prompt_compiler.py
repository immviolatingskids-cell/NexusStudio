"""Compile character and scene facts into a deliberate image-direction plan."""

from __future__ import annotations

from collections.abc import Iterable

from engine.adapters.base import DENSITIES, validate_density
from engine.loader import load_character
from engine.identity import IDENTITY_DIR, find_identity_conflicts, identity_color_is_locked, load_identity_profile
import json
from engine.prompt_plan import PromptPlan
from engine.prompt_validation import validate_prompt_plan
from engine.prompt_validation import PromptValidationError


def _unique(items: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        key = item.casefold().replace("natural ", "").replace("naturally ", "")
        if item and key not in seen:
            seen.add(key)
            result.append(item)
    return tuple(result)


def _appearance(character, path: str, default: str = "") -> str:
    value = character.appearance
    for part in path.split("."):
        if not isinstance(value, dict):
            return default
        value = value.get(part)
    return value if isinstance(value, str) else default


def _phrase(section_map: dict[str, str], section: str) -> str | None:
    return section_map.get(section)


def _intent(mode: str) -> str:
    return {
        "portrait": "Photorealistic medium portrait",
        "full_body": "Photorealistic full-body image",
        "environmental": "Photorealistic wide environmental image",
    }.get(mode, "Photorealistic lifestyle image")


def _identity_profile_data(character_id: str) -> dict:
    path = IDENTITY_DIR / f"{character_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _identity_items(character_id: str) -> tuple[dict, ...]:
    data = _identity_profile_data(character_id)
    lock = data.get("identity_lock", {})
    return tuple(value for value in lock.values() if isinstance(value, dict) and isinstance(value.get("description"), str))


def _composition(camera: str | None) -> str | None:
    if not camera:
        return None
    text = camera.replace("framing", "composition")
    if "full-body" in text:
        return "Use a full-body composition with her entire figure visible, including her feet, and comfortable space around her."
    if "medium portrait" in text:
        return "Frame her in a medium portrait from roughly the waist upward."
    if "wide environmental" in text:
        return "Use a wide environmental composition that clearly shows her within the surrounding setting."
    if "three-quarter view" in text:
        return "Use a three-quarter angle at eye level."
    return f"Use {text}."


def _lighting(lighting: str | None, environment: str | None) -> str | None:
    if not lighting:
        return None
    if "window light" in lighting:
        return "Diffused daylight enters from a nearby window, creating gentle facial modelling."
    if "indoor ambient" in lighting:
        return "Soft practical indoor light keeps the work setting believable."
    if "overcast" in lighting:
        return "Soft overcast daylight gives even, natural facial light."
    if "natural daylight" in lighting:
        return "Soft natural daylight creates gentle, believable shadows."
    return lighting.rstrip(".") + "."


def compile_prompt_plan(character, visual_description, scene_description, density: str = "standard") -> PromptPlan:
    """Select and order facts once, before any model-specific rendering."""
    validate_density(density)
    if character.character_id != scene_description.character_id:
        raise ValueError("Prompt plan character does not match the scene description")
    sections = {section.id: section.text for section in visual_description.sections}
    hair_color = _appearance(character, "hair.color")
    hair_length = _appearance(character, "hair.length")
    eye_color = _appearance(character, "eyes.color")
    skin_tone = _appearance(character, "skin.tone")
    build = _appearance(character, "body.build")
    freckles = next((feature for feature in _appearance_list(character, "skin.features") if "freckle" in feature.casefold()), "")
    profile = load_identity_profile(character.character_id)
    drift = tuple(item["instruction"] for item in profile.drift_critical_features)
    canonical_anchors = (f"{hair_length} {hair_color} hair".strip(), f"{eye_color} eyes" if eye_color and identity_color_is_locked(character.character_id, "eyes") else "", freckles, build)
    # Critical LOCKED_LOOK facts lead every density; canonical appearance
    # remains supporting input and cannot displace the identity contract.
    anchors = _unique((*profile.critical_anchors, *(item["instruction"] for item in profile.drift_critical_features), *canonical_anchors))
    identity = f"{character.identity.name}, a {character.identity.age}-year-old {character.identity.nationality} {character.identity.gender}"
    context = scene_description.context
    scene_text = " ".join(filter(None, (context.activity, context.environment, context.wardrobe, context.pose, context.camera, context.lighting, context.mood)))
    identity_conflicts = find_identity_conflicts(character.character_id, scene_text)
    if identity_conflicts:
        raise PromptValidationError("; ".join(identity_conflicts))
    # Anchors already carry build, hair colour/length, eyes and freckles.  The
    # supporting clauses deliberately add texture and facial structure instead
    # of restating those same concepts in serialized-composer prose.
    body = None
    face_shape = _appearance(character, "face.shape")
    cheekbones = _appearance(character, "face.cheekbones")
    face_bits = _unique((_skin_phrase(skin_tone), _face_shape_phrase(face_shape), _cheekbone_phrase(cheekbones)))
    face = "She has " + _natural_join(face_bits) + "." if face_bits else None
    hair_density = _appearance(character, "hair.density")
    hair_texture = _appearance(character, "hair.texture")
    hair_framing = _appearance(character, "hair.framing")
    hair_bits = _unique((hair_density, hair_texture, hair_framing))
    hair = "Her hair is " + _natural_join(hair_bits) + "." if hair_bits else None
    omitted: list[str] = []
    if density == "compact":
        face = None
        body = None
        omitted.extend(("face_detail", "supporting_style"))
    else:
        profile_data = _identity_profile_data(character.character_id)
        identity_lock = profile_data.get("identity_lock", {})
        if isinstance(identity_lock, dict):
            if density in {"standard", "detailed"}:
                relations = profile_data.get("identity_relationships", {})
                expression = profile_data.get("expression_behavior", {})
                strong_text = " ".join(value.rstrip(".") + "." for value in profile.strong_anchors)
                relationship_text = "; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in relations.items() if k != "priority") if isinstance(relations, dict) else ""
                expression_text = "; ".join(str(v) for k, v in expression.items() if k != "priority") if density == "detailed" and isinstance(expression, dict) else ""
                face = " ".join(value.rstrip(".") + "." for value in (face, strong_text, relationship_text, expression_text) if value)
    if density != "detailed":
        omitted.append("atmosphere")
    plan = PromptPlan(
        character_id=character.character_id, character_name=character.identity.name, mode=scene_description.mode,
        density=density, image_intent=_intent(scene_description.mode), subject_identity=identity,
        identity_anchors=anchors, identity_block=(profile.prompt_identity_blocks or {}).get(density), body_description=body, face_description=face, hair_description=hair,
        wardrobe=f"She is dressed in {context.wardrobe}." if context.wardrobe else None,
        activity=_event_for(scene_description.mode, context.activity, context.pose), pose=_pose_for(context.activity, context.pose),
        environment=_environment_for(scene_description.mode, context.environment), composition=_composition(context.camera), camera=context.camera,
        lighting=_lighting(context.lighting, context.environment), atmosphere=context.mood if density == "detailed" else None,
        quality_constraints=("Natural skin texture", "Realistic proportions", "Realistic fabric behaviour") if density == "detailed" else ("Natural skin texture", "Realistic proportions"),
        identity_constraints=(("Preserve her described hair colour, eye colour, and facial proportions as locked identity; allow requested mutable styling and scene changes",) + drift + profile.negative_constraints),
        omitted_fields=tuple(omitted), source_metadata={
            "canonical_fallback_paths": visual_description.canonical_fallback_paths,
            "defaulted_fields": scene_description.defaulted_fields,
            "character_context_fields": scene_description.character_context_fields,
            "override_fields": scene_description.override_fields,
            "redundancies_removed": ("overlapping freckle and build descriptions",),
            "identity_diagnostics": {
                "identity_lock_version": profile.version,
                "critical_traits": sum(1 for item in _identity_items(character.character_id) if item.get("priority") == "critical"),
                "strong_traits": sum(1 for item in _identity_items(character.character_id) if item.get("priority") == "strong"),
                "drift_critical_traits": len(profile.drift_critical_features),
                "scene_conflicts": len(identity_conflicts),
                "style_conflicts": 0,
                "mutable_traits": sorted(profile.mutable_features),
                "protected_traits": list(profile.immutable_features),
            },
        },
    )
    validate_prompt_plan(plan)
    return plan


def compile_prompt_plan_by_id(character_id: str, visual_description, scene_description, density: str = "standard") -> PromptPlan:
    return compile_prompt_plan(load_character(character_id), visual_description, scene_description, density)


def _appearance_list(character, path: str) -> tuple[str, ...]:
    value = character.appearance
    for part in path.split("."):
        if not isinstance(value, dict):
            return ()
        value = value.get(part)
    return tuple(item for item in value if isinstance(item, str)) if isinstance(value, list) else ()


def _join_nonrepeating(parts: Iterable[str | None]) -> str | None:
    values = _unique(part for part in parts if part)
    return " ".join(values) if values else None


def _natural_join(values: tuple[str, ...]) -> str:
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return " and ".join(values)
    return ", ".join(values[:-1]) + ", and " + values[-1]


def _skin_phrase(tone: str) -> str:
    """Render canonical skin scalars as grammatical appearance language."""
    value = tone.removesuffix(" skin").removesuffix(" complexion").strip()
    if value == "light natural":
        return "a light, natural complexion"
    if not value:
        return ""
    return f"a {value} complexion"


def _face_shape_phrase(shape: str) -> str:
    """Turn canonical face-shape scalars into a natural noun phrase."""
    if not shape:
        return ""
    if " softly " in shape:
        lead, rest = shape.split(" softly ", 1)
        return f"a {lead}, softly {rest} face"
    if " rounded " in shape:
        lead, rest = shape.split(" rounded ", 1)
        return f"a {lead}, rounded {rest} face"
    return f"a {shape} face"


def _cheekbone_phrase(cheekbones: str) -> str:
    """Keep cheekbone descriptors distinct but grammatically coordinated."""
    if not cheekbones:
        return ""
    return cheekbones.replace(" and ", ", ", 1) + " cheekbones"


def _pose_for(activity: str | None, pose: str | None) -> str | None:
    if not activity:
        return pose
    activity_lower = activity.casefold()
    if "working as a chef" in activity_lower:
        return "standing naturally at the counter, with her hands engaged in the work"
    if pose:
        return pose
    return "positioned naturally for the activity"


def _event_for(mode: str, activity: str | None, pose: str | None) -> str | None:
    """Make activity and pose one visual event instead of adjacent labels."""
    if activity and activity.startswith("working as a chef"):
        return "She stands at a preparation counter, focused on the work in her hands."
    if activity and activity.startswith("working as a software engineer"):
        return "She works at a desk, focused on her screen and keyboard."
    if activity and activity.startswith("working as a "):
        occupation = activity.removeprefix("working as a ")
        return f"She works naturally as a {occupation}."
    if activity and activity.startswith("enjoying "):
        hobby = activity.removeprefix("enjoying ")
        return f"She is {hobby}, moving naturally through the setting."
    if activity:
        return f"She is {activity}, {pose or 'positioned naturally for it'}."
    if mode == "lifestyle":
        return "She sits casually in an unposed everyday moment."
    if mode == "full_body":
        return "She stands naturally, with a relaxed and balanced posture."
    if mode == "environmental":
        return "She stands naturally within the setting, making the location part of the image."
    if pose:
        return f"She holds {pose.removeprefix('a ')}."
    return None


def _environment_for(mode: str, environment: str | None) -> str | None:
    if not environment:
        return None
    if mode == "environmental":
        return f"Give clear visual weight to {environment}."
    return f"The scene is set in {environment}."
