"""Compile character and scene facts into a deliberate image-direction plan."""

from __future__ import annotations

from collections.abc import Iterable

from engine.adapters.base import DENSITIES, validate_density
from engine.loader import load_character
from engine.prompt_plan import PromptPlan
from engine.prompt_validation import validate_prompt_plan


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


def _composition(camera: str | None) -> str | None:
    if not camera:
        return None
    text = camera.replace("framing", "composition")
    if "full-body" in text:
        return "full-body composition with the entire figure visible and comfortable space around her"
    if "medium portrait" in text:
        return "medium portrait framed from roughly the waist upward"
    if "wide environmental" in text:
        return "wide environmental composition showing her within the surrounding setting"
    if "three-quarter view" in text:
        return "three-quarter angle at eye level"
    return text


def _lighting(lighting: str | None, environment: str | None) -> str | None:
    if not lighting:
        return None
    if "window light" in lighting:
        return "diffused daylight entering from a nearby window, with gentle facial modelling"
    if "indoor ambient" in lighting:
        return "soft practical indoor light that keeps the work setting believable"
    if "overcast" in lighting:
        return "soft overcast daylight with even, natural facial light"
    if "natural daylight" in lighting:
        return "soft natural daylight with gentle, believable shadows"
    return lighting


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
    anchors = _unique((f"{hair_length} {hair_color} hair".strip(), f"{eye_color} eyes" if eye_color else "", freckles, build))
    identity = f"{character.identity.name}, a {character.identity.age}-year-old {character.identity.nationality} {character.identity.gender}"
    context = scene_description.context
    # Anchors already carry build, hair colour/length, eyes and freckles.  The
    # supporting clauses deliberately add texture and facial structure instead
    # of restating those same concepts in serialized-composer prose.
    body = None
    face_shape = _appearance(character, "face.shape")
    cheekbones = _appearance(character, "face.cheekbones")
    face_bits = _unique((f"{skin_tone} skin" if skin_tone else "", f"{face_shape} facial features" if face_shape else "", f"{cheekbones} cheekbones" if cheekbones else ""))
    face = "She has " + _natural_join(face_bits) + "." if face_bits else None
    hair_density = _appearance(character, "hair.density")
    hair_texture = _appearance(character, "hair.texture")
    hair_framing = _appearance(character, "hair.framing")
    hair_bits = _unique((hair_density, hair_texture, hair_framing))
    hair = "Her hair is " + _natural_join(hair_bits) + "." if hair_bits else None
    omitted: list[str] = []
    if density == "compact":
        face = None
        omitted.extend(("face_detail", "supporting_style"))
    if density != "detailed":
        omitted.append("atmosphere")
    plan = PromptPlan(
        character_id=character.character_id, character_name=character.identity.name, mode=scene_description.mode,
        density=density, image_intent=_intent(scene_description.mode), subject_identity=identity,
        identity_anchors=anchors, body_description=body, face_description=face, hair_description=hair,
        wardrobe=context.wardrobe, activity=context.activity or ("caught in an unposed everyday moment" if scene_description.mode == "lifestyle" else None), pose=_pose_for(context.activity, context.pose),
        environment=context.environment, composition=_composition(context.camera), camera=context.camera,
        lighting=_lighting(context.lighting, context.environment), atmosphere=context.mood if density == "detailed" else None,
        quality_constraints=("natural skin texture", "realistic proportions", "realistic fabric behaviour") if density == "detailed" else ("natural skin texture", "realistic proportions"),
        identity_constraints=("preserve her described hair colour, eye colour, and distinguishing facial features",),
        omitted_fields=tuple(omitted), source_metadata={
            "canonical_fallback_paths": visual_description.canonical_fallback_paths,
            "defaulted_fields": scene_description.defaulted_fields,
            "character_context_fields": scene_description.character_context_fields,
            "override_fields": scene_description.override_fields,
            "redundancies_removed": ("overlapping freckle and build descriptions",),
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


def _pose_for(activity: str | None, pose: str | None) -> str | None:
    if not activity:
        return pose
    activity_lower = activity.casefold()
    if "working as a chef" in activity_lower:
        return "standing naturally at the counter, with her hands engaged in the work"
    if pose:
        return pose
    return "positioned naturally for the activity"
