"""Serializable result contracts for visual character descriptions."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DescriptionSection:
    id: str
    heading: str
    text: str
    source_entry_ids: tuple[str, ...] = ()
    source_paths: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {"id": self.id, "heading": self.heading, "text": self.text, "source_entry_ids": list(self.source_entry_ids), "source_paths": list(self.source_paths)}


@dataclass(frozen=True)
class VisualDescription:
    character_id: str
    character_name: str
    sections: tuple[DescriptionSection, ...]
    unresolved_summary: tuple[str, ...] = ()
    canonical_fallback_paths: tuple[str, ...] = ()
    metadata: dict[str, int] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return "\n\n".join(section.text for section in self.sections)

    def to_dict(self) -> dict:
        return {"character_id": self.character_id, "character_name": self.character_name, "sections": [section.to_dict() for section in self.sections], "text": self.text, "unresolved_summary": list(self.unresolved_summary), "canonical_fallback_paths": list(self.canonical_fallback_paths), "metadata": dict(self.metadata)}
