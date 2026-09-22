"""Authoritative public gateway for prompt adapters."""

from __future__ import annotations

from engine.adapters import GeminiImageAdapter, GenericPromptAdapter, OpenAIImageAdapter, PromptAdapter


ADAPTER_REGISTRY: dict[str, PromptAdapter] = {
    "generic": GenericPromptAdapter(),
    "openai": OpenAIImageAdapter(),
    "gemini": GeminiImageAdapter(),
}


def list_adapters() -> tuple[str, ...]:
    return tuple(ADAPTER_REGISTRY)


def get_adapter(name: str) -> PromptAdapter:
    try:
        return ADAPTER_REGISTRY[name]
    except KeyError as error:
        raise ValueError(f"Unknown prompt adapter '{name}'. Available adapters: {', '.join(list_adapters())}") from error


def render_prompt(character_id: str, mode: str, adapter: str = "generic", density: str = "standard", overrides: dict[str, str] | None = None):
    """Registry-level convenience route using the public composition pipeline."""
    from engine.prompt_pipeline import build_prompt

    return build_prompt(character_id, mode, adapter, density, overrides)
