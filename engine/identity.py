"""Loading of character-specific immutable visual identity profiles."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import CHARACTERS_DIR
from engine.rules import CharacterValidationError


IDENTITY_DIR = CHARACTERS_DIR / "identity"


@dataclass(frozen=True)
class IdentityProfile:
    character_id: str
    version: str
    anchors: tuple[str, ...]
    immutable_features: tuple[str, ...]
    mutable_features: frozenset[str]
    negative_constraints: tuple[str, ...]
    drift_critical_features: tuple[dict[str, str], ...] = ()
    reference_consensus: dict[str, Any] | None = None
    variation_envelope: dict[str, Any] | None = None
    identity_relationships: dict[str, Any] | None = None
    expression_behavior: dict[str, Any] | None = None
    presentation_exclusions: tuple[str, ...] = ()
    critical_anchors: tuple[str, ...] = ()
    strong_anchors: tuple[str, ...] = ()
    signature_features: tuple[dict[str, str], ...] = ()
    prompt_identity_blocks: dict[str, str] | None = None


def _profile_path(character_id: str) -> Path:
    return IDENTITY_DIR / f"{character_id}.json"


def load_identity_profile(character_id: str) -> IdentityProfile:
    path = _profile_path(character_id)
    if not path.is_file():
        raise CharacterValidationError(f"Identity profile is missing for '{character_id}'.")
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CharacterValidationError(f"Invalid identity JSON in '{path.name}'.") from exc

    if data.get("character_id") != character_id:
        raise CharacterValidationError(f"Identity profile '{path.name}' does not match '{character_id}'.")
    if data.get("schema") != "character_studio.locked_look.v1" or not isinstance(data.get("version"), str):
        raise CharacterValidationError(f"Identity profile '{path.name}' needs a locked-look schema and version.")
    identity_lock = data.get("identity_lock")
    if not isinstance(identity_lock, dict) or not identity_lock:
        raise CharacterValidationError(f"Identity profile '{path.name}' needs identity_lock entries.")
    anchors = tuple(
        value["description"] for value in identity_lock.values()
        if isinstance(value, dict) and isinstance(value.get("description"), str)
    )
    critical_anchors = tuple(
        value["description"] for value in identity_lock.values()
        if isinstance(value, dict) and value.get("priority") == "critical" and isinstance(value.get("description"), str)
    )
    strong_anchors = tuple(
        value["description"] for value in identity_lock.values()
        if isinstance(value, dict) and value.get("priority") == "strong" and isinstance(value.get("description"), str)
    )
    immutable = data.get("immutable_features")
    mutable = data.get("mutable_features")
    negatives = data.get("negative_identity_constraints")
    if not anchors or not isinstance(immutable, list) or not isinstance(mutable, dict) or not isinstance(negatives, list):
        raise CharacterValidationError(f"Identity profile '{path.name}' has an incomplete identity contract.")
    required = ("drift_critical_features", "reference_consensus", "variation_envelope", "identity_relationships", "expression_behavior", "presentation_exclusions", "signature_features", "prompt_identity_blocks")
    missing = [field for field in required if field not in data]
    if missing:
        raise CharacterValidationError(f"Identity profile '{path.name}' is missing: {', '.join(missing)}.")
    if not isinstance(data["drift_critical_features"], list) or not data["drift_critical_features"]:
        raise CharacterValidationError(f"Identity profile '{path.name}' needs drift-critical features.")
    if not isinstance(data["reference_consensus"], dict) or not isinstance(data["variation_envelope"], dict):
        raise CharacterValidationError(f"Identity profile '{path.name}' needs reference consensus and variation guidance.")
    if not isinstance(data["identity_relationships"], dict) or not isinstance(data["expression_behavior"], dict):
        raise CharacterValidationError(f"Identity profile '{path.name}' needs identity relationships and expression behavior.")
    prompt_blocks = data["prompt_identity_blocks"]
    if not isinstance(prompt_blocks, dict) or any(not isinstance(prompt_blocks.get(key), str) or not prompt_blocks[key].strip() for key in ("compact", "standard", "detailed")):
        raise CharacterValidationError(f"Identity profile '{path.name}' needs compact, standard, and detailed prompt identity blocks.")
    return IdentityProfile(
        character_id=character_id,
        version=data["version"],
        anchors=anchors,
        immutable_features=tuple(str(feature) for feature in immutable),
        mutable_features=frozenset(key for key, enabled in mutable.items() if enabled),
        negative_constraints=tuple(str(item) for item in negatives),
        drift_critical_features=tuple(
            item for item in data.get("drift_critical_features", [])
            if isinstance(item, dict) and isinstance(item.get("feature"), str) and isinstance(item.get("instruction"), str)
        ),
        reference_consensus=data.get("reference_consensus") if isinstance(data.get("reference_consensus"), dict) else None,
        variation_envelope=data.get("variation_envelope") if isinstance(data.get("variation_envelope"), dict) else None,
        identity_relationships=data.get("identity_relationships") if isinstance(data.get("identity_relationships"), dict) else None,
        expression_behavior=data.get("expression_behavior") if isinstance(data.get("expression_behavior"), dict) else None,
        presentation_exclusions=tuple(str(item) for item in data.get("presentation_exclusions", [])),
        critical_anchors=critical_anchors,
        strong_anchors=strong_anchors,
        signature_features=tuple(
            item for item in data.get("signature_features", [])
            if isinstance(item, dict) and isinstance(item.get("feature"), str)
        ),
        prompt_identity_blocks=dict(prompt_blocks),
    )


_EYE_PHRASE = re.compile(r"\b((?:(?:dark|light|pale|deep|bright)\s+)?(?:blue|brown|green|hazel|grey|gray|amber)(?:[- ](?:blue|brown|green|hazel|grey|gray|amber))?)\s+eyes\b", re.I)
_HAIR_PHRASE = re.compile(r"\b((?:(?:dark|light|deep|very dark|medium)\s+)?(?:black|brown|blonde|blond|auburn|red|copper|ginger|grey|gray)(?:[- ](?:brown|blonde|blond|auburn|red|copper|ginger|grey|gray))?)\s+hair\b", re.I)


def identity_color_is_locked(character_id: str, feature: str) -> bool:
    """Whether the profile establishes a colour for the requested identity trait."""
    data = json.loads(_profile_path(character_id).read_text(encoding="utf-8"))
    description = data.get("identity_lock", {}).get(feature, {}).get("description", "")
    if feature not in {"eyes", "hair"}:
        return False
    return bool(re.search(r"\b(?:blue|brown|green|hazel|grey|gray|amber|black|blonde|blond|auburn|red|copper|ginger)\b", description, re.I))


def find_identity_conflicts(character_id: str, candidate_text: str) -> tuple[str, ...]:
    """Find explicit eye or hair colour overrides that disagree with a lock."""
    path = _profile_path(character_id)
    data = json.loads(path.read_text(encoding="utf-8"))
    lock = data["identity_lock"]
    conflicts: list[str] = []
    for name, pattern in (("eyes", _EYE_PHRASE), ("hair", _HAIR_PHRASE)):
        phrases = pattern.findall(candidate_text)
        if not phrases:
            continue
        locked_text = lock.get(name, {}).get("description", "").casefold()
        locked_colors = set(re.findall(r"blue|brown|green|hazel|grey|gray|amber|black|blonde|blond|auburn|red|copper|ginger", locked_text))
        if not locked_colors:
            continue
        for phrase in phrases:
            requested_colors = {part for part in re.findall(r"blue|brown|green|hazel|grey|gray|amber|black|blonde|blond|auburn|red|copper|ginger", phrase.casefold())}
            if not requested_colors.issubset(locked_colors):
                conflicts.append(f"scene requests {phrase} {name}, conflicting with the locked {name} colour")
    return tuple(conflicts)
