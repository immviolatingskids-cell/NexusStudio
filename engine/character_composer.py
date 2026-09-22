"""Deterministic rendering of resolver output into visual character prose."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from engine.composer_models import DescriptionSection, VisualDescription
from engine.loader import load_all_characters, load_character
from engine.resolver import resolve_character
from engine.resolver_models import ResolutionResult


SECTION_ORDER = ("identity", "build", "skin", "face", "eyes", "hair", "distinguishing_features", "fashion")
FALLBACK_PATHS = frozenset({"appearance.eyes.color", "appearance.hair.length", "appearance.hair.color", "appearance.skin.tone"})


def _join(items: Iterable[str]) -> str:
    unique: list[str] = []
    seen: set[str] = set()
    for item in items:
        key = item.casefold().replace("natural ", "").replace("naturally ", "")
        if key not in seen:
            seen.add(key)
            unique.append(item)
    if len(unique) < 2:
        return "".join(unique)
    if len(unique) == 2:
        return f"{unique[0]} and {unique[1]}"
    return f"{', '.join(unique[:-1])}, and {unique[-1]}"


def _value_at(appearance: dict[str, Any], path: str) -> str | None:
    value: Any = appearance
    for part in path.removeprefix("appearance.").split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value if isinstance(value, str) else None


def _section_for_path(path: str) -> str:
    if path.startswith("appearance.body"):
        return "build"
    if path.startswith("appearance.skin"):
        return "skin"
    if path.startswith("appearance.hair"):
        return "hair"
    if path.startswith("appearance.eyes"):
        return "eyes"
    if path.startswith("appearance.face"):
        return "face"
    return "distinguishing_features"


def _phrase_text(item) -> str:
    return item.entry.text if hasattr(item, "entry") else item[1]


def _render_section(section_id: str, items: list) -> str:
    phrases = [_phrase_text(item) for item in items]
    if section_id == "build":
        build_words = [phrase.removesuffix(" build").replace("soft athletic", "softly athletic") for phrase in phrases if "build" in phrase]
        proportion_words = [phrase for phrase in phrases if "proportion" in phrase]
        lead = _join(build_words) or _join(phrases)
        tail = f" with {_join(proportion_words)}" if proportion_words else ""
        return f"She has a {lead} build{tail}."
    if section_id == "skin":
        complexion = next((phrase for phrase in phrases if "complexion" in phrase), None)
        details = [phrase for phrase in phrases if phrase != complexion]
        return f"Her complexion is {complexion}, with {_join(details)}." if complexion and details else f"Her skin is defined by {_join(phrases)}."
    if section_id == "eyes":
        colours = [phrase for phrase in phrases if phrase in {"green", "hazel", "brown", "blue", "grey", "amber"}]
        shapes = [phrase for phrase in phrases if phrase not in colours]
        colour_text = "-".join(colours) if len(colours) == 2 else _join(colours)
        shape_text = f", with { _join(shapes) }-shaped features" if shapes else ""
        return f"Her eyes are {colour_text}{shape_text}."
    if section_id == "hair":
        return f"Her hair is {_join(phrases)}."
    if section_id == "face":
        return f"Her facial features include {_join(phrases)}."
    if section_id == "distinguishing_features":
        return f"Her distinguishing features include {_join(phrases)}."
    return f"Her typical style leans toward {_join(phrases)}."


def compose_character(character) -> VisualDescription:
    return _compose(character, resolve_character(character))


def compose_character_by_id(character_id: str) -> VisualDescription:
    return compose_character(load_character(character_id))


def compose_from_resolution(result: ResolutionResult) -> VisualDescription:
    """Compose from a result by loading its canonical source through the loader."""
    return _compose(load_character(result.character_id), result)


def compose_all_characters() -> tuple[VisualDescription, ...]:
    return tuple(compose_character(character) for character in load_all_characters())


def _compose(character, result: ResolutionResult) -> VisualDescription:
    grouped: dict[str, list] = defaultdict(list)
    resolved_paths = {item.source_path for item in result.resolved_entries}
    for item in result.resolved_entries:
        grouped[_section_for_path(item.source_path)].append(item)
    fallback_paths: list[str] = []
    for trait in result.unresolved_traits:
        if trait.source_path in FALLBACK_PATHS and trait.source_path not in resolved_paths:
            value = _value_at(character.appearance, trait.source_path)
            if value:
                grouped[_section_for_path(trait.source_path)].append((trait.source_path, value, None))
                fallback_paths.append(trait.source_path)

    identity = character.identity
    sections: list[DescriptionSection] = [DescriptionSection("identity", "Identity", f"{identity.name} is a {identity.age}-year-old {identity.nationality} {identity.gender} from {identity.home}.", source_paths=("identity.name", "identity.age", "identity.nationality", "identity.gender", "identity.home"))]
    rendered_so_far = ""
    for section_id in SECTION_ORDER[1:]:
        items = grouped.get(section_id, [])
        if section_id == "skin":
            # A single scalar complexion field can resolve to several tokens;
            # retain its highest-precedence entry rather than state two tones.
            seen_paths: set[str] = set()
            items = [item for item in items if not (item.source_path in seen_paths or seen_paths.add(item.source_path))]
        phrases = [item.entry.text if hasattr(item, "entry") else item[1] for item in items]
        phrases = [phrase for phrase in phrases if phrase.casefold() not in rendered_so_far.casefold()]
        if not phrases:
            continue
        source_entries = tuple(item.entry.id for item in items if hasattr(item, "entry"))
        source_paths = tuple(item.source_path if hasattr(item, "source_path") else item[0] for item in items)
        text = _render_section(section_id, items)
        sections.append(DescriptionSection(section_id, section_id.replace("_", " ").title(), text, source_entries, source_paths))
        rendered_so_far += " " + text
    unresolved = tuple(f"{trait.source_path}: {trait.source_value}" for trait in result.unresolved_traits if trait.source_path not in fallback_paths)
    return VisualDescription(character.character_id, identity.name, tuple(sections), unresolved, tuple(fallback_paths), {"resolved_entries": len(result.resolved_entries), "canonical_fallbacks": len(fallback_paths), "unresolved_omitted": len(unresolved)})
