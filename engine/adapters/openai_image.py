"""Concise instruction-oriented renderer for OpenAI image systems."""

from __future__ import annotations

from engine.adapters.base import PromptAdapter, result_for, source_sections, validate_density
from engine.scene_context_models import SceneDescription


class OpenAIImageAdapter(PromptAdapter):
    name = "openai"

    def render(self, scene_description: SceneDescription, density: str = "standard"):
        validate_density(density)
        sections = source_sections(scene_description, density)
        by_id = {section.id: section.text for section in sections}
        parts = [f"Create a photorealistic image of {by_id['subject']}"]
        for section_id in ("appearance", "scene", "composition", "lighting", "mood", "style", "constraints"):
            if section_id in by_id:
                parts.append(by_id[section_id])
        parts.append("Keep her identity, hair color, eye color, and defining facial features consistent.")
        positive = " ".join(f"{part.rstrip('.')}." for part in parts)
        return result_for(self.name, scene_description, sections, positive, None, density)
