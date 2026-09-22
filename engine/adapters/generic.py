"""Broadly compatible, structured natural-language prompt adapter."""

from __future__ import annotations

from engine.adapters.base import PromptAdapter, result_for, source_sections, validate_density
from engine.scene_context_models import SceneDescription


class GenericPromptAdapter(PromptAdapter):
    name = "generic"

    def render(self, scene_description: SceneDescription, density: str = "standard"):
        validate_density(density)
        sections = source_sections(scene_description, density)
        positive = "\n\n".join(f"{section.id.upper()}:\n{section.text}" for section in sections)
        negative = "identity drift; incorrect hair color; incorrect eye color; distorted anatomy; duplicate limbs; extra fingers; text; watermark"
        return result_for(self.name, scene_description, sections, positive, negative, density)
