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

    def __init__(self, model: str = "gemini-3.1-flash-image") -> None:
        self.model = model

    def capabilities(self) -> dict[str, object]:
        return {"live": True, "reference_images": True, "deterministic": False, "model": self.model}

    def validate(self) -> None:
        if not os.getenv("GEMINI_API_KEY"):
            raise ProviderError("GEMINI_API_KEY is required for the Gemini provider.")
        try:
            from google import genai  # noqa: F401
        except ImportError as exc:
            raise ProviderError("Install the optional 'google-genai' package to use Gemini generation.") from exc

    def generate(self, prompt: PromptDocument, reference_paths: tuple[Path, ...] = ()) -> GenerationResult:
        self.validate()
        from google import genai
        from google.genai import types
        contents: list[object] = [prompt.render()]
        for path in reference_paths:
            if not path.is_file():
                raise ProviderError(f"Approved reference image is missing: {path}")
            contents.append(types.Part.from_bytes(data=path.read_bytes(), mime_type="image/png"))
        response = genai.Client().models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )
        for part in response.parts or ():
            if getattr(part, "inline_data", None) and part.inline_data.data:
                return GenerationResult(self.name, self.model, base64.b64decode(part.inline_data.data), part.inline_data.mime_type or "image/png", {})
        raise ProviderError("Gemini returned no image data.")


def get_provider(name: str) -> GenerationProvider:
    if name == "fake":
        return FakeProvider()
    if name == "gemini":
        return GeminiProvider()
    raise ProviderError(f"Unknown provider '{name}'. Supported providers: fake, gemini.")
