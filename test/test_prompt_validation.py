import pytest

from engine.prompt_plan import PromptPlan
from engine.prompt_validation import PromptValidationError, validate_prompt_plan


def _plan(**changes):
    values = dict(character_id="test", character_name="Test", mode="portrait", density="standard", image_intent="Photorealistic portrait", subject_identity="Test subject", identity_anchors=("auburn hair",))
    values.update(changes)
    return PromptPlan(**values)


@pytest.mark.parametrize(("changes", "message"), (({"pose":"seated naturally", "composition":"full-body portrait framing"}, "portrait framing"), ({"pose":"standing naturally and seated casually"}, "seated pose"), ({"environment":"an indoor room", "lighting":"street lighting"}, "interior setting"), ({"environment":"a night exterior", "lighting":"direct midday sunlight"}, "night scene")))
def test_obvious_scene_contradictions_fail_loudly(changes, message):
    with pytest.raises(PromptValidationError, match=message):
        validate_prompt_plan(_plan(**changes))


def test_coherent_plan_passes_without_warnings():
    assert validate_prompt_plan(_plan(pose="seated naturally", environment="a quiet cafe", lighting="soft window daylight")) == ()
