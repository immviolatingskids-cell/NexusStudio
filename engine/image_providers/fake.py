"""Deterministic, offline image provider for pipeline testing."""

from __future__ import annotations

import hashlib
from pathlib import Path

from engine.generation_errors import GenerationError
from engine.generation_models import GenerationRequest, GenerationResult
from engine.image_providers.base import ImageProvider
from engine.output_manager import write_asset


class FakeImageProvider(ImageProvider):
    name = "fake"
    preferred_adapter = "generic"

    def __init__(self, *, fail: bool = False, output_dir: Path | None = None) -> None:
        self.fail = fail
        self.output_dir = output_dir

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if self.fail:
            raise GenerationError("Fake provider forced failure.")
        digest = hashlib.sha256(request.positive_prompt.encode("utf-8")).hexdigest()
        payload = f"CharacterStudio fake image\n{digest}\n".encode("utf-8")
        asset = write_asset(request, payload, "text/plain", output_dir=self.output_dir, provider_metadata={"digest": digest})
        return GenerationResult(True, self.name, request.model, request.character_id, request.scene_mode, request.adapter, (asset,), "text/plain", provider_metadata={"digest": digest})
