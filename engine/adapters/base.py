"""Small shared protocol and source-section preparation for adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.prompt_models import PromptResult, PromptSection
from engine.scene_context_models import SceneDescription


DENSITIES = ("compact", "standard", "detailed")
APPEARANCE_SECTIONS = ("build", "skin", "face", "eyes", "hair", "distinguishing_features")


class PromptAdapter(ABC):
    name: str

    @abstractmethod
    def render(self, scene_description: SceneDescription, density: str = "standard") -> PromptResult:
        """Render without changing the provided scene or its source models."""


def validate_density(density: str) -> None:
    if density not in DENSITIES:
        raise ValueError(f"Unknown prompt density '{density}'. Available densities: {', '.join(DENSITIES)}")


def source_sections(scene: SceneDescription, density: str) -> tuple[PromptSection, ...]:
    """Extract only composed facts, in the explicit model-facing order."""
    validate_density(density)
    character = {section.id: section.text for section in scene.character_description.sections}
    context = scene.context
    sections = [PromptSection("subject", character["identity"])]
    # All densities retain visual identity anchors. Compact reduces scene prose,
    # rather than quietly dropping traits which distinguish the character.
    appearance = [character[key] for key in APPEARANCE_SECTIONS if key in character]
    if appearance:
        sections.append(PromptSection("appearance", " ".join(appearance)))
    scene_bits = [bit for bit in (context.wardrobe, context.environment, context.activity) if bit]
    if scene_bits:
        sections.append(PromptSection("scene", "; ".join(scene_bits)))
    if density != "compact":
        composition = [bit for bit in (context.pose, context.camera) if bit]
        if composition:
            sections.append(PromptSection("composition", "; ".join(composition)))
        if context.lighting:
            sections.append(PromptSection("lighting", context.lighting))
        if context.mood:
            sections.append(PromptSection("mood", context.mood))
    if density == "detailed":
        provenance = [
            f"scene mode: {scene.mode}",
            "preserve the described facial features and distinguishing details",
        ]
        sections.append(PromptSection("constraints", "; ".join(provenance)))
    sections.append(PromptSection("style", "photorealistic; natural skin texture; realistic proportions; sharp facial detail; coherent lighting"))
    return tuple(sections)


def result_for(name: str, scene: SceneDescription, sections: tuple[PromptSection, ...], positive: str, negative: str | None, density: str) -> PromptResult:
    return PromptResult(
        character_id=scene.character_id,
        adapter_name=name,
        positive_prompt=positive,
        negative_prompt=negative,
        source_scene_mode=scene.mode,
        sections=sections,
        source_metadata={
            "density": density,
            "defaulted_fields": scene.defaulted_fields,
            "character_context_fields": scene.character_context_fields,
            "override_fields": scene.override_fields,
        },
    )
