"""Structured descriptive renderer; semantic priority is owned by the compiler."""

from engine.adapters.base import PromptAdapter, prose_paragraphs, result_for, source_sections
from engine.prompt_plan import PromptPlan


class GeminiImageAdapter(PromptAdapter):
    name = "gemini"

    def render(self, plan: PromptPlan):
        sections = source_sections(plan)
        positive = prose_paragraphs(sections)
        return result_for(self.name, plan, sections, positive, None)
