"""Immutable, local records for offline preview takes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import hashlib

from config import OUTPUT_DIR
from config import CHARACTERS_DIR
from engine.composer import compose_negative_prompt, compose_prompt
from engine.prompts import compose_prompt_document
from engine.scene_models import ResolvedScene
from engine.versions import MANIFEST_VERSION, TAKE_VERSION


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_fingerprints(character_id: str) -> dict[str, str]:
    character_path = next((path for path in CHARACTERS_DIR.glob("*.json") if json.loads(path.read_text(encoding="utf-8")).get("character_id") == character_id), None)
    identity_path = CHARACTERS_DIR / "identity" / f"{character_id}.json"
    return {
        "character": _sha256(character_path) if character_path else "missing",
        "identity": _sha256(identity_path) if identity_path.is_file() else "missing",
    }


def _manifest_path() -> Path:
    return OUTPUT_DIR / "take-manifest.json"


def _load_manifest() -> dict:
    path = _manifest_path()
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"schema_version": MANIFEST_VERSION, "takes": []}


def _write_manifest(manifest: dict) -> None:
    path = _manifest_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def record_take(scene: ResolvedScene, *, provider: str = "offline-preview", model: str = "", parent_take_id: str | None = None, output_path: Path | None = None, provider_metadata: dict | None = None) -> Path:
    """Store an immutable take and append a compact manifest entry."""
    record_id = uuid4().hex
    directory = OUTPUT_DIR / "records"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{record_id}.json"
    payload = {
        "schema_version": TAKE_VERSION,
        "take_id": record_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider": {"name": provider, "model": model, "metadata": provider_metadata or {}},
        "parent_take_id": parent_take_id,
        "source_fingerprints": _source_fingerprints(scene.brief.character_id),
        "scene": scene.to_dict(),
        "prompt_document": compose_prompt_document(scene).to_dict(),
        "prompt_preview": compose_prompt(scene),
        "negative_prompt": compose_negative_prompt(scene),
        "output": {"path": str(output_path) if output_path else None, "sha256": _sha256(output_path) if output_path else None},
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = _load_manifest()
    manifest["takes"].append({"take_id": record_id, "record": str(path), "character_id": scene.brief.character_id, "created_at": payload["created_at"], "provider": provider, "record_sha256": _sha256(path)})
    _write_manifest(manifest)
    return path


def list_takes() -> list[dict]:
    return _load_manifest()["takes"]


def load_take(take_id: str) -> dict:
    for item in list_takes():
        if item["take_id"] == take_id:
            return json.loads(Path(item["record"]).read_text(encoding="utf-8"))
    raise KeyError(f"Take '{take_id}' was not found.")


def verify_take(take_id: str) -> bool:
    for item in list_takes():
        if item["take_id"] == take_id:
            path = Path(item["record"])
            payload = json.loads(path.read_text(encoding="utf-8"))
            output = payload["output"]
            return _sha256(path) == item["record_sha256"] and (not output["path"] or (Path(output["path"]).is_file() and _sha256(Path(output["path"])) == output["sha256"]))
    raise KeyError(f"Take '{take_id}' was not found.")
