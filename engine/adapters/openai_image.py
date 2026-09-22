"""Instruction-oriented renderer; semantic priority is owned by the compiler."""

from engine.adapters.base import PromptAdapter, result_for, source_sections
from engine.prompt_plan import PromptPlan


class OpenAIImageAdapter(PromptAdapter):
    name = "openai"

    def render(self, plan: PromptPlan):
        sections = source_sections(plan)
        positive = "Create an image with this direction: " + " ".join(section.text.rstrip(".") + "." for section in sections)
        return result_for(self.name, plan, sections, positive, None)
