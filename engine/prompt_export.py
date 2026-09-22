"""Plain-text and JSON export for manual image generation workflows."""

from __future__ import annotations

import json

from engine.prompt_refiner import RefinedPromptResult


def render_text_export(result: RefinedPromptResult) -> str:
    """Format a paste-ready prompt with traceable direction metadata."""
    plan = (result.source_metadata or {}).get("prompt_plan", {})
    character_name = plan.get("character_name") if isinstance(plan, dict) else None
    if not character_name:
        from engine.loader import load_character
        character_name = load_character(result.character_id).identity.name
    return (
        f"Character: {character_name}\n"
        f"Identity lock: {result.identity_lock_version}\n"
        f"Mode: {result.mode}\n"
        f"Density: {result.density}\n"
        f"Refinement: {result.refinement_mode}\n\n"
        "FINAL PROMPT\n------------\n\n"
        f"{result.refined_prompt}\n"
    )


def render_json_export(result: RefinedPromptResult) -> str:
    """Serialize both source and refined prompts with provenance."""
    return json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n"
