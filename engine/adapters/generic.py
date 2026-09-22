"""Broadly compatible renderer of an already selected prompt plan."""

from engine.adapters.base import PromptAdapter, result_for, source_sections
from engine.prompt_plan import PromptPlan


class GenericPromptAdapter(PromptAdapter):
    name = "generic"

    def render(self, plan: PromptPlan):
        sections = source_sections(plan)
        positive = "\n\n".join(section.text for section in sections)
        negative = "identity drift; incorrect hair color; incorrect eye color; distorted anatomy; duplicate limbs; extra fingers; text; watermark"
        return result_for(self.name, plan, sections, positive, negative)
