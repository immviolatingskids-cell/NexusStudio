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
    ("ayami_tanaka", "workplace"): "099fa1fd7d6f7bb05e6e2047f46e8298b629cce427773d5d3add7754d35f2985",
    ("ayami_tanaka", "portrait"): "2da4a53c14129cee55fd1e47187dc9d78cc35bccfaf40c22649bf38896e745e2",
    ("luna_campbell", "lifestyle"): "62bcb46a75e66e2404640eb442618d16b6c3a5540be9b794946602a1b1d26012",
    ("luna_campbell", "full_body"): "185145ac923c6b16084cbfcc4a4c8a95b69fbdf48ec6ae031c222eb3d4f2de95",
    ("naomi", "hobby"): "613cba226f02a8deca3697614bc3163a312ff810cc94bc604f95a37accd4cd4d",
    ("naomi", "environmental"): "d1a5f1c3fcdb454ed82e0d2275b9a7218e6ac5ce47e558f42445205fd3a089b2",
    ("zara", "portrait"): "ae2312891f474105a4ad88ad56d8262ee11843858ee3dcb4d2090d247765bb3a",
    ("zara", "lifestyle"): "2ae9138c1d92d0d5fd98e970d49758e7c71c2fe2f615e08833075ef5196c3f91",
    ("idun_braten", "workplace"): "e87f74caf40c89241379d2726ea1941067af56fec104f0d31acf1421f6833dd9",
    ("idun_braten", "environmental"): "883226e52665bddb62f7dcc9cb8a1d28d99e4b4ff90403ea9f7b414e1a9e641f",
    ("charlotte_taylor_rose", "portrait"): "c4b60b0b21c1cdc490c589a0dbecca80587eb0f4b086e1d092ead8132e2a7d83",
    ("charlotte_taylor_rose", "lifestyle"): "57de42695eeac9a984141a838b5f8b764f3a4c1e7a329c1d0d6359c2772ab86a",
}


@pytest.mark.parametrize(("character_id", "mode"), BENCHMARK_HASHES)
def test_prompt_quality_benchmark_is_stable(character_id, mode):
    prompt = build_prompt(character_id, mode, "generic").positive_prompt
    assert hashlib.sha256(prompt.encode()).hexdigest() == BENCHMARK_HASHES[(character_id, mode)]
