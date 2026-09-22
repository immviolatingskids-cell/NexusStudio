import json
from pathlib import Path

from engine.identity import find_identity_conflicts, load_identity_profile
from engine.loader import load_all_characters, load_character
from engine.prompt_compiler import compile_prompt_plan
from engine.resolver import resolve_scene
from engine.scene_composer import compose_scene
from engine.scene_models import SceneBrief
from engine.prompts import compose_prompt_document
from stress_test_identity import CASES, _prompt, load_local_env
from engine.providers import GeminiProvider, ProviderError


IDENTITY_DIR = Path(__file__).parents[1] / "characters" / "identity"


def test_all_canonical_characters_have_consensus_variation_and_drift_guidance():
    characters = load_all_characters()
    assert len(characters) == 6
    for character in characters:
        profile = load_identity_profile(character.character_id)
        assert profile.drift_critical_features
        assert profile.reference_consensus["reference_count"] == 1
        assert profile.reference_consensus["confidence"] == "single-reference"
        assert profile.variation_envelope["hair"]["can_change"] is True
        assert profile.identity_relationships
        assert profile.expression_behavior
        assert profile.presentation_exclusions


def test_ayami_fixture_matches_the_authoritative_reference_schema():
    fixture = Path(__file__).parent / "fixtures" / "identity" / "ayami_tanaka.locked_look.json"
    assert json.loads(fixture.read_text(encoding="utf-8")) == json.loads((IDENTITY_DIR / "ayami_tanaka.json").read_text(encoding="utf-8"))


def test_identity_density_keeps_critical_traits_and_adds_detail_without_identity_drift():
    plans = {}
    for density in ("compact", "standard", "detailed"):
        character = load_character("ayami")
        scene = compose_scene(character, "portrait")
        plans[density] = compile_prompt_plan(character, scene.character_description, scene, density)
    compact = set(plans["compact"].identity_anchors)
    assert compact.issubset(set(plans["standard"].identity_anchors))
    assert compact.issubset(set(plans["detailed"].identity_anchors))
    assert "facial length to width:" in plans["detailed"].face_description
    assert "hair_style" in plans["detailed"].source_metadata["identity_diagnostics"]["mutable_traits"]


def test_identity_lock_does_not_mutate_canonical_character_data():
    canonical = {path.name: path.read_bytes() for path in (Path(__file__).parents[1] / "characters").glob("*.json")}
    for character in load_all_characters():
        load_identity_profile(character.character_id)
    assert canonical == {path.name: path.read_bytes() for path in (Path(__file__).parents[1] / "characters").glob("*.json")}


def test_explicit_scene_colour_contradictions_are_rejected_but_styling_remains_mutable():
    assert find_identity_conflicts("ayami_tanaka", "blue eyes and blonde hair")
    assert not find_identity_conflicts("ayami_tanaka", "a blue outfit, loose hair, and a warm expression")
    character = load_character("ayami")
    scene = compose_scene(character, "portrait", {"wardrobe": "a blue outfit with blonde hair"})
    try:
        compile_prompt_plan(character, scene.character_description, scene)
    except ValueError as exc:
        assert "conflicting" in str(exc)
    else:
        raise AssertionError("contradictory hair colour override was accepted")


def test_resolver_rejects_explicit_immutable_colour_changes():
    character = load_character("luna")
    profile = load_identity_profile(character.character_id)
    try:
        resolve_scene(SceneBrief(character_id=character.character_id, hair_style="blonde hair in a ponytail"), profile)
    except ValueError as exc:
        assert "conflicting" in str(exc)
    else:
        raise AssertionError("contradictory hair colour reached the prompt")

    scene = resolve_scene(SceneBrief(character_id=character.character_id, hair_style="hair in a ponytail", wardrobe_style="oversized jacket"), profile)
    assert scene.selections["hair_style"] == "hair in a ponytail"


def test_all_eighteen_stress_cases_compile_at_each_identity_density():
    assert set(CASES) == {character.character_id for character in load_all_characters()}
    assert all(len(cases) == 3 for cases in CASES.values())
    for character_id, cases in CASES.items():
        case_identity = []
        for case in cases:
            scene = _prompt(character_id, case)
            documents = [compose_prompt_document(scene, density) for density in ("compact", "standard", "detailed")]
            for density, document in zip(("compact", "standard", "detailed"), documents):
                rendered_identity = " ".join(document.identity).casefold()
                block = load_identity_profile(character_id).prompt_identity_blocks[density]
                assert block.casefold() in rendered_identity
                assert all(item["instruction"].casefold() in rendered_identity for item in load_identity_profile(character_id).drift_critical_features)
                assert document.identity_diagnostics["scene_conflicts"] == 0
            case_identity.append(documents[0].identity)
        assert case_identity[0] == case_identity[1] == case_identity[2]


def test_stress_runner_loads_only_the_expected_key_from_local_env(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text('OTHER=value\nexport GEMINI_API_KEY="temporary-test-key"\n', encoding="utf-8")
    load_local_env(env_file)
    assert __import__("os").environ["GEMINI_API_KEY"] == "temporary-test-key"


def test_text_refiner_returns_text_without_requesting_images(monkeypatch):
    class Response:
        text = "Refined prompt."

    class Models:
        def generate_content(self, **kwargs):
            assert kwargs["model"] == "gemini-2.5-flash"
            assert "PROMPT TO REFINE" in kwargs["contents"]
            assert kwargs["config"].automatic_function_calling.disable is True
            return Response()

    class Client:
        models = Models()

    provider = GeminiProvider()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(provider, "_client", Client())
    assert provider.refine("Original prompt") == "Refined prompt."
