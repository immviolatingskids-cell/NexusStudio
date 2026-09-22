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
    ("ayami_tanaka", "portrait"): "1e03727de6b44c6bdcd461bfaf223de8e7570450106918b83c011ce3aaea900a",
    ("ayami_tanaka", "workplace"): "730381f3f78bf64f001d18266aa38d0097e9255e01ed2fec50b9dba0493c4ee9",
    ("ayami_tanaka", "lifestyle"): "3ee7d18008b8ad071722e5193675485b7704ce33334379819808a3ac893bd3af",
    ("luna_campbell", "portrait"): "5c40b5ece1e8a768a85c3a48ee615f434e1645da3b742a894ed9c6d66dcfffbe",
    ("luna_campbell", "full_body"): "ffed3165a20abb31de71ca5fed2cf556ac24e37026d018ed9fe456ea6a0078d3",
    ("luna_campbell", "lifestyle"): "b168686bc6fcab00556d51b711e8080aa54a27df7ff2cf5a24f0996d5c94fd89",
    ("naomi", "hobby"): "82054e758033d66587671bc31bec8aa80f1f8b631fe5e72462487f6e1caafa64",
    ("naomi", "environmental"): "8faee69facef0b076f414d20fadb9d153f83c620f5464dc3f6ef48585d3fa739",
    ("zara", "portrait"): "a0241450f265c0653be347bfc1aea69e9519270488c91409f065c442ab0f6734",
    ("idun_braten", "portrait"): "ec9288611ed6220f16fd1d58445afe8944449b63fcd77a5395728c5142b9468d",
    ("idun_braten", "workplace"): "3956c72b0899d9a3161f3b0337183394e8812ff9df753356a48ea06e17036b87",
    ("idun_braten", "environmental"): "e47acc3d7bbd08b8a34b85b33f6e9e840cc2009cc9bd59d0dc88f25221432552",
    ("charlotte_taylor_rose", "portrait"): "3945926d67bd2bc588adb7bc2fec00ef9c9a4be5b59c4152da9744db7ac3ee2e",
    ("charlotte_taylor_rose", "lifestyle"): "208da36ec3b9edb8a5b2ea85c4edc372030bdd5199e48c216aa65bbbad5d8764",
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
