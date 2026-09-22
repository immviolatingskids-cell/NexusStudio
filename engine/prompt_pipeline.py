"""Public, non-duplicating route from composed scene to prompt result."""

from __future__ import annotations

from engine.adapter_registry import get_adapter
from engine.loader import load_character
from engine.prompt_compiler import compile_prompt_plan
from engine.prompt_models import PromptResult
from engine.prompt_refiner import RefinedPromptResult, TextRefiner, refine_prompt
from engine.scene_composer import compose_scene_by_id


def build_prompt(character_id: str, mode: str, adapter: str = "generic", density: str = "standard", overrides: dict[str, str] | None = None) -> PromptResult:
    """Compose once through the existing pipeline and render at its edge."""
    character = load_character(character_id)
    scene = compose_scene_by_id(character_id, mode, overrides)
    plan = compile_prompt_plan(character, scene.character_description, scene, density)
    return get_adapter(adapter).render(plan)


def render_prompt(character_id: str, mode: str, adapter: str = "generic", density: str = "standard", overrides: dict[str, str] | None = None) -> PromptResult:
    """Convenience alias for callers that prefer registry-style naming."""
    return build_prompt(character_id, mode, adapter, density, overrides)


def build_refined_prompt(
    character_id: str,
    mode: str,
    adapter: str = "generic",
    density: str = "standard",
    overrides: dict[str, str] | None = None,
    refinement_mode: str = "off",
    refiner: TextRefiner | None = None,
) -> RefinedPromptResult:
    """Build deterministically first, then apply the optional text-only pass."""
    return refine_prompt(build_prompt(character_id, mode, adapter, density, overrides), refinement_mode, refiner)
