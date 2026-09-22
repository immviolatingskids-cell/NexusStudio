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
    ("ayami_tanaka", "portrait"): "02771a666e59ec3db609494538f6ed59e04630ec9be93f0666b7894805b7025f",
    ("ayami_tanaka", "workplace"): "bab762bd5e5d4a31ba5f737d9d56240ecffd7ae3a94941eb564ffbc2e88157f3",
    ("ayami_tanaka", "lifestyle"): "cdc7b4765f9d32faa10523e1f4df5b47b1e5e1e4e703628afddc8c97d7abbf3e",
    ("luna_campbell", "portrait"): "7765c55c1e8ebdd04bb6b00368d11266675fa9b7863119ce949401bf8b136c72",
    ("luna_campbell", "full_body"): "a68bcc3550d7fcf9f9d5f8f33797a6ad3dfbf42f3b3df955ba85f775fc365652",
    ("luna_campbell", "lifestyle"): "ee33d472786d4bdb4eb61d11d0b378e343a88a6287e6c2e453cbf38a3d072265",
    ("naomi", "hobby"): "40d83cc9cf84e4a3d98f71d8d4e304d6a9008bd983ed4bd603e53984fa7b240d",
    ("naomi", "environmental"): "63e793f7f2c02853e418b759f44da65e921002aa1c71299d4e103b4b87e8b20e",
    ("zara", "portrait"): "610c6430e6c0e9b0b577be23a7fffd05801664e19623e7daec8867a2c52bdc3d",
    ("idun_braten", "portrait"): "455245f80be9d5f24fc6a8c64d994f1dddd3a9d469da01d10b0e45472bfc87c9",
    ("idun_braten", "workplace"): "41f8990758ad7f90df29bd75a4653608a57c8ad7f1693219e8eb4f05b7753cb1",
    ("idun_braten", "environmental"): "67141a4af30ba9cc4472f96f4c13c65bc8aea82ea7df29bcefe92150d3cfb7ac",
    ("charlotte_taylor_rose", "portrait"): "67ccda8b00ca342be004576389da39f20678cad28a9f10731f8715e641d0bbd4",
    ("charlotte_taylor_rose", "lifestyle"): "bf22667f4539cf8e43d7c6f287b438d6e83bc247dc0f57174b7be7673355607f",
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
