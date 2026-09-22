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
        refiner = FakeRefiner()
        result = refine_prompt(prompt, mode, refiner)
        assert result.compiled_prompt == prompt.positive_prompt
        assert result.refined_prompt == "Refined image prompt."
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
    assert "contradicted locked identity" in result.warnings[0]
