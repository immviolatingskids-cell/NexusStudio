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
    ("ayami_tanaka", "workplace"): "357391d76385bf2303ad8b1d33a7204b01bdbbc33cdd93843ae174bc8f6ca44b",
    ("ayami_tanaka", "portrait"): "5506ec29b6a7628799ed16bcb1e6d9888856362f139dec03ef46ab1b215ad98e",
    ("luna_campbell", "lifestyle"): "5669022662fd336e1df8eaedde14a1ada07f3f62171a47e9957dc8e6df3eead5",
    ("luna_campbell", "full_body"): "3682aa1d450825b7ff8b70dfb76224e07112c819a419336b83087cfa7f061c55",
    ("naomi", "hobby"): "ead29ffe3c3cc9675481c01645d32b95c7800bfd2a5dc3c0a28042050fc05c06",
    ("naomi", "environmental"): "9079d41a546db4edad2cd9d5412151bf686ca75b8d10ff3073962c70c05ed7a8",
    ("zara", "portrait"): "74a6d7bce168f8136f7a0003d2e8aabe408683c2d5077c48ba1f6f3ef025e88b",
    ("zara", "lifestyle"): "50f7108260cc48bc7eb7cf7652a0392b9d99dd3bd3aa197cac8fca74054814c1",
    ("idun_braten", "workplace"): "a68e7e102899c197c7f843ada2231cf93639b0d117ee7aff146c2e649d0f0626",
    ("idun_braten", "environmental"): "94c86d53a3d01a310ec99c840102d8477e1f5878aa6e38232f1147e6cc9a0709",
    ("charlotte_taylor_rose", "portrait"): "5f7125264d4cc1f60114411e4b8c6e31954aafa71a5cff68a2bb29572cd2f62f",
    ("charlotte_taylor_rose", "lifestyle"): "89c2713fb55597b72f73788bb1252a37df97c1fd8937f0e718af6fb8e4c66563",
}


@pytest.mark.parametrize(("character_id", "mode"), BENCHMARK_HASHES)
def test_prompt_quality_benchmark_is_stable(character_id, mode):
    prompt = build_prompt(character_id, mode, "generic").positive_prompt
    assert hashlib.sha256(prompt.encode()).hexdigest() == BENCHMARK_HASHES[(character_id, mode)]
