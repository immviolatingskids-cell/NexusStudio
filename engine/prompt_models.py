"""Serializable, immutable contracts for model-facing prompt rendering."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PromptSection:
    """One named, inspectable portion of a rendered prompt."""

    id: str
    text: str

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "text": self.text}


@dataclass(frozen=True)
class PromptResult:
    """The deterministic output of one prompt adapter."""

    character_id: str
    adapter_name: str
    positive_prompt: str
    source_scene_mode: str
    sections: tuple[PromptSection, ...]
    negative_prompt: str | None = None
    source_metadata: dict[str, object] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "character_id": self.character_id,
            "adapter_name": self.adapter_name,
            "positive_prompt": self.positive_prompt,
            "negative_prompt": self.negative_prompt,
            "source_scene_mode": self.source_scene_mode,
            "sections": [section.to_dict() for section in self.sections],
            "source_metadata": dict(self.source_metadata),
            "warnings": list(self.warnings),
        }
