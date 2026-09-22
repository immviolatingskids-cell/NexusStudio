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
    ("ayami_tanaka", "portrait"): "2da4a53c14129cee55fd1e47187dc9d78cc35bccfaf40c22649bf38896e745e2",
    ("ayami_tanaka", "workplace"): "099fa1fd7d6f7bb05e6e2047f46e8298b629cce427773d5d3add7754d35f2985",
    ("ayami_tanaka", "lifestyle"): "1275023b5cfa64be54c7ce5eef4c340dc872023c2397fed2dcb1de6a2d56d122",
    ("luna_campbell", "portrait"): "3d0f056dc013bd41db94d4c846f25e05a281dad51a84365012c8b1949afefc93",
    ("luna_campbell", "full_body"): "185145ac923c6b16084cbfcc4a4c8a95b69fbdf48ec6ae031c222eb3d4f2de95",
    ("luna_campbell", "lifestyle"): "62bcb46a75e66e2404640eb442618d16b6c3a5540be9b794946602a1b1d26012",
    ("naomi", "hobby"): "613cba226f02a8deca3697614bc3163a312ff810cc94bc604f95a37accd4cd4d",
    ("naomi", "environmental"): "d1a5f1c3fcdb454ed82e0d2275b9a7218e6ac5ce47e558f42445205fd3a089b2",
    ("zara", "portrait"): "ae2312891f474105a4ad88ad56d8262ee11843858ee3dcb4d2090d247765bb3a",
    ("idun_braten", "portrait"): "3806963243aa440bb56668829112051125812c25aeb14e1f259fddab003ca187",
    ("idun_braten", "workplace"): "e87f74caf40c89241379d2726ea1941067af56fec104f0d31acf1421f6833dd9",
    ("idun_braten", "environmental"): "883226e52665bddb62f7dcc9cb8a1d28d99e4b4ff90403ea9f7b414e1a9e641f",
    ("charlotte_taylor_rose", "portrait"): "c4b60b0b21c1cdc490c589a0dbecca80587eb0f4b086e1d092ead8132e2a7d83",
    ("charlotte_taylor_rose", "lifestyle"): "57de42695eeac9a984141a838b5f8b764f3a4c1e7a329c1d0d6359c2772ab86a",
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
    assert "Realistic proportions. Preserve her described hair colour" in prompt


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
