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


def validate_character_data(data: dict[str, Any], *, character: str | None = None) -> None:
    """Validate a canonical character record without changing its contents.

    ``character`` is a source label supplied by the loader so failures identify
    the affected record even when its own ``character_id`` is absent or invalid.
    """
    label = character or (
        data.get("character_id", "<unknown>") if isinstance(data, dict) else "<unknown>"
    )

    def fail(location: str, reason: str) -> None:
        raise CharacterValidationError(f"{label}.{location}: {reason}")

    if not isinstance(data, dict):
        fail("$", "expected object/dictionary")

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
        fail("character_id", "expected string")

    if not data["character_id"].strip():
        fail("character_id", "expected non-empty string")

    identity = _require_dict(
        data["identity"],
        "identity",
    )

    _require_fields(
        identity,
        REQUIRED_IDENTITY_FIELDS,
        "identity",
    )

    for field_name in ("name", "gender", "nationality", "home"):
        value = identity[field_name]
        if not isinstance(value, str) or not value.strip():
            fail(f"identity.{field_name}", "expected non-empty string")

    if not isinstance(identity["age"], int) or isinstance(identity["age"], bool):
        fail("identity.age", "expected integer")

    if not 18 <= identity["age"] <= 120:
        fail("identity.age", "expected sensible adult age (18-120)")

    appearance = _require_dict(
        data["appearance"],
        "appearance",
    )

    _require_fields(
        appearance,
        REQUIRED_APPEARANCE_FIELDS,
        "appearance",
    )

    for section in ("skin", "physicality"):
        _require_dict(appearance[section], f"appearance.{section}")

    _require_list(appearance["distinguishing_features"], "appearance.distinguishing_features")

    body = _require_dict(
        appearance["body"],
        "appearance.body",
    )

    _require_fields(
        body,
        REQUIRED_BODY_FIELDS,
        "appearance.body",
    )

    for field_name in ("height", "build", "proportions"):
        if not isinstance(body[field_name], str):
            fail(f"appearance.body.{field_name}", "expected string")
    _require_list(body["physical_features"], "appearance.body.physical_features")

    face = _require_dict(
        appearance["face"],
        "appearance.face",
    )

    _require_fields(
        face,
        REQUIRED_FACE_FIELDS,
        "appearance.face",
    )

    for field_name in ("shape", "jaw", "cheekbones"):
        if not isinstance(face[field_name], str):
            fail(f"appearance.face.{field_name}", "expected string")

    eyes = _require_dict(
        appearance["eyes"],
        "appearance.eyes",
    )

    _require_fields(
        eyes,
        REQUIRED_EYE_FIELDS,
        "appearance.eyes",
    )

    for field_name in REQUIRED_EYE_FIELDS:
        if not isinstance(eyes[field_name], str):
            fail(f"appearance.eyes.{field_name}", "expected string")

    hair = _require_dict(
        appearance["hair"],
        "appearance.hair",
    )

    _require_fields(
        hair,
        REQUIRED_HAIR_FIELDS,
        "appearance.hair",
    )

    for field_name in REQUIRED_HAIR_FIELDS:
        if not isinstance(hair[field_name], str):
            fail(f"appearance.hair.{field_name}", "expected string")

    occupation = _require_dict(
        data["occupation"],
        "occupation",
    )

    if not isinstance(occupation.get("primary"), str) or not occupation["primary"].strip():
        fail("occupation.primary", "expected non-empty string")

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
