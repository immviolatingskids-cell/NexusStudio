"""Safe, portable asset and sidecar writing for image providers."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from config import OUTPUT_DIR
from engine.generation_errors import OutputWriteError
from engine.generation_models import GeneratedAsset, GenerationRequest


MIME_EXTENSIONS = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "text/plain": "txt"}


def _safe(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9_-]+", "_", value.casefold()).strip("_-")
    if not cleaned:
        raise OutputWriteError("Output path component is empty after sanitization.")
    return cleaned


def output_path_for(request: GenerationRequest, mime_type: str, output_dir: Path | None = None) -> Path:
    extension = MIME_EXTENSIONS.get(mime_type)
    if extension is None:
        raise OutputWriteError(f"Unsupported generated MIME type '{mime_type}'.")
    root = output_dir or (Path(request.output_dir) if request.output_dir else OUTPUT_DIR)
    directory = root / _safe(request.character_id) / _safe(request.scene_mode)
    stem = f"{_safe(request.character_id)}_{_safe(request.scene_mode)}_{_safe(request.provider)}"
    index = 1
    while (directory / f"{stem}_{index:03d}.{extension}").exists():
        index += 1
    return directory / f"{stem}_{index:03d}.{extension}"


def write_asset(request: GenerationRequest, image_bytes: bytes, mime_type: str, *, output_dir: Path | None = None, provider_asset_id: str | None = None, provider_metadata: dict[str, object] | None = None) -> GeneratedAsset:
    path = output_path_for(request, mime_type, output_dir)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(image_bytes)
        digest = hashlib.sha256(image_bytes).hexdigest()
        sidecar = {
            "character_id": request.character_id, "scene_mode": request.scene_mode,
            "density": request.density, "adapter": request.adapter,
            "provider": request.provider, "model": request.model,
            "positive_prompt": request.positive_prompt, "negative_prompt": request.negative_prompt,
            "output_filename": path.name, "mime_type": mime_type,
            "content_hash": digest, "provider_metadata": provider_metadata or {},
        }
        path.with_suffix(".json").write_text(json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as error:
        raise OutputWriteError(f"Could not write generated output '{path}': {error}") from error
    return GeneratedAsset(str(path), mime_type, provider_asset_id=provider_asset_id, content_hash=digest)
