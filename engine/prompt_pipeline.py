"""Public, non-duplicating route from composed scene to prompt result."""

from __future__ import annotations

from engine.adapter_registry import get_adapter
from engine.prompt_models import PromptResult
from engine.scene_composer import compose_scene_by_id


def build_prompt(character_id: str, mode: str, adapter: str = "generic", density: str = "standard", overrides: dict[str, str] | None = None) -> PromptResult:
    """Compose once through the existing pipeline and render at its edge."""
    scene = compose_scene_by_id(character_id, mode, overrides)
    return get_adapter(adapter).render(scene, density)


def render_prompt(character_id: str, mode: str, adapter: str = "generic", density: str = "standard", overrides: dict[str, str] | None = None) -> PromptResult:
    """Convenience alias for callers that prefer registry-style naming."""
    return build_prompt(character_id, mode, adapter, density, overrides)
