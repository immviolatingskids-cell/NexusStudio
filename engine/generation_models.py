"""Normalized, serializable contracts for one image-generation attempt."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GenerationRequest:
    character_id: str
    adapter: str
    scene_mode: str
    density: str
    positive_prompt: str
    provider: str
    model: str
    negative_prompt: str | None = None
    output_dir: str | None = None
    seed: int | None = None

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class GeneratedAsset:
    file_path: str
    mime_type: str
    width: int | None = None
    height: int | None = None
    provider_asset_id: str | None = None
    content_hash: str | None = None

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class GenerationResult:
    success: bool
    provider: str
    model: str
    character_id: str
    scene_mode: str
    adapter: str
    assets: tuple[GeneratedAsset, ...] = ()
    mime_type: str | None = None
    warnings: tuple[str, ...] = ()
    provider_metadata: dict[str, object] = field(default_factory=dict)
    error: str | None = None
    dry_run: bool = False
    record_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "success": self.success, "provider": self.provider, "model": self.model,
            "character_id": self.character_id, "scene_mode": self.scene_mode,
            "adapter": self.adapter, "assets": [asset.to_dict() for asset in self.assets],
            "mime_type": self.mime_type, "warnings": list(self.warnings),
            "provider_metadata": dict(self.provider_metadata), "error": self.error,
            "dry_run": self.dry_run,
            "record_id": self.record_id,
        }
