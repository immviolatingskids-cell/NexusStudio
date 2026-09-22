import json

from engine.prompt_export import render_json_export, render_text_export
from engine.prompt_pipeline import build_prompt
from engine.prompt_refiner import refine_prompt


def test_text_export_is_paste_ready_and_traces_lock_version():
    prompt = build_prompt("ayami", "workplace", density="detailed")
    result = refine_prompt(prompt, "off")
    exported = render_text_export(result)
    assert "Character: Ayami Tanaka" in exported
    assert "Identity lock: 1.1.0" in exported
    assert "Mode: workplace" in exported
    assert "FINAL PROMPT" in exported
    assert result.refined_prompt in exported


def test_json_export_retains_compiled_and_refined_text_and_metadata():
    result = refine_prompt(build_prompt("luna", "portrait"), "off")
    exported = json.loads(render_json_export(result))
    assert exported["compiled_prompt"] == exported["refined_prompt"]
    assert exported["identity_lock_version"] == "1.1.0"
    assert exported["source_metadata"]["identity_lock_version"] == "1.1.0"
