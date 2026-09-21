"""Explicit, backup-safe migration support for canonical character records."""

from __future__ import annotations

import json
from pathlib import Path

from engine.versions import CHARACTER_VERSION, LEGACY_CHARACTER_VERSION


class MigrationError(ValueError):
    pass


def character_migration_preview(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    version = str(data.get("schema_version", ""))
    if version == CHARACTER_VERSION:
        return {"path": str(path), "changed": False, "from": version, "to": version}
    if version != LEGACY_CHARACTER_VERSION:
        raise MigrationError(f"Unsupported character schema version '{version}' in {path.name}.")
    return {"path": str(path), "changed": True, "from": version, "to": CHARACTER_VERSION}


def migrate_character_file(path: Path, *, apply: bool = False) -> dict:
    preview = character_migration_preview(path)
    if not apply or not preview["changed"]:
        return preview
    data = json.loads(path.read_text(encoding="utf-8"))
    backup = path.with_suffix(".v0.1.backup.json")
    if backup.exists():
        raise MigrationError(f"Refusing to overwrite existing backup {backup.name}.")
    backup.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    data["schema_version"] = CHARACTER_VERSION
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {**preview, "backup": str(backup)}
