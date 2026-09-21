from __future__ import annotations

import json
from pathlib import Path

from config import CHARACTERS_DIR
from engine.models import Character
from engine.rules import (
    CharacterValidationError,
    validate_character_data,
)


def list_character_ids() -> list[str]:
    """Return canonical character filenames without their .json suffix."""
    return sorted(path.stem for path in CHARACTERS_DIR.glob("*.json") if path.is_file())


class CharacterNotFoundError(FileNotFoundError):
    """Raised when a requested character JSON file does not exist."""


def get_character_path(character_name: str) -> Path:
    safe_name = character_name.strip().lower()

    return CHARACTERS_DIR / f"{safe_name}.json"


def load_character(character_name: str) -> Character:
    if not isinstance(character_name, str) or not character_name.strip():
        raise CharacterNotFoundError("Character ID must be a non-empty string")

    path = get_character_path(character_name)

    if not path.exists():
        for candidate in CHARACTERS_DIR.glob("*.json"):
            try:
                with candidate.open("r", encoding="utf-8") as file:
                    candidate_data = json.load(file)
            except (OSError, json.JSONDecodeError):
                continue

            if (
                isinstance(candidate_data, dict)
                and candidate_data.get("character_id") == character_name.strip()
            ):
                path = candidate
                break

    if not path.exists():
        raise CharacterNotFoundError(
            f"Character '{character_name}' was not found at: {path}"
        )

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as exc:
        raise CharacterValidationError(
            f"Invalid JSON in '{path.name}': "
            f"line {exc.lineno}, column {exc.colno}"
        ) from exc

    validate_character_data(data)

    return Character.from_dict(data)


def load_all_characters() -> list[Character]:
    """Load all discovered characters through the authoritative loader."""
    return [load_character(character_id) for character_id in list_character_ids()]
