"""Minimal provider interface, deliberately independent of prompt composition."""

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.generation_models import GenerationRequest, GenerationResult


class ImageProvider(ABC):
    name: str
    preferred_adapter: str

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate and persist one normalized result."""
