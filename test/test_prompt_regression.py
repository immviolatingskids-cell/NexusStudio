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
    ("ayami_tanaka", "workplace"): "2b43c1ef3df4033dfa86d959b919db571834d697357001b3c3236ee76918e27a",
    ("ayami_tanaka", "portrait"): "888564132e34e444103f0ba7564085954120c61ef51d865acc149e3da0d46eef",
    ("luna_campbell", "lifestyle"): "990beff1081387e2be5b9bbc2e8f7635bb449f9c43388117d7bfb06b9396bb7b",
    ("luna_campbell", "full_body"): "8ebb129e6a9d66c6ec0df0bcbdde355bf2b388bbc5ba193f86cb651091f44edd",
    ("naomi", "hobby"): "2c49ac901dcbeed05fb3c8bde9d4360e598894b7036955a053803c9484106639",
    ("naomi", "environmental"): "a0c1f45d14003d0a3d3444ce344e09a684bbdbf58aa70be82583afe027349820",
    ("zara", "portrait"): "d6b9f08d7c3f86b076a679ba11400b85da6d47a0e9900fe125ca54f6a42d78d1",
    ("zara", "lifestyle"): "02e5b8f70365ec7d70e077a6b7eb9ad568a2b84de6d059dfe928ab91405e0691",
    ("idun_braten", "workplace"): "c0296388a59a3d2b671a8cced7336ebe9698b4768fd7c7a0b3dc9d76cbb44b09",
    ("idun_braten", "environmental"): "7cafb940d5c548ffc9f90aa20cd68b0ce2e9236df51327df9643f428a61be3ef",
    ("charlotte_taylor_rose", "portrait"): "b2cf135c66ad7745a4e325c506423575ef7b25d7f240d58a1e157c70325021e3",
    ("charlotte_taylor_rose", "lifestyle"): "256b3f766eeb3f5862447a0dbbfdb1b12b8011e953258dbfee6619f1d5d77c28",
}


@pytest.mark.parametrize(("character_id", "mode"), BENCHMARK_HASHES)
def test_prompt_quality_benchmark_is_stable(character_id, mode):
    prompt = build_prompt(character_id, mode, "generic").positive_prompt
    assert hashlib.sha256(prompt.encode()).hexdigest() == BENCHMARK_HASHES[(character_id, mode)]
