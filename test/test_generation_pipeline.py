import json
from pathlib import Path

import pytest

from engine.generation_errors import ConfigurationError, GenerationError, InvalidProviderResponseError, ProviderUnavailableError
from engine.generation_models import GenerationRequest
from engine.generation_pipeline import generate_image
from engine.image_providers.fake import FakeImageProvider
from engine.image_providers.gemini import GeminiImageProvider
from engine.output_manager import output_path_for
from engine.provider_registry import get_provider, list_providers


def test_provider_registry_contains_fake_and_gemini_and_rejects_unknown_provider():
    assert list_providers() == ("fake", "gemini")
    assert get_provider("fake").name == "fake"
    with pytest.raises(ConfigurationError, match="Unknown image provider 'unknown'"):
        get_provider("unknown")


def test_end_to_end_fake_generation_writes_asset_and_safe_metadata(tmp_path):
    result = generate_image("luna", "portrait", provider="fake", output_dir=tmp_path)

    assert result.success and result.provider == "fake"
    asset = result.assets[0]
    path = Path(asset.file_path)
    assert path == tmp_path / "luna_campbell" / "portrait" / "luna_campbell_portrait_fake_001.txt"
    assert path.is_file() and asset.content_hash
    sidecar = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    assert sidecar["character_id"] == "luna_campbell"
    assert sidecar["adapter"] == "generic"
    assert "Luna Campbell" in sidecar["positive_prompt"]
    assert "API_KEY" not in json.dumps(sidecar)


def test_provider_preference_and_explicit_adapter_precedence(tmp_path):
    preferred = generate_image("luna", "portrait", provider="fake", output_dir=tmp_path)
    explicit = generate_image("luna", "portrait", provider="fake", adapter="gemini", output_dir=tmp_path)

    assert preferred.adapter == "generic"
    assert explicit.adapter == "gemini"
    assert "Fake provider used with gemini adapter." in explicit.warnings


def test_overrides_and_density_flow_into_prompt_and_request_metadata(tmp_path):
    result = generate_image("idun", "workplace", provider="fake", density="detailed", overrides={"environment": "a quiet test kitchen"}, output_dir=tmp_path)
    sidecar = json.loads(Path(result.assets[0].file_path).with_suffix(".json").read_text(encoding="utf-8"))

    assert sidecar["density"] == "detailed"
    assert "quiet test kitchen" in sidecar["positive_prompt"]


def test_dry_run_plans_output_without_calling_provider_or_writing(tmp_path, monkeypatch):
    provider = get_provider("fake")
    monkeypatch.setattr(provider, "generate", lambda request: pytest.fail("provider should not run"))

    result = generate_image("luna", "portrait", provider="fake", dry_run=True, output_dir=tmp_path)

    assert result.success and result.dry_run
    assert result.assets[0].file_path.endswith("luna_campbell_portrait_fake_001.txt")
    assert not Path(result.assets[0].file_path).exists()
    assert not Path(result.assets[0].file_path).with_suffix(".json").exists()
    assert result.provider_metadata["request"]["adapter"] == "generic"


def test_fake_provider_forced_failure_is_readable(tmp_path):
    request = GenerationRequest("luna_campbell", "generic", "portrait", "standard", "test", "fake", "deterministic-fake", output_dir=str(tmp_path))
    with pytest.raises(GenerationError, match="forced failure"):
        FakeImageProvider(fail=True).generate(request)


def test_output_paths_are_sanitized_and_increment_without_overwriting(tmp_path):
    request = GenerationRequest("Luna Campbell!", "generic", "Portrait Mode", "standard", "test", "fake", "deterministic-fake", output_dir=str(tmp_path))
    first = output_path_for(request, "text/plain")
    first.parent.mkdir(parents=True)
    first.write_text("existing", encoding="utf-8")
    second = output_path_for(request, "text/plain")

    assert first.name.endswith("_001.txt")
    assert second.name.endswith("_002.txt")
    assert " " not in str(second)


def test_gemini_reports_missing_credentials_without_importing_sdk(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    request = GenerationRequest("luna_campbell", "gemini", "portrait", "standard", "test", "gemini", "test-model")
    with pytest.raises(ProviderUnavailableError, match="missing API credential"):
        GeminiImageProvider().generate(request)


def test_gemini_extracts_bytes_and_rejects_invalid_response():
    class Inline:
        data = b"image-bytes"
        mime_type = "image/png"

    class Part:
        inline_data = Inline()

    class Response:
        parts = (Part(),)

    assert GeminiImageProvider._image_data(Response()) == (b"image-bytes", "image/png")
    with pytest.raises(InvalidProviderResponseError, match="no image data"):
        GeminiImageProvider._image_data(type("Empty", (), {"parts": ()})())
