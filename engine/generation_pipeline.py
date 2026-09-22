"""Public image-execution pipeline built strictly on the prompt boundary."""

from __future__ import annotations

from pathlib import Path

from config import DEFAULT_IMAGE_PROVIDER, GEMINI_IMAGE_MODEL
from engine.generation_models import GeneratedAsset, GenerationRequest, GenerationResult
from engine.output_manager import output_path_for
from engine.prompt_pipeline import build_prompt
from engine.provider_registry import get_provider


def generate_image(character_id: str, mode: str, provider: str = DEFAULT_IMAGE_PROVIDER, adapter: str | None = None, density: str = "standard", overrides: dict[str, str] | None = None, dry_run: bool = False, output_dir: str | Path | None = None) -> GenerationResult:
    """Build a prompt once, then execute it at the provider edge."""
    image_provider = get_provider(provider)
    selected_adapter = adapter or image_provider.preferred_adapter
    prompt = build_prompt(character_id, mode, selected_adapter, density, overrides)
    model = image_provider.model if provider == "gemini" else "deterministic-fake"
    request = GenerationRequest(
        character_id=prompt.character_id, adapter=selected_adapter, scene_mode=mode,
        density=density, positive_prompt=prompt.positive_prompt,
        negative_prompt=prompt.negative_prompt, provider=provider, model=model,
        output_dir=str(output_dir) if output_dir is not None else None,
    )
    warnings = list(prompt.warnings)
    if selected_adapter != image_provider.preferred_adapter:
        warnings.append(f"{provider.title()} provider used with {selected_adapter} adapter.")
    if dry_run:
        mime_type = "image/png" if provider == "gemini" else "text/plain"
        path = output_path_for(request, mime_type)
        asset = GeneratedAsset(str(path), mime_type)
        return GenerationResult(True, provider, model, prompt.character_id, mode, selected_adapter, (asset,), mime_type, tuple(warnings), {"request": request.to_dict()}, dry_run=True)
    result = image_provider.generate(request)
    return GenerationResult(
        result.success, result.provider, result.model, result.character_id,
        result.scene_mode, result.adapter, result.assets, result.mime_type,
        tuple((*warnings, *result.warnings)), result.provider_metadata, result.error,
        result.dry_run,
    )
