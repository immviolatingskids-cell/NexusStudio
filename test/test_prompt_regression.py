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
    ("ayami_tanaka", "workplace"): "40ad1488145bb82d835d0fe5fd728c3ec8538d59523ba741424c01a8934c67fe",
    ("ayami_tanaka", "portrait"): "0df2c2bd0cb7add35408bfe4580ccabaa9b5995d987d341ab1707b135504e8b5",
    ("luna_campbell", "lifestyle"): "60af25eb2b8f90d129a535cd6ad8fc070f8b8816fb5b4712945e41fc4cfc7a4b",
    ("luna_campbell", "full_body"): "93342c4cef39ac25ad76df3ce32f87cd7726dc1366f009832816ebaedd7e298c",
    ("naomi", "hobby"): "4b73a1860162bcb3558caf81c4926b61e9347bef4b90df737de805a92bd55076",
    ("naomi", "environmental"): "3c72184d4dc1c6bd329f9ebef26b44ac33b005595d504ca2618633a7d279b1e9",
    ("zara", "portrait"): "2e192989db5492a71ca242a73ba3c0473132ac3af033e7d4521e52d28bdeda89",
    ("zara", "lifestyle"): "ef7a99c572e1844d51546499a0ef0700a054b7f0e6d521cbf51e01ff0cc794bb",
    ("idun_braten", "workplace"): "586762207cfaa081cc7410fc570dce0e522139620068c2ee0ee1de85eb062de9",
    ("idun_braten", "environmental"): "4543b17fb26aa48485118c9c6b7885fac01b3056cc7889fbde626476ab85498a",
    ("charlotte_taylor_rose", "portrait"): "f55042de26b95747db1409a4babbae2ca43f4831ee8537ce40aec69506e84773",
    ("charlotte_taylor_rose", "lifestyle"): "a7d3bd268ae268b2b95a6feb3d24e4b04be2edd4c5e157b9713f83377ce940d8",
}


@pytest.mark.parametrize(("character_id", "mode"), BENCHMARK_HASHES)
def test_prompt_quality_benchmark_is_stable(character_id, mode):
    prompt = build_prompt(character_id, mode, "generic").positive_prompt
    assert hashlib.sha256(prompt.encode()).hexdigest() == BENCHMARK_HASHES[(character_id, mode)]
