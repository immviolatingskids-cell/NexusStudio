from __future__ import annotations

from typing import Any


class CharacterValidationError(ValueError):
    """Raised when a character file violates the canonical character contract."""


REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "character_id",
    "identity",
    "appearance",
    "occupation",
    "hobbies",
    "interests",
    "personality",
    "affinities",
}

REQUIRED_IDENTITY_FIELDS = {
    "name",
    "age",
    "gender",
    "nationality",
    "home",
}

REQUIRED_APPEARANCE_FIELDS = {
    "body",
    "skin",
    "face",
    "eyes",
    "hair",
    "distinguishing_features",
    "physicality",
}

REQUIRED_BODY_FIELDS = {
    "height",
    "build",
    "proportions",
    "physical_features",
}

REQUIRED_FACE_FIELDS = {
    "shape",
    "jaw",
    "cheekbones",
    "nose",
    "lips",
    "brows",
}

REQUIRED_EYE_FIELDS = {
    "color",
    "shape",
    "size",
}

REQUIRED_HAIR_FIELDS = {
    "color",
    "length",
    "density",
    "texture",
    "framing",
}

FORBIDDEN_TOP_LEVEL_FIELDS = {
    "wardrobe",
    "environment",
    "photography",
    "negative_prompt",
    "scene",
    "camera",
    "lighting",
}


def _require_fields(
    data: dict[str, Any],
    required: set[str],
    location: str,
) -> None:
    missing = required - data.keys()

    if missing:
        fields = ", ".join(sorted(missing))
        raise CharacterValidationError(
            f"{location} is missing required field(s): {fields}"
        )


def _require_dict(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CharacterValidationError(
            f"{location} must be an object/dictionary."
        )

    return value


def _require_list(value: Any, location: str) -> list[Any]:
    if not isinstance(value, list):
        raise CharacterValidationError(
            f"{location} must be a list."
        )

    return value


def validate_character_data(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise CharacterValidationError(
            "Character JSON root must be an object."
        )

    _require_fields(
        data,
        REQUIRED_TOP_LEVEL_FIELDS,
        "character",
    )

    forbidden = FORBIDDEN_TOP_LEVEL_FIELDS.intersection(data)

    if forbidden:
        fields = ", ".join(sorted(forbidden))
        raise CharacterValidationError(
            f"Canonical character contains depiction-specific field(s): {fields}"
        )

    if not isinstance(data["schema_version"], (str, int, float)):
        raise CharacterValidationError(
            "schema_version must be a string or number."
        )

    if not isinstance(data["character_id"], str):
        raise CharacterValidationError(
            "character_id must be a string."
        )

    if not data["character_id"].strip():
        raise CharacterValidationError(
            "character_id must be a non-empty string."
        )

    identity = _require_dict(
        data["identity"],
        "identity",
    )

    _require_fields(
        identity,
        REQUIRED_IDENTITY_FIELDS,
        "identity",
    )

    if not isinstance(identity["age"], int):
        raise CharacterValidationError(
            "identity.age must be an integer."
        )

    if not 20 <= identity["age"] <= 27:
        raise CharacterValidationError(
            "identity.age must be between 20 and 27."
        )

    appearance = _require_dict(
        data["appearance"],
        "appearance",
    )

    _require_fields(
        appearance,
        REQUIRED_APPEARANCE_FIELDS,
        "appearance",
    )

    body = _require_dict(
        appearance["body"],
        "appearance.body",
    )

    _require_fields(
        body,
        REQUIRED_BODY_FIELDS,
        "appearance.body",
    )

    face = _require_dict(
        appearance["face"],
        "appearance.face",
    )

    _require_fields(
        face,
        REQUIRED_FACE_FIELDS,
        "appearance.face",
    )

    eyes = _require_dict(
        appearance["eyes"],
        "appearance.eyes",
    )

    _require_fields(
        eyes,
        REQUIRED_EYE_FIELDS,
        "appearance.eyes",
    )

    hair = _require_dict(
        appearance["hair"],
        "appearance.hair",
    )

    _require_fields(
        hair,
        REQUIRED_HAIR_FIELDS,
        "appearance.hair",
    )

    occupation = _require_dict(
        data["occupation"],
        "occupation",
    )

    if "primary" not in occupation:
        raise CharacterValidationError(
            "occupation.primary is required."
        )

    for field_name in (
        "hobbies",
        "interests",
        "personality",
    ):
        values = _require_list(
            data[field_name],
            field_name,
        )

        if not all(isinstance(item, str) for item in values):
            raise CharacterValidationError(
                f"{field_name} must contain only strings."
            )

    affinities = _require_dict(
        data["affinities"],
        "affinities",
    )

    for tag, weight in affinities.items():
        if not isinstance(tag, str):
            raise CharacterValidationError(
                "Affinity names must be strings."
            )

        if not isinstance(weight, int):
            raise CharacterValidationError(
                f"Affinity '{tag}' must use an integer weight."
            )

        if weight < -3 or weight > 3:
            raise CharacterValidationError(
                f"Affinity '{tag}' must be between -3 and 3."
            )
