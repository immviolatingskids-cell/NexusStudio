from dataclasses import asdict

from engine.prompt_pipeline import build_prompt
from engine.prompt_refiner import refine_prompt


class FakeRefiner:
    name = "fake-text"
    model = "fake-model"

    def __init__(self, answer="Refined image prompt.", error=None):
        self.answer = answer
        self.error = error
        self.calls = []

    def refine(self, prompt, instruction=""):
        self.calls.append((prompt, instruction))
        if self.error:
            raise self.error
        return self.answer


def test_off_mode_skips_api_and_keeps_compiled_prompt():
    prompt = build_prompt("ayami", "portrait")
    refiner = FakeRefiner()
    result = refine_prompt(prompt, "off", refiner)
    assert result.refined_prompt == result.compiled_prompt == prompt.positive_prompt
    assert not refiner.calls


def test_balanced_and_rich_send_identity_and_scene_contract_and_keep_both_outputs():
    prompt = build_prompt("ayami", "portrait", density="detailed")
    before = asdict(prompt)
    for mode in ("balanced", "rich"):
        refiner = FakeRefiner(prompt.positive_prompt + " Add a softly textured cafe interior in the background.")
        result = refine_prompt(prompt, mode, refiner)
        assert result.compiled_prompt == prompt.positive_prompt
        assert result.refined_prompt == refiner.answer
        assert result.identity_lock_version == "1.1.0"
        instruction = refiner.calls[0][1]
        assert "LOCKED IDENTITY" in instruction
        assert "DRIFT-CRITICAL GUARDS" in instruction
        assert "SCENE INTENT AND CONSTRAINTS" in instruction
        assert "must not change hair or eye colour" in instruction
    assert asdict(prompt) == before


def test_api_failure_falls_back_to_compiled_prompt():
    prompt = build_prompt("ayami", "portrait")
    result = refine_prompt(prompt, "rich", FakeRefiner(error=RuntimeError("offline")))
    assert result.refined_prompt == result.compiled_prompt
    assert "using compiled prompt" in result.warnings[0]


def test_refiner_output_that_changes_locked_hair_colour_is_rejected():
    prompt = build_prompt("ayami", "portrait")
    result = refine_prompt(prompt, "rich", FakeRefiner("Give her blonde hair and green eyes."))
    assert result.refined_prompt == result.compiled_prompt
    assert "violated the protected prompt contract" in result.warnings[0]


def test_refiner_cannot_add_conflicting_facial_geometry():
    prompt = build_prompt("ayami", "portrait", density="detailed")
    result = refine_prompt(prompt, "rich", FakeRefiner(prompt.positive_prompt + " Give her a broad square face and sharp jaw."))
    assert result.refined_prompt == result.compiled_prompt
    assert "facial geometry" in result.warnings[0]


def test_refiner_cannot_change_body_baseline():
    prompt = build_prompt("ayami", "portrait", density="detailed")
    result = refine_prompt(prompt, "rich", FakeRefiner(prompt.positive_prompt + " She is frail and heavily muscular."))
    assert result.refined_prompt == result.compiled_prompt
    assert "body proportions" in result.warnings[0]


def test_refiner_cannot_omit_a_distinguishing_mark():
    prompt = build_prompt("ayami", "portrait", density="detailed")
    candidate = prompt.positive_prompt.replace("small beauty mark below her left eye", "no beauty mark", 1)
    result = refine_prompt(prompt, "rich", FakeRefiner(candidate))
    assert result.refined_prompt == result.compiled_prompt
    assert "distinguishing identity" in result.warnings[0]


def test_refiner_cannot_remove_or_hide_a_distinguishing_mark():
    prompt = build_prompt("ayami", "portrait", density="detailed")
    result = refine_prompt(prompt, "rich", FakeRefiner(prompt.positive_prompt + " Remove the beauty mark below her left eye."))
    assert result.refined_prompt == result.compiled_prompt
    assert "distinguishing mark" in result.warnings[0]


def test_refiner_falls_back_when_a_scene_contract_changes():
    prompt = build_prompt("ayami", "workplace", density="detailed")
    plan = prompt.source_metadata["prompt_plan"]
    replacements = (
        ("activity", "She is dancing."),
        ("composition", "Use a close-up portrait."),
        ("lighting", "Harsh flash lighting."),
        ("wardrobe", "She is dressed in a red evening gown."),
        ("environment", "The scene is set on a beach."),
    )
    for field, replacement in replacements:
        original = plan[field]
        candidate = prompt.positive_prompt.replace(original, replacement, 1)
        result = refine_prompt(prompt, "balanced", FakeRefiner(candidate))
        assert result.refined_prompt == result.compiled_prompt, field
        assert "violated the protected prompt contract" in result.warnings[0], field
