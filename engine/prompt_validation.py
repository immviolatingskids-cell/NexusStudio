"""Concrete, deterministic coherence checks for prompt plans."""

from __future__ import annotations

from engine.prompt_plan import PromptPlan


class PromptValidationError(ValueError):
    """Raised when scene direction contradicts canonical visual identity."""


def validate_prompt_plan(plan: PromptPlan) -> tuple[str, ...]:
    """Reject obvious contradictions and return non-fatal concrete warnings."""
    combined = " ".join(filter(None, (plan.activity, plan.pose, plan.environment, plan.lighting, plan.composition))).casefold()
    errors: list[str] = []
    if "portrait" in combined and "full-body" in combined:
        errors.append("portrait framing conflicts with full-body framing")
    if "seated" in combined and "standing" in combined:
        errors.append("seated pose conflicts with standing pose")
    if any(word in combined for word in ("indoor", "room", "apartment", "cafe", "restaurant", "workspace")) and "street lighting" in combined:
        errors.append("interior setting conflicts with exterior street lighting")
    if "night" in combined and any(word in combined for word in ("midday sunlight", "noon sunlight")):
        errors.append("night scene conflicts with direct midday sunlight")
    if errors:
        raise PromptValidationError("; ".join(errors))
    return ()
