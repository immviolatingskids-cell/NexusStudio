"""Optional text-only refinement of deterministic compiler output."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol

from engine.identity import IdentityProfile, find_identity_conflicts, load_identity_profile
from engine.prompt_models import PromptResult


REFINEMENT_MODES = ("off", "balanced", "rich")


class TextRefiner(Protocol):
    name: str
    model: str

    def refine(self, prompt: str, instruction: str = "") -> str: ...


@dataclass(frozen=True)
class RefinedPromptResult:
    character_id: str
    identity_lock_version: str
    mode: str
    density: str
    refinement_mode: str
    compiled_prompt: str
    refined_prompt: str
    refiner_model: str | None = None
    warnings: tuple[str, ...] = ()
    source_metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["warnings"] = list(self.warnings)
        return result


def refinement_instruction(profile: IdentityProfile, plan: dict[str, Any], mode: str) -> str:
    """Build a strict prompt that gives the text model facts, intent, and boundaries."""
    if mode not in REFINEMENT_MODES:
        raise ValueError(f"Unknown refinement mode '{mode}'. Available modes: {', '.join(REFINEMENT_MODES)}")
    locked = "\n".join(f"- {anchor}" for anchor in profile.anchors)
    drift = "\n".join(f"- {item['feature']}: {item['instruction']}" for item in profile.drift_critical_features)
    negatives = "\n".join(f"- {item}" for item in profile.negative_constraints)
    context_fields = ("image_intent", "mode", "style", "scene_style", "wardrobe", "activity", "pose", "environment", "composition", "camera", "lighting", "atmosphere", "identity_constraints")
    context = "\n".join(f"- {field}: {plan[field]}" for field in context_fields if plan.get(field))
    expansion = (
        "Improve grammar, flow, spatial wording, and scene coherence without significantly expanding the prompt."
        if mode == "balanced" else
        "Write a fuller, vivid, spatially clear prompt. Add environmental and pose detail only when it follows directly from the supplied scene facts."
    )
    return f"""You are a text-only image-prompt editor. Return only the revised prompt; do not generate or request an image.

The deterministic compiler is authoritative. {expansion}

LOCKED IDENTITY (preserve every applicable fact; do not add permanent traits):
{locked}

DRIFT-CRITICAL GUARDS:
{drift}

NEGATIVE IDENTITY CONSTRAINTS:
{negatives}

SCENE INTENT AND CONSTRAINTS (preserve exactly):
{context}

You may improve grammar, descriptive richness, natural flow, spatial wording, and scene coherence; remove repetition. You must not change hair or eye colour, facial structure, body baseline, distinguishing marks, requested activity, pose, framing, lighting intent, scene style, or wardrobe direction. Do not invent permanent identity features or omit a drift-critical guard. Do not treat temporary hairstyle, makeup, clothing, jewellery, background, lighting, pose, or props as identity. Preserve the original language and paragraph structure where practical."""


def refine_prompt(
    prompt: PromptResult,
    refinement_mode: str = "off",
    refiner: TextRefiner | None = None,
    *,
    profile: IdentityProfile | None = None,
) -> RefinedPromptResult:
    """Return both compiler text and optional refined text, falling back cleanly."""
    if refinement_mode not in REFINEMENT_MODES:
        raise ValueError(f"Unknown refinement mode '{refinement_mode}'. Available modes: {', '.join(REFINEMENT_MODES)}")
    identity = profile or load_identity_profile(prompt.character_id)
    plan = prompt.source_metadata.get("prompt_plan", {})
    if not isinstance(plan, dict):
        plan = {}
    compiled = prompt.positive_prompt
    warnings = list(prompt.warnings)
    model = None
    refined = compiled
    if refinement_mode != "off":
        if refiner is None:
            warnings.append("Prompt refinement was requested but no text refiner is configured; using compiled prompt.")
        else:
            model = getattr(refiner, "model", None)
            try:
                candidate = refiner.refine(compiled, refinement_instruction(identity, plan, refinement_mode)).strip()
                if candidate:
                    conflicts = find_identity_conflicts(prompt.character_id, candidate)
                    if conflicts:
                        warnings.append("Text refiner contradicted locked identity (" + "; ".join(conflicts) + "); using compiled prompt.")
                    else:
                        refined = candidate
                else:
                    warnings.append("Text refiner returned an empty prompt; using compiled prompt.")
            except Exception as exc:
                warnings.append(f"Text refinement failed ({type(exc).__name__}); using compiled prompt.")
    metadata = dict(prompt.source_metadata)
    metadata["identity_lock_version"] = identity.version
    metadata["refinement_mode"] = refinement_mode
    return RefinedPromptResult(
        character_id=prompt.character_id,
        identity_lock_version=identity.version,
        mode=prompt.source_scene_mode,
        density=str(prompt.source_metadata.get("density", "standard")),
        refinement_mode=refinement_mode,
        compiled_prompt=compiled,
        refined_prompt=refined,
        refiner_model=model,
        warnings=tuple(warnings),
        source_metadata=metadata,
    )
