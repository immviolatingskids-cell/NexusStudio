import pytest

from engine.identity import find_identity_conflicts
from engine.loader import load_character
from engine.prompt_compiler import compile_prompt_plan
from engine.prompt_validation import PromptValidationError
from engine.scene_composer import compose_scene


def test_scene_colour_override_cannot_replace_locked_identity():
    character = load_character("ayami")
    scene = compose_scene(character, "portrait", {"wardrobe": "a blue blouse with blonde hair"})
    with pytest.raises(PromptValidationError, match="conflicting"):
        compile_prompt_plan(character, scene.character_description, scene)


def test_mutable_hair_arrangement_and_clothing_colour_are_allowed():
    assert not find_identity_conflicts("ayami_tanaka", "a blue outfit with hair in a ponytail")


def test_hair_and_eye_conflicts_are_reported_separately():
    conflicts = find_identity_conflicts("ayami_tanaka", "blonde hair and green eyes")
    assert len(conflicts) == 2
