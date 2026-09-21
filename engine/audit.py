"""Read-only integrity audit for data, vocabulary, and local configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

from config import REFERENCE_IMAGES_DIR
from engine.identity import load_identity_profile
from engine.loader import load_all_characters
from pools.registry import BY_ID, ENTRIES, registry_issues


@dataclass(frozen=True)
class AuditReport:
    characters: int
    pool_entries: int
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {"characters": self.characters, "pool_entries": self.pool_entries, "errors": list(self.errors), "warnings": list(self.warnings), "ok": self.ok}


def run_audit() -> AuditReport:
    errors = list(registry_issues())
    warnings: list[str] = []
    characters = load_all_characters()
    for character in characters:
        load_identity_profile(character.character_id)
        image = REFERENCE_IMAGES_DIR / f"{character.character_id.split('_')[0]}.png"
        if not image.is_file():
            errors.append(f"Missing reference image for {character.character_id}: {image.name}")
    if not os.getenv("GEMINI_API_KEY"):
        warnings.append("GEMINI_API_KEY is not configured; live Gemini generation is unavailable.")
    if len(BY_ID) != len(ENTRIES):
        errors.append("Pool registry has duplicate IDs.")
    return AuditReport(len(characters), len(ENTRIES), tuple(errors), tuple(warnings))
