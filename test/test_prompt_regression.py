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
    ("ayami_tanaka", "workplace"): "730381f3f78bf64f001d18266aa38d0097e9255e01ed2fec50b9dba0493c4ee9",
    ("ayami_tanaka", "portrait"): "1e03727de6b44c6bdcd461bfaf223de8e7570450106918b83c011ce3aaea900a",
    ("luna_campbell", "lifestyle"): "b168686bc6fcab00556d51b711e8080aa54a27df7ff2cf5a24f0996d5c94fd89",
    ("luna_campbell", "full_body"): "ffed3165a20abb31de71ca5fed2cf556ac24e37026d018ed9fe456ea6a0078d3",
    ("naomi", "hobby"): "82054e758033d66587671bc31bec8aa80f1f8b631fe5e72462487f6e1caafa64",
    ("naomi", "environmental"): "8faee69facef0b076f414d20fadb9d153f83c620f5464dc3f6ef48585d3fa739",
    ("zara", "portrait"): "a0241450f265c0653be347bfc1aea69e9519270488c91409f065c442ab0f6734",
    ("zara", "lifestyle"): "50ad93b1cc48cc29962ceff2b7ce42e392b34b2a4c1e948ff6f89d554e7cb771",
    ("idun_braten", "workplace"): "3956c72b0899d9a3161f3b0337183394e8812ff9df753356a48ea06e17036b87",
    ("idun_braten", "environmental"): "e47acc3d7bbd08b8a34b85b33f6e9e840cc2009cc9bd59d0dc88f25221432552",
    ("charlotte_taylor_rose", "portrait"): "3945926d67bd2bc588adb7bc2fec00ef9c9a4be5b59c4152da9744db7ac3ee2e",
    ("charlotte_taylor_rose", "lifestyle"): "208da36ec3b9edb8a5b2ea85c4edc372030bdd5199e48c216aa65bbbad5d8764",
}


@pytest.mark.parametrize(("character_id", "mode"), BENCHMARK_HASHES)
def test_prompt_quality_benchmark_is_stable(character_id, mode):
    prompt = build_prompt(character_id, mode, "generic").positive_prompt
    assert hashlib.sha256(prompt.encode()).hexdigest() == BENCHMARK_HASHES[(character_id, mode)]
