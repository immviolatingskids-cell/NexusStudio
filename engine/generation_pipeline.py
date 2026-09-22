"""Public image-execution pipeline built strictly on the prompt boundary."""

from __future__ import annotations

from pathlib import Path

from config import DEFAULT_IMAGE_PROVIDER, OUTPUT_DIR
from engine.generation_models import GeneratedAsset, GenerationRequest, GenerationResult
from engine.generation_errors import GenerationError, ProviderUnavailableError
from engine.generation_records import RecordAsset, build_record
from engine.loader import load_character
from engine.output_manager import output_path_for
from engine.prompt_pipeline import build_prompt
from engine.provider_registry import get_provider
from engine.record_store import save_record


def _character_snapshot_hash(character_id: str) -> str:
    import hashlib
    import json
    character = load_character(character_id)
    snapshot = {"identity": character.identity.__dict__, "appearance": character.appearance}
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _record_assets(result: GenerationResult, root: Path) -> tuple[RecordAsset, ...]:
    return tuple(RecordAsset(str(Path(asset.file_path).relative_to(root)), asset.mime_type, asset.content_hash) for asset in result.assets)


def generate_image(character_id: str, mode: str, provider: str = DEFAULT_IMAGE_PROVIDER, adapter: str | None = None, density: str = "standard", overrides: dict[str, str] | None = None, dry_run: bool = False, output_dir: str | Path | None = None, record_failures: bool = False, model: str | None = None) -> GenerationResult:
    """Build a prompt once, then execute it at the provider edge."""
    image_provider = get_provider(provider)
    selected_adapter = adapter or image_provider.preferred_adapter
    prompt = build_prompt(character_id, mode, selected_adapter, density, overrides)
    model = model or (image_provider.model if provider == "gemini" else "deterministic-fake")
    request = GenerationRequest(
        character_id=prompt.character_id, adapter=selected_adapter, scene_mode=mode,
        density=density, positive_prompt=prompt.positive_prompt,
        negative_prompt=prompt.negative_prompt, provider=provider, model=model,
        output_dir=str(output_dir) if output_dir is not None else None,
    )
    warnings = list(prompt.warnings)
    if selected_adapter != image_provider.preferred_adapter:
        warnings.append(f"{provider.title()} provider used with {selected_adapter} adapter.")
    root = Path(output_dir) if output_dir is not None else Path(request.output_dir) if request.output_dir else OUTPUT_DIR
    if dry_run:
        mime_type = "image/png" if provider == "gemini" else "text/plain"
        path = output_path_for(request, mime_type)
        asset = GeneratedAsset(str(path), mime_type)
        return GenerationResult(True, provider, model, prompt.character_id, mode, selected_adapter, (asset,), mime_type, tuple(warnings), {"request": request.to_dict()}, dry_run=True)
    try:
        result = image_provider.generate(request)
    except (GenerationError, ProviderUnavailableError) as error:
        if not record_failures:
            raise
        record = build_record(character_id=prompt.character_id, scene_mode=mode, scene_overrides=overrides, adapter=selected_adapter, density=density, provider=provider, model=model, positive_prompt=prompt.positive_prompt, negative_prompt=prompt.negative_prompt, assets=(), status="failed", character_snapshot_hash=_character_snapshot_hash(prompt.character_id), warnings=tuple(warnings), error=str(error))
        save_record(record, root)
        return GenerationResult(False, provider, model, prompt.character_id, mode, selected_adapter, warnings=tuple(warnings), error=str(error), record_id=record.record_id)
    final = GenerationResult(
        result.success, result.provider, result.model, result.character_id,
        result.scene_mode, result.adapter, result.assets, result.mime_type,
        tuple((*warnings, *result.warnings)), result.provider_metadata, result.error,
        result.dry_run,
    )
    record = build_record(character_id=prompt.character_id, scene_mode=mode, scene_overrides=overrides, adapter=selected_adapter, density=density, provider=provider, model=model, positive_prompt=prompt.positive_prompt, negative_prompt=prompt.negative_prompt, assets=_record_assets(final, root), status="success", character_snapshot_hash=_character_snapshot_hash(prompt.character_id), provider_metadata=final.provider_metadata, warnings=final.warnings)
    save_record(record, root)
    return GenerationResult(**{**final.__dict__, "record_id": record.record_id})
