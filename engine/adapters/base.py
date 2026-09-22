"""Thin model-facing adapters for already compiled prompt plans."""

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.prompt_models import PromptResult, PromptSection
from engine.prompt_plan import PromptPlan


DENSITIES = ("compact", "standard", "detailed")


class PromptAdapter(ABC):
    name: str

    @abstractmethod
    def render(self, plan: PromptPlan) -> PromptResult:
        """Render without altering the compiler's semantic choices."""


def validate_density(density: str) -> None:
    if density not in DENSITIES:
        raise ValueError(f"Unknown prompt density '{density}'. Available densities: {', '.join(DENSITIES)}")


def source_sections(plan: PromptPlan) -> tuple[PromptSection, ...]:
    """Expose compiler-selected material in one explicit order."""
    validate_density(plan.density)
    if plan.identity_block and plan.character_name.casefold() in plan.identity_block.casefold():
        subject = f"{plan.image_intent}."
    else:
        subject = f"{plan.image_intent} of {plan.subject_identity}."
    sections = [PromptSection("subject", subject)]
    if plan.identity_block:
        identity_text = plan.identity_block.rstrip()
        if identity_text.endswith((".", "!", "?")):
            identity_text = identity_text[:-1]
        sections.append(PromptSection("identity", identity_text))
    elif plan.identity_anchors:
        clauses = tuple(item.strip() for item in plan.identity_anchors if item.strip())
        identity_text = " ".join(item if item.endswith((".", "!", "?")) else item + "." for item in clauses)
        sections.append(PromptSection("identity", identity_text))
    identity_support = not plan.identity_block
    for section_id, text in (("body", plan.body_description if identity_support else None), ("face", plan.face_description if identity_support else None), ("hair", plan.hair_description if identity_support else None), ("wardrobe", plan.wardrobe)):
        if text:
            sections.append(PromptSection(section_id, text))
    scene_fields = (("environment", plan.environment), ("action", plan.activity), ("composition", plan.composition)) if plan.mode == "environmental" else (("action", plan.activity), ("environment", plan.environment), ("composition", plan.composition))
    for section_id, text in scene_fields:
        if text:
            sections.append(PromptSection(section_id, text))
    for section_id, text in (("lighting", plan.lighting), ("atmosphere", plan.atmosphere)):
        if text:
            sections.append(PromptSection(section_id, text))
    sections.extend((PromptSection("realism", ", ".join(plan.quality_constraints)), PromptSection("constraints", "; ".join(plan.identity_constraints))))
    return tuple(sections)


def prose_paragraphs(sections: tuple[PromptSection, ...]) -> str:
    """Group fixed compiler sections into readable image-direction paragraphs."""
    by_id = {section.id: section.text for section in sections}
    groups = (
        ("subject", "identity", "body", "face", "hair"),
        ("wardrobe", "action", "environment"),
        ("composition", "lighting", "atmosphere"),
        ("realism", "constraints"),
    )
    return "\n\n".join(_sentence_join(by_id[name] for name in group if name in by_id) for group in groups if any(name in by_id for name in group))


def _sentence_join(parts) -> str:
    """Join complete clauses without allowing final constraints to run on."""
    values = [part.strip() for part in parts if part and part.strip()]
    return " ".join(value if value.endswith((".", "!", "?")) else value + "." for value in values)


def result_for(name: str, plan: PromptPlan, sections: tuple[PromptSection, ...], positive: str, negative: str | None) -> PromptResult:
    return PromptResult(
        character_id=plan.character_id,
        adapter_name=name,
        positive_prompt=positive,
        negative_prompt=negative,
        source_scene_mode=plan.mode,
        sections=sections,
        source_metadata={
            "density": plan.density,
            "prompt_plan": plan.to_dict(),
            **plan.source_metadata,
        },
    )
