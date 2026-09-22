"""Structured context contracts for deterministic visual scene composition."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from engine.composer_models import DescriptionSection, VisualDescription


@dataclass(frozen=True)
class SceneContext:
    mode: str
    activity: str | None = None
    environment: str | None = None
    wardrobe: str | None = None
    pose: str | None = None
    camera: str | None = None
    lighting: str | None = None
    mood: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SceneDescription:
    character_id: str
    mode: str
    character_description: VisualDescription
    context: SceneContext
    sections: tuple[DescriptionSection, ...]
    defaulted_fields: tuple[str, ...] = ()
    character_context_fields: tuple[str, ...] = ()
    override_fields: tuple[str, ...] = ()

    @property
    def text(self) -> str:
        return "\n\n".join(section.text for section in self.sections)

    def to_dict(self) -> dict:
        return {"character_id": self.character_id, "mode": self.mode, "character_description": self.character_description.to_dict(), "context": self.context.to_dict(), "sections": [section.to_dict() for section in self.sections], "defaulted_fields": list(self.defaulted_fields), "character_context_fields": list(self.character_context_fields), "override_fields": list(self.override_fields), "text": self.text}
