"""Optional Gemini image provider; SDK imports and credentials stay isolated."""

from __future__ import annotations

import base64
import os

from config import GEMINI_API_KEY_ENV, GEMINI_IMAGE_MODEL
from engine.generation_errors import InvalidProviderResponseError, ProviderUnavailableError
from engine.generation_models import GenerationRequest, GenerationResult
from engine.image_providers.base import ImageProvider
from engine.output_manager import write_asset


class GeminiImageProvider(ImageProvider):
    name = "gemini"
    preferred_adapter = "gemini"

    def __init__(self, model: str = GEMINI_IMAGE_MODEL) -> None:
        self.model = model

    def _client(self):
        key = os.getenv(GEMINI_API_KEY_ENV)
        if not key:
            raise ProviderUnavailableError("Gemini provider unavailable: missing API credential (GEMINI_API_KEY).")
        try:
            from google import genai
        except ImportError as error:
            raise ProviderUnavailableError("Gemini provider unavailable: install optional package 'google-genai'.") from error
        return genai.Client(api_key=key)

    @staticmethod
    def _image_data(response) -> tuple[bytes, str]:
        candidates = getattr(response, "parts", None) or ()
        for part in candidates:
            inline = getattr(part, "inline_data", None)
            data = getattr(inline, "data", None) if inline else None
            if data:
                if isinstance(data, str):
                    data = base64.b64decode(data)
                if not isinstance(data, bytes):
                    raise InvalidProviderResponseError("Gemini returned image data in an unsupported format.")
                return data, getattr(inline, "mime_type", None) or "image/png"
        raise InvalidProviderResponseError("Gemini returned no image data.")

    def generate(self, request: GenerationRequest) -> GenerationResult:
        client = self._client()
        response = client.models.generate_content(model=request.model or self.model, contents=request.positive_prompt)
        image_bytes, mime_type = self._image_data(response)
        asset = write_asset(request, image_bytes, mime_type, provider_metadata={"response": "image received"})
        return GenerationResult(True, self.name, request.model or self.model, request.character_id, request.scene_mode, request.adapter, (asset,), mime_type)
