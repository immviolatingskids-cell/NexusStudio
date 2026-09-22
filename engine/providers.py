"""Provider-neutral CLI image generation adapters."""

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from engine.prompts import PromptDocument


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class GenerationResult:
    provider: str
    model: str
    image_bytes: bytes
    mime_type: str
    metadata: dict[str, str]


class GenerationProvider(Protocol):
    name: str
    def capabilities(self) -> dict[str, object]: ...
    def validate(self) -> None: ...
    def generate(self, prompt: PromptDocument, reference_paths: tuple[Path, ...] = ()) -> GenerationResult: ...


class FakeProvider:
    name = "fake"

    def capabilities(self) -> dict[str, object]:
        return {"live": False, "reference_images": True, "deterministic": True}

    def validate(self) -> None:
        return None

    def generate(self, prompt: PromptDocument, reference_paths: tuple[Path, ...] = ()) -> GenerationResult:
        digest = hashlib.sha256((prompt.render() + "|" + "|".join(map(str, reference_paths))).encode("utf-8")).hexdigest()
        return GenerationResult(self.name, "deterministic-preview", f"NexusStudio fake image {digest}\n".encode("utf-8"), "text/plain", {"digest": digest})


class GeminiProvider:
    name = "gemini"

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
        self._client = None

    def capabilities(self) -> dict[str, object]:
        return {"live": True, "reference_images": False, "deterministic": False, "model": self.model, "purpose": "text refinement"}

    def validate(self) -> None:
        if not os.getenv("GEMINI_API_KEY"):
            raise ProviderError("GEMINI_API_KEY is required for the Gemini provider.")
        try:
            from google import genai  # noqa: F401
        except ImportError as exc:
            raise ProviderError("Install the optional 'google-genai' package to use Gemini text refinement.") from exc

    def refine(self, prompt: str, instruction: str = "") -> str:
        self.validate()
        from google import genai
        from google.genai import types
        if self._client is None:
            self._client = genai.Client()
        task = instruction.strip() or (
            "Refine this into a clear, concise image-generation prompt. Preserve all locked identity facts and the scene intent; "
            "do not add new identity details, alter protected traits, or generate an image. Return only the refined prompt."
        )
        response = self._client.models.generate_content(
            model=self.model,
            contents=f"{task}\n\nPROMPT TO REFINE:\n{prompt}",
            config=types.GenerateContentConfig(
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        refined = (getattr(response, "text", None) or "").strip()
        if not refined:
            raise ProviderError("Gemini returned no refined prompt text.")
        return refined

    def generate(self, prompt: PromptDocument, reference_paths: tuple[Path, ...] = ()) -> GenerationResult:
        raise ProviderError("GeminiProvider is text-only. Use refine() for prompt refinement; generate images in your chosen image tool.")


def get_provider(name: str) -> GenerationProvider:
    if name == "fake":
        return FakeProvider()
    if name == "gemini":
        return GeminiProvider()
    raise ProviderError(f"Unknown provider '{name}'. Supported providers: fake, gemini.")
