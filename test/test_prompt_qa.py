import hashlib

import pytest

from engine.adapters.base import source_sections
from engine.loader import load_character
from engine.prompt_compiler import compile_prompt_plan
from engine.prompt_pipeline import build_prompt
from engine.scene_composer import compose_scene
from test.fixtures.expected_identity_anchors import EXPECTED_IDENTITY_ANCHORS


BENCHMARKS = (
    ("ayami_tanaka", "portrait"), ("ayami_tanaka", "workplace"), ("ayami_tanaka", "lifestyle"),
    ("luna_campbell", "portrait"), ("luna_campbell", "full_body"), ("luna_campbell", "lifestyle"),
    ("naomi", "hobby"), ("naomi", "environmental"), ("zara", "portrait"),
    ("idun_braten", "portrait"), ("idun_braten", "workplace"), ("idun_braten", "environmental"),
    ("charlotte_taylor_rose", "portrait"), ("charlotte_taylor_rose", "lifestyle"),
)

GEMINI_QA_GOLDENS = {
    ("ayami_tanaka", "portrait"): "888564132e34e444103f0ba7564085954120c61ef51d865acc149e3da0d46eef",
    ("ayami_tanaka", "workplace"): "2b43c1ef3df4033dfa86d959b919db571834d697357001b3c3236ee76918e27a",
    ("ayami_tanaka", "lifestyle"): "2f5630f6fe3493ac605f59e2191f1c12365800e5eecf9888a95957d4ed2c3daa",
    ("luna_campbell", "portrait"): "3041af7a7a9869e956183bd17403be856949d349df6778ea5b91f4b37194c023",
    ("luna_campbell", "full_body"): "8ebb129e6a9d66c6ec0df0bcbdde355bf2b388bbc5ba193f86cb651091f44edd",
    ("luna_campbell", "lifestyle"): "990beff1081387e2be5b9bbc2e8f7635bb449f9c43388117d7bfb06b9396bb7b",
    ("naomi", "hobby"): "2c49ac901dcbeed05fb3c8bde9d4360e598894b7036955a053803c9484106639",
    ("naomi", "environmental"): "a0c1f45d14003d0a3d3444ce344e09a684bbdbf58aa70be82583afe027349820",
    ("zara", "portrait"): "d6b9f08d7c3f86b076a679ba11400b85da6d47a0e9900fe125ca54f6a42d78d1",
    ("idun_braten", "portrait"): "d720868fe6a2a90ec90270785dac04948cc8c7f753ff4fc8c90458b483f0cb0c",
    ("idun_braten", "workplace"): "c0296388a59a3d2b671a8cced7336ebe9698b4768fd7c7a0b3dc9d76cbb44b09",
    ("idun_braten", "environmental"): "7cafb940d5c548ffc9f90aa20cd68b0ce2e9236df51327df9643f428a61be3ef",
    ("charlotte_taylor_rose", "portrait"): "b2cf135c66ad7745a4e325c506423575ef7b25d7f240d58a1e157c70325021e3",
    ("charlotte_taylor_rose", "lifestyle"): "256b3f766eeb3f5862447a0dbbfdb1b12b8011e953258dbfee6619f1d5d77c28",
}


def _plan(character_id, mode):
    character = load_character(character_id)
    scene = compose_scene(character, mode)
    return compile_prompt_plan(character, scene.character_description, scene)


@pytest.mark.parametrize("character_id", EXPECTED_IDENTITY_ANCHORS)
def test_expected_identity_anchors_are_semantically_preserved(character_id):
    anchors = " ".join(_plan(character_id, "portrait").identity_anchors).casefold()
    assert all(expected in anchors for expected in EXPECTED_IDENTITY_ANCHORS[character_id])


@pytest.mark.parametrize(("character_id", "mode"), BENCHMARKS)
def test_qa_benchmark_gemini_prompts_are_coherent(character_id, mode):
    prompt = build_prompt(character_id, mode, "gemini")
    assert prompt.positive_prompt.startswith("Photorealistic")
    assert "identity drift" not in prompt.positive_prompt
    assert "\n\na simple" not in prompt.positive_prompt


@pytest.mark.parametrize(("character_id", "mode"), GEMINI_QA_GOLDENS)
def test_reviewed_gemini_prompt_golden_is_stable(character_id, mode):
    prompt = build_prompt(character_id, mode, "gemini").positive_prompt
    assert hashlib.sha256(prompt.encode()).hexdigest() == GEMINI_QA_GOLDENS[(character_id, mode)]


def test_activity_and_pose_are_compiled_as_one_event():
    prompt = build_prompt("idun", "workplace", "gemini").positive_prompt
    assert "preparation counter, focused on the work in her hands" in prompt
    assert "working as a chef, standing naturally" not in prompt


def test_realism_and_identity_constraints_have_a_sentence_boundary():
    prompt = build_prompt("luna", "lifestyle", "gemini").positive_prompt
    assert "Realistic proportions. no " in prompt
    assert "Preserve her described hair colour" not in prompt


def test_skin_scalars_are_rendered_as_field_aware_complexion_phrases():
    prompt = build_prompt("ayami", "portrait", "gemini").positive_prompt
    assert "a light, natural complexion" in prompt
    assert "light natural complexion skin" not in prompt


def test_face_shape_and_cheekbones_use_field_aware_phrasing():
    prompt = build_prompt("luna", "lifestyle", "gemini").positive_prompt
    assert "a short, softly rounded face" in prompt
    assert "low, softly defined cheekbones" in prompt


def test_software_engineer_uses_a_visual_occupation_action():
    prompt = build_prompt("ayami", "workplace", "gemini").positive_prompt
    assert "works at a desk, focused on her screen and keyboard" in prompt
    assert "professional setting" not in prompt


def test_full_body_uses_head_to_toe_composition_language():
    prompt = build_prompt("luna", "full_body", "gemini").positive_prompt
    assert "entire figure visible, including her feet" in prompt
    assert "waist upward" not in prompt


def test_environmental_mode_prioritizes_the_location_before_subject_action():
    ids = tuple(section.id for section in source_sections(_plan("naomi", "environmental")))
    assert ids.index("environment") < ids.index("action")
    assert "Give clear visual weight" in build_prompt("naomi", "environmental", "gemini").positive_prompt


@pytest.mark.parametrize(("character_id", "mode"), (("luna_campbell", "lifestyle"), ("idun_braten", "workplace"), ("naomi", "environmental")))
def test_adapter_comparison_preserves_compiler_semantics(character_id, mode):
    plans = [build_prompt(character_id, mode, adapter).source_metadata["prompt_plan"] for adapter in ("generic", "openai", "gemini")]
    assert plans[0] == plans[1] == plans[2]
