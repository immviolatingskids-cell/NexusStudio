"""Versioned, immutable records for generation events and reproduction."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


RECORD_VERSION = 1


def _fingerprint(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def request_fingerprint_for(*, character_id: str, scene_mode: str, scene_overrides: dict[str, str] | None, adapter: str, density: str, provider: str, model: str, positive_prompt: str, negative_prompt: str | None) -> str:
    return _fingerprint({"character_id": character_id, "scene_mode": scene_mode, "scene_overrides": dict(scene_overrides or {}), "adapter": adapter, "density": density, "provider": provider, "model": model, "positive_prompt": positive_prompt, "negative_prompt": negative_prompt})


def new_record_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"gen_{stamp}_{uuid4().hex[:6]}"


@dataclass(frozen=True)
class RecordAsset:
    relative_path: str
    mime_type: str
    content_hash: str | None = None


@dataclass(frozen=True)
class GenerationRecord:
    record_id: str
    created_at: str
    character_id: str
    scene_mode: str
    scene_overrides: dict[str, str]
    adapter: str
    density: str
    provider: str
    model: str
    positive_prompt: str
    negative_prompt: str | None
    assets: tuple[RecordAsset, ...]
    status: str
    request_fingerprint: str
    prompt_fingerprint: str
    character_snapshot_hash: str
    provider_metadata: dict[str, object] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    error: str | None = None
    record_version: int = RECORD_VERSION

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["assets"] = [asdict(asset) for asset in self.assets]
        payload["warnings"] = list(self.warnings)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "GenerationRecord":
        return cls(**{**payload, "assets": tuple(RecordAsset(**item) for item in payload.get("assets", [])), "warnings": tuple(payload.get("warnings", []))})


def build_record(*, character_id: str, scene_mode: str, scene_overrides: dict[str, str] | None, adapter: str, density: str, provider: str, model: str, positive_prompt: str, negative_prompt: str | None, assets: tuple[RecordAsset, ...], status: str, character_snapshot_hash: str, provider_metadata: dict[str, object] | None = None, warnings: tuple[str, ...] = (), error: str | None = None) -> GenerationRecord:
    overrides = dict(scene_overrides or {})
    request_fingerprint = request_fingerprint_for(character_id=character_id, scene_mode=scene_mode, scene_overrides=overrides, adapter=adapter, density=density, provider=provider, model=model, positive_prompt=positive_prompt, negative_prompt=negative_prompt)
    return GenerationRecord(new_record_id(), datetime.now(timezone.utc).isoformat(), character_id, scene_mode, overrides, adapter, density, provider, model, positive_prompt, negative_prompt, assets, status, request_fingerprint, _fingerprint({"positive_prompt": positive_prompt, "negative_prompt": negative_prompt}), character_snapshot_hash, dict(provider_metadata or {}), tuple(warnings), error)
