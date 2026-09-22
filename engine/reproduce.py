"""Rebuild a saved request; image equality is never promised by default."""

from __future__ import annotations

from pathlib import Path

from engine.generation_pipeline import generate_image
from engine.record_store import load_record


def reproduce_generation(record_id: str, provider: str | None = None, dry_run: bool = False, output_root: Path | None = None):
    record = load_record(record_id, output_root)
    selected_provider = provider or record.provider
    selected_model = record.model if selected_provider == record.provider else None
    return generate_image(record.character_id, record.scene_mode, selected_provider, record.adapter, record.density, record.scene_overrides, dry_run, output_root, record_failures=True, model=selected_model)
