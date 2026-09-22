from pathlib import Path

import pytest

from engine.character_composer import compose_character_by_id
from engine.loader import load_character
from engine.resolver import resolve_character_by_id
from engine.scene_composer import compose_scene_by_id, compose_scene_from_description
from engine.scene_defaults import MODE_DEFAULTS, SCENE_MODES
from engine.scene_context_models import SceneContext


FIXTURES = Path(__file__).parent / "fixtures" / "scenes"


@pytest.mark.parametrize("mode", SCENE_MODES)
def test_each_scene_mode_composes_deterministically(mode):
    first = compose_scene_by_id("luna", mode)
    second = compose_scene_by_id("luna_campbell", mode)

    assert first.to_dict() == second.to_dict()
    assert first.context.mode == mode
    populated_by = set(first.defaulted_fields) | set(first.character_context_fields) | set(first.override_fields)
    assert set(MODE_DEFAULTS[mode]) <= populated_by


@pytest.mark.parametrize(
    ("character_id", "mode", "fixture"),
    (("luna_campbell", "portrait", "luna_portrait.txt"), ("charlotte_taylor_rose", "lifestyle", "charlotte_lifestyle.txt"), ("idun_braten", "workplace", "idun_workplace.txt")),
)
def test_representative_scene_sections_match_golden_fixtures(character_id, mode, fixture):
    expected = (FIXTURES / fixture).read_text(encoding="utf-8").strip()

    assert compose_scene_by_id(character_id, mode).sections[-1].text == expected


def test_explicit_overrides_win_over_character_context_and_defaults():
    scene = compose_scene_by_id("idun", "workplace", {"environment": "a quiet test kitchen", "activity": "reviewing a menu", "lighting": "soft overcast daylight"})

    assert scene.context.environment == "a quiet test kitchen"
    assert scene.context.activity == "reviewing a menu"
    assert scene.context.lighting == "soft overcast daylight"
    assert set(scene.override_fields) == {"environment", "activity", "lighting"}
    assert "environment" not in scene.character_context_fields


def test_character_aware_context_uses_only_existing_canonical_facts():
    workplace = compose_scene_by_id("idun", "workplace")
    hobby = compose_scene_by_id("luna", "hobby")

    assert "chef" in workplace.context.activity
    assert "chef" in workplace.context.environment
    assert hobby.context.activity == "enjoying gym"
    assert hobby.context.environment == "a setting suited to gym"


def test_scene_preserves_visual_identity_and_does_not_mutate_inputs():
    character = load_character("luna")
    description = compose_character_by_id("luna")
    resolution = resolve_character_by_id("luna")
    before = (repr(character), description.to_dict(), resolution.to_dict())

    scene = compose_scene_from_description(description, SceneContext(mode="portrait", environment="a quiet studio", pose="standing naturally"))

    assert "natural auburn hair" in scene.text
    assert "green-hazel" in scene.text
    assert "natural freckles" in scene.text
    assert "naturally curvy" in scene.text
    assert before == (repr(character), description.to_dict(), resolution.to_dict())
