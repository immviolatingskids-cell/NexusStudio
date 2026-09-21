import json

import pytest

from engine.composer import compose_negative_prompt, compose_prompt
from engine.identity import load_identity_profile
from engine.loader import load_character
from engine.resolver import resolve_scene
from engine.scene_models import SceneBrief
from engine.scoring import score_entry
from engine import takes
from pools.registry import find, find_display


CHARACTERS = [
    "ayami",
    "luna",
    "naomi",
    "zara",
    "idun",
    "charlotte",
]


@pytest.mark.parametrize(
    "character_name",
    CHARACTERS,
)
def test_all_characters_load(character_name):
    character = load_character(character_name)

    assert character.character_id
    assert character.identity.name
    assert 20 <= character.identity.age <= 27
    assert character.appearance
    assert character.occupation.primary


def test_character_is_canonical_after_loading():
    ayami = load_character("ayami")

    assert ayami.identity.name == "Ayami Tanaka"
    assert ayami.identity.age == 23
    assert ayami.identity.nationality == "Japanese"


def test_affinity_weights_are_valid():
    for character_name in CHARACTERS:
        character = load_character(character_name)

        for weight in character.affinities.values():
            assert -3 <= weight <= 3


@pytest.mark.parametrize("character_name", CHARACTERS)
def test_every_character_has_a_matching_identity_profile(character_name):
    character = load_character(character_name)
    profile = load_identity_profile(character.character_id)

    assert profile.character_id == character.character_id
    assert profile.anchors
    assert profile.negative_constraints


def test_scene_resolution_is_seeded_and_identity_safe():
    luna = load_character("luna")
    brief = SceneBrief(
        character_id=luna.character_id,
        activity="getting ready for a concert",
        location="bar",
        wardrobe_style="streetwear",
        lighting="neon_coloured",
        seed=7,
    )
    profile = load_identity_profile(luna.character_id)

    first = resolve_scene(brief, profile)
    second = resolve_scene(brief, profile)

    assert first == second
    assert first.selections["location"] == "bar"
    assert first.selections["wardrobe"] == "modern streetwear"
    assert "copper-auburn" in compose_prompt(first)
    assert "no brown or blonde hair" in compose_negative_prompt(first)


def test_recorded_take_captures_resolved_scene(tmp_path, monkeypatch):
    luna = load_character("luna")
    scene = resolve_scene(
        SceneBrief(character_id=luna.character_id, activity="reading", seed=3),
        load_identity_profile(luna.character_id),
    )
    monkeypatch.setattr(takes, "OUTPUT_DIR", tmp_path)

    record = takes.record_take(scene)

    assert record.is_file()
    assert '"name": "offline-preview"' in record.read_text(encoding="utf-8")
    assert takes.verify_take(json.loads(record.read_text(encoding="utf-8"))["take_id"])


def test_affinities_can_rank_scene_vocabulary_without_changing_identity():
    streetwear = find_display("streetwear", category="style")

    assert streetwear is not None
    assert score_entry(streetwear, {"streetwear": 3}) == 3
