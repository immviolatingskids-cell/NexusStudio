from dataclasses import asdict

from engine.identity import load_identity_profile
from engine.loader import load_all_characters
from engine.prompt_compiler import compile_prompt_plan
from engine.scene_composer import compose_scene


def test_all_locked_identity_files_are_versioned_and_use_the_frozen_schema():
    characters = load_all_characters()
    assert len(characters) == 6
    for character in characters:
        profile = load_identity_profile(character.character_id)
        assert profile.version == "1.1.0"
        assert profile.critical_anchors
        assert profile.drift_critical_features


def test_critical_and_drift_traits_survive_each_compiler_density():
    character = next(c for c in load_all_characters() if c.character_id == "ayami_tanaka")
    profile = load_identity_profile(character.character_id)
    scene = compose_scene(character, "portrait")
    plans = [compile_prompt_plan(character, scene.character_description, scene, density) for density in ("compact", "standard", "detailed")]
    for plan in plans:
        joined = " ".join(plan.identity_anchors + plan.identity_constraints + ((plan.face_description or ""),))
        assert all(item in joined for item in (profile.critical_anchors + tuple(d["instruction"] for d in profile.drift_critical_features)))
    assert set(plans[0].identity_anchors).issubset(set(plans[1].identity_anchors))
    assert set(plans[1].identity_anchors).issubset(set(plans[2].identity_anchors))


def test_compiler_is_deterministic_and_does_not_mutate_canonical_models():
    character = next(c for c in load_all_characters() if c.character_id == "ayami_tanaka")
    before = asdict(character)
    scene = compose_scene(character, "portrait")
    first = compile_prompt_plan(character, scene.character_description, scene, "detailed").to_dict()
    second = compile_prompt_plan(character, scene.character_description, scene, "detailed").to_dict()
    assert first == second
    assert before == asdict(character)
