"""Loading of character-specific immutable visual identity profiles."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import CHARACTERS_DIR
from engine.rules import CharacterValidationError


IDENTITY_DIR = CHARACTERS_DIR / "identity"


@dataclass(frozen=True)
class IdentityProfile:
    character_id: str
    anchors: tuple[str, ...]
    immutable_features: tuple[str, ...]
    mutable_features: frozenset[str]
    negative_constraints: tuple[str, ...]


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
    identity_lock = data.get("identity_lock")
    if not isinstance(identity_lock, dict) or not identity_lock:
        raise CharacterValidationError(f"Identity profile '{path.name}' needs identity_lock entries.")
    anchors = tuple(
        value["description"] for value in identity_lock.values()
        if isinstance(value, dict) and isinstance(value.get("description"), str)
    )
    immutable = data.get("immutable_features")
    mutable = data.get("mutable_features")
    negatives = data.get("negative_identity_constraints")
    if not anchors or not isinstance(immutable, list) or not isinstance(mutable, dict) or not isinstance(negatives, list):
        raise CharacterValidationError(f"Identity profile '{path.name}' has an incomplete identity contract.")
    return IdentityProfile(
        character_id=character_id,
        anchors=anchors,
        immutable_features=tuple(str(feature) for feature in immutable),
        mutable_features=frozenset(key for key, enabled in mutable.items() if enabled),
        negative_constraints=tuple(str(item) for item in negatives),
    )
