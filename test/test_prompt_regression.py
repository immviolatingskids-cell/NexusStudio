import hashlib

import pytest

from engine.loader import list_character_ids
from engine.prompt_pipeline import build_prompt
from engine.scene_defaults import SCENE_MODES


@pytest.mark.parametrize("character_id", list_character_ids())
@pytest.mark.parametrize("mode", SCENE_MODES)
def test_every_character_and_mode_compiles(character_id, mode):
    prompt = build_prompt(character_id, mode, "generic")
    assert prompt.positive_prompt and "Photorealistic" in prompt.positive_prompt
    assert prompt.source_metadata["prompt_plan"]["identity_anchors"]


BENCHMARK_HASHES = {
    ("ayami_tanaka", "workplace"): "bab762bd5e5d4a31ba5f737d9d56240ecffd7ae3a94941eb564ffbc2e88157f3",
    ("ayami_tanaka", "portrait"): "02771a666e59ec3db609494538f6ed59e04630ec9be93f0666b7894805b7025f",
    ("luna_campbell", "lifestyle"): "ee33d472786d4bdb4eb61d11d0b378e343a88a6287e6c2e453cbf38a3d072265",
    ("luna_campbell", "full_body"): "a68bcc3550d7fcf9f9d5f8f33797a6ad3dfbf42f3b3df955ba85f775fc365652",
    ("naomi", "hobby"): "40d83cc9cf84e4a3d98f71d8d4e304d6a9008bd983ed4bd603e53984fa7b240d",
    ("naomi", "environmental"): "63e793f7f2c02853e418b759f44da65e921002aa1c71299d4e103b4b87e8b20e",
    ("zara", "portrait"): "610c6430e6c0e9b0b577be23a7fffd05801664e19623e7daec8867a2c52bdc3d",
    ("zara", "lifestyle"): "82248b1c8c4e6f5363ef96bb1ece69670c6af8af79769e9be361938ac4289e3d",
    ("idun_braten", "workplace"): "41f8990758ad7f90df29bd75a4653608a57c8ad7f1693219e8eb4f05b7753cb1",
    ("idun_braten", "environmental"): "67141a4af30ba9cc4472f96f4c13c65bc8aea82ea7df29bcefe92150d3cfb7ac",
    ("charlotte_taylor_rose", "portrait"): "67ccda8b00ca342be004576389da39f20678cad28a9f10731f8715e641d0bbd4",
    ("charlotte_taylor_rose", "lifestyle"): "bf22667f4539cf8e43d7c6f287b438d6e83bc247dc0f57174b7be7673355607f",
}


@pytest.mark.parametrize(("character_id", "mode"), BENCHMARK_HASHES)
def test_prompt_quality_benchmark_is_stable(character_id, mode):
    prompt = build_prompt(character_id, mode, "generic").positive_prompt
    assert hashlib.sha256(prompt.encode()).hexdigest() == BENCHMARK_HASHES[(character_id, mode)]
