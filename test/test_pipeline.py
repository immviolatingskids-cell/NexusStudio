import json

import pytest

from engine.audit import run_audit
from engine.identity import load_identity_profile
from engine.loader import load_character
from engine.migrations import migrate_character_file
from engine.prompts import PromptLintError, PromptDocument, compose_prompt_document, lint_prompt
from engine.providers import FakeProvider, GeminiProvider, ProviderError
from engine.resolver import reroll_scene, resolve_scene
from engine.scene_models import SceneBrief
from engine.versions import CHARACTER_VERSION
from pools.registry import BY_ID, find, find_display, registry_issues


def _scene():
    character = load_character("luna")
    profile = load_identity_profile(character.character_id)
    return character, profile, resolve_scene(
        SceneBrief(character_id=character.character_id, location="environment_location_bar", seed=8, locks=frozenset({"location"})),
        profile,
        character.affinities,
    )


def test_resolved_scene_records_stable_pool_ids_and_locked_reroll():
    character, profile, first = _scene()

    rerolled = reroll_scene(first, profile, character.affinities)

    assert first.selection_ids["location"] == "environment_location_bar"
    assert rerolled.selection_ids["location"] == "environment_location_bar"
    assert rerolled.brief.seed == first.brief.seed + 1
    with pytest.raises(ValueError, match="locked"):
        reroll_scene(first, profile, character.affinities, dimension="location")


def test_registry_keeps_internal_lookup_id_only():
    assert find("streetwear", category="style") is None
    assert find("fashion_streetwear", category="style") == BY_ID["fashion_streetwear"]
    assert find_display("streetwear", category="style") == BY_ID["fashion_streetwear"]
    assert not registry_issues()


def test_prompt_lint_rejects_identity_conflict():
    with pytest.raises(PromptLintError, match="conflicts"):
        lint_prompt(PromptDocument("test", ("freckles",), ("freckle-free skin",), ("medium framing",), ("no freckle-free skin",)))


def test_prompt_document_preserves_identity_separate_from_direction():
    _, profile, scene = _scene()
    prompt = compose_prompt_document(scene)

    assert profile.prompt_identity_blocks["standard"] in prompt.identity
    assert all(item["instruction"] in prompt.identity for item in profile.drift_critical_features)
    assert prompt.negative == scene.negative_constraints
    assert prompt.direction


def test_prompt_document_identity_density_tracks_the_same_character():
    _, profile, scene = _scene()
    compact = compose_prompt_document(scene, "compact")
    standard = compose_prompt_document(scene, "standard")
    detailed = compose_prompt_document(scene, "detailed")

    assert all(item["instruction"] in compact.identity for item in profile.drift_critical_features)
    assert all(item in " ".join(standard.identity) for item in compact.identity)
    assert all(item in " ".join(detailed.identity) for item in standard.identity)
    assert profile.prompt_identity_blocks["standard"] in standard.identity
    assert profile.prompt_identity_blocks["detailed"] in detailed.identity
    assert detailed.identity_diagnostics["mutable_traits"]


def test_character_migration_preview_and_apply_creates_backup(tmp_path):
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps({"schema_version": "0.1", "character_id": "fixture"}), encoding="utf-8")

    preview = migrate_character_file(path)
    applied = migrate_character_file(path, apply=True)

    assert preview["changed"] is True
    assert applied["backup"].endswith(".v0.1.backup.json")
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == CHARACTER_VERSION
    assert json.loads((tmp_path / "legacy.v0.1.backup.json").read_text(encoding="utf-8"))["schema_version"] == "0.1"


def test_audit_validates_current_contracts():
    report = run_audit()

    assert report.ok
    assert report.characters == 6
    assert report.pool_entries == len(BY_ID)


def test_fake_provider_is_deterministic_and_gemini_requires_configuration(monkeypatch):
    _, _, scene = _scene()
    prompt = compose_prompt_document(scene)
    fake = FakeProvider()

    assert fake.generate(prompt).image_bytes == fake.generate(prompt).image_bytes
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="GEMINI_API_KEY"):
        GeminiProvider().validate()


def test_gemini_refinement_defaults_to_text_model_and_allows_override(monkeypatch):
    monkeypatch.delenv("GEMINI_TEXT_MODEL", raising=False)
    assert GeminiProvider().model == "gemini-2.5-flash"
    monkeypatch.setenv("GEMINI_TEXT_MODEL", "gemini-3.1-flash-lite")
    assert GeminiProvider().model == "gemini-3.1-flash-lite"


def test_gemini_image_generation_is_disabled_in_prompt_refinement_workflow():
    with pytest.raises(ProviderError, match="text-only"):
        GeminiProvider().generate(compose_prompt_document(_scene()[2]))
