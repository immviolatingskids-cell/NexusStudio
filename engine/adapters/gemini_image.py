"""Descriptive prose renderer for Gemini image systems, with no API coupling."""

from __future__ import annotations

from engine.adapters.base import PromptAdapter, result_for, source_sections, validate_density
from engine.scene_context_models import SceneDescription


class GeminiImageAdapter(PromptAdapter):
    name = "gemini"

    def render(self, scene_description: SceneDescription, density: str = "standard"):
        validate_density(density)
        sections = source_sections(scene_description, density)
        by_id = {section.id: section.text for section in sections}
        prose = [f"Create a coherent photorealistic scene featuring {by_id['subject']}"]
        for section_id in ("appearance", "scene", "composition", "lighting", "mood", "constraints", "style"):
            if section_id in by_id:
                prose.append(by_id[section_id])
        positive = "\n\n".join(f"{sentence.rstrip('.')}." for sentence in prose)
        return result_for(self.name, scene_description, sections, positive, None, density)
