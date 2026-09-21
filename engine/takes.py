"""Immutable, local records for offline preview takes."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from config import OUTPUT_DIR
from engine.composer import compose_negative_prompt, compose_prompt
from engine.scene_models import ResolvedScene


def record_take(scene: ResolvedScene) -> Path:
    """Store the exact resolved direction without attempting image generation."""
    record_id = uuid4().hex
    directory = OUTPUT_DIR / "records"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{record_id}.json"
    payload = {
        "schema_version": "nexus_studio.take.v1",
        "take_id": record_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider": "offline-preview",
        "scene_brief": {
            **asdict(scene.brief),
            "locks": sorted(scene.brief.locks),
        },
        "selections": scene.selections,
        "identity_anchors": scene.identity_anchors,
        "prompt_preview": compose_prompt(scene),
        "negative_prompt": compose_negative_prompt(scene),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
