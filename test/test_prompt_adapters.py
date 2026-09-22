import pytest

from engine.adapter_registry import get_adapter, list_adapters, render_prompt
from engine.loader import list_character_ids, load_character
from engine.prompt_pipeline import build_prompt
from engine.resolver import resolve_character_by_id
from engine.scene_composer import compose_scene_by_id



def test_registry_exposes_the_expected_adapters_and_rejects_unknown_names():
    assert list_adapters() == ("generic", "openai", "gemini")
    assert get_adapter("generic").name == "generic"
    assert render_prompt("luna", "portrait").adapter_name == "generic"
    with pytest.raises(ValueError, match="Unknown prompt adapter 'unknown'"):
        get_adapter("unknown")


@pytest.mark.parametrize("adapter", list_adapters())
def test_each_adapter_is_deterministic_and_preserves_luna_identity_and_scene(adapter):
    first = build_prompt("luna", "portrait", adapter)
    second = build_prompt("luna_campbell", "portrait", adapter)

    assert first.to_dict() == second.to_dict()
    for phrase in ("Luna Campbell", "21-year-old", "British", "curvy", "freckles", "green-hazel", "auburn", "simple neutral environment", "Frame her in a medium portrait", "Soft natural daylight"):
        assert phrase in first.positive_prompt


@pytest.mark.parametrize("character_id", list_character_ids())
@pytest.mark.parametrize("adapter", list_adapters())
@pytest.mark.parametrize("density", ("compact", "standard", "detailed"))
def test_every_canonical_character_renders_through_every_adapter_at_every_density(character_id, adapter, density):
    prompt = build_prompt(character_id, "portrait", adapter, density)

    assert prompt.character_id == character_id
    assert prompt.adapter_name == adapter
    assert prompt.source_metadata["density"] == density
    assert prompt.positive_prompt


def test_density_controls_verbosity_without_dropping_critical_identity_traits():
    compact = build_prompt("luna", "portrait", "generic", "compact")
    standard = build_prompt("luna", "portrait", "generic", "standard")
    detailed = build_prompt("luna", "portrait", "generic", "detailed")

    assert len(compact.positive_prompt) < len(standard.positive_prompt) < len(detailed.positive_prompt)
    for prompt in (compact, standard, detailed):
        for phrase in ("Luna Campbell", "curvy", "freckles", "green-hazel", "auburn"):
            assert phrase in prompt.positive_prompt
    assert detailed.source_metadata["density"] == "detailed"


def test_adapter_negative_prompt_policy_is_explicit():
    generic = build_prompt("luna", "portrait", "generic")
    openai = build_prompt("luna", "portrait", "openai")
    gemini = build_prompt("luna", "portrait", "gemini")

    assert "incorrect hair color" in generic.negative_prompt
    assert openai.negative_prompt is None and "hair colour" in openai.positive_prompt
    assert gemini.negative_prompt is None


@pytest.mark.parametrize("adapter", list_adapters())
def test_scene_context_with_activity_is_preserved_by_every_adapter(adapter):
    prompt = build_prompt("idun", "workplace", adapter)
    for phrase in ("practical chef workspace", "preparation counter", "three-quarter angle", "Soft practical indoor light"):
        assert phrase in prompt.positive_prompt


def test_prompt_pipeline_does_not_mutate_upstream_character_resolution_or_scene():
    character = load_character("luna")
    resolution = resolve_character_by_id("luna")
    scene = compose_scene_by_id("luna", "portrait")
    before = (repr(character), resolution.to_dict(), scene.to_dict())

    build_prompt("luna", "portrait", "gemini", "detailed")

    assert before == (repr(character), resolution.to_dict(), scene.to_dict())


@pytest.mark.parametrize(("character_id", "mode", "adapter"), (("luna", "portrait", "generic"), ("luna", "portrait", "openai"), ("luna", "portrait", "gemini"), ("charlotte", "lifestyle", "openai")))
def test_representative_adapter_output_is_deterministic(character_id, mode, adapter):
    assert build_prompt(character_id, mode, adapter).positive_prompt == build_prompt(character_id, mode, adapter).positive_prompt
