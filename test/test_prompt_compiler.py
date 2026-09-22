from engine.character_composer import compose_character
from engine.loader import load_character
from engine.prompt_compiler import compile_prompt_plan
from engine.scene_composer import compose_scene


def _plan(character_id="luna", mode="portrait", density="standard"):
    character = load_character(character_id)
    scene = compose_scene(character, mode)
    return compile_prompt_plan(character, scene.character_description, scene, density)


def test_identity_anchors_survive_every_density():
    plans = tuple(_plan(density=density) for density in ("compact", "standard", "detailed"))
    assert all("natural auburn-copper" in " ".join(plan.identity_anchors) for plan in plans)
    assert all("green-hazel eyes" in plan.identity_anchors for plan in plans)


def test_environmental_mode_orders_environment_before_action():
    plan = _plan("naomi", "environmental")
    from engine.adapters.base import source_sections
    ids = tuple(section.id for section in source_sections(plan))
    assert ids.index("environment") < ids.index("action")


def test_compiler_is_deterministic_and_does_not_mutate_inputs():
    character = load_character("idun")
    visual = compose_character(character)
    scene = compose_scene(character, "workplace")
    before = (repr(character), visual.to_dict(), scene.to_dict())
    assert compile_prompt_plan(character, visual, scene).to_dict() == compile_prompt_plan(character, visual, scene).to_dict()
    assert before == (repr(character), visual.to_dict(), scene.to_dict())


def test_compact_omits_supporting_detail_before_identity():
    compact = _plan(density="compact")
    detailed = _plan(density="detailed")
    assert compact.face_description is None
    assert detailed.face_description
    assert set(compact.identity_anchors).issubset(set(detailed.identity_anchors))


def test_all_adapters_receive_the_same_compiled_plan():
    from engine.prompt_pipeline import build_prompt

    plans = [build_prompt("charlotte", "lifestyle", adapter).source_metadata["prompt_plan"] for adapter in ("generic", "openai", "gemini")]
    assert plans[0] == plans[1] == plans[2]
