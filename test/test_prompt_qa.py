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
    ("ayami_tanaka", "portrait"): "0df2c2bd0cb7add35408bfe4580ccabaa9b5995d987d341ab1707b135504e8b5",
    ("ayami_tanaka", "workplace"): "40ad1488145bb82d835d0fe5fd728c3ec8538d59523ba741424c01a8934c67fe",
    ("ayami_tanaka", "lifestyle"): "6fa66fecb068b998059d34b1d98cab86e888c0b8aef47d9c04e614b2e4638402",
    ("luna_campbell", "portrait"): "70b9fca30baaa37e4c988a527355ceaeac41563585e632bf79ef7356baefb5ae",
    ("luna_campbell", "full_body"): "93342c4cef39ac25ad76df3ce32f87cd7726dc1366f009832816ebaedd7e298c",
    ("luna_campbell", "lifestyle"): "60af25eb2b8f90d129a535cd6ad8fc070f8b8816fb5b4712945e41fc4cfc7a4b",
    ("naomi", "hobby"): "4b73a1860162bcb3558caf81c4926b61e9347bef4b90df737de805a92bd55076",
    ("naomi", "environmental"): "3c72184d4dc1c6bd329f9ebef26b44ac33b005595d504ca2618633a7d279b1e9",
    ("zara", "portrait"): "2e192989db5492a71ca242a73ba3c0473132ac3af033e7d4521e52d28bdeda89",
    ("idun_braten", "portrait"): "944203f24fb99184d85ccc17f2aeed35f1ad4ee3721253b5a3d218a9b700f4ee",
    ("idun_braten", "workplace"): "586762207cfaa081cc7410fc570dce0e522139620068c2ee0ee1de85eb062de9",
    ("idun_braten", "environmental"): "4543b17fb26aa48485118c9c6b7885fac01b3056cc7889fbde626476ab85498a",
    ("charlotte_taylor_rose", "portrait"): "f55042de26b95747db1409a4babbae2ca43f4831ee8537ce40aec69506e84773",
    ("charlotte_taylor_rose", "lifestyle"): "a7d3bd268ae268b2b95a6feb3d24e4b04be2edd4c5e157b9713f83377ce940d8",
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
    assert "realistic proportions. preserve her described hair colour" in prompt


def test_skin_scalars_are_rendered_as_field_aware_complexion_phrases():
    prompt = build_prompt("ayami", "portrait", "gemini").positive_prompt
    assert "a light, natural complexion" in prompt
    assert "light natural complexion skin" not in prompt


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
