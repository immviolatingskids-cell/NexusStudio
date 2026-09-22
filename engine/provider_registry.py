"""Authoritative provider lookup for the v0.8 execution boundary."""

from __future__ import annotations

from engine.generation_errors import ConfigurationError
from engine.image_providers import FakeImageProvider, GeminiImageProvider, ImageProvider


PROVIDER_REGISTRY: dict[str, ImageProvider] = {"fake": FakeImageProvider(), "gemini": GeminiImageProvider()}


def list_providers() -> tuple[str, ...]:
    return tuple(PROVIDER_REGISTRY)


def get_provider(name: str) -> ImageProvider:
    try:
        return PROVIDER_REGISTRY[name]
    except KeyError as error:
        raise ConfigurationError(f"Unknown image provider '{name}'. Available providers: {', '.join(list_providers())}") from error
