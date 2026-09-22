"""Optional text-only refinement of deterministic compiler output."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Protocol

from engine.identity import IdentityProfile, find_identity_conflicts, load_identity_profile
from engine.prompt_models import PromptResult


REFINEMENT_MODES = ("off", "balanced", "rich")
_SCENE_CONTRACTS = {
    "activity": "activity",
    "framing": "composition",
    "lighting": "lighting",
    "wardrobe": "wardrobe",
    "location": "environment",
}
_FACE_CONTRADICTION_RULES = (
    ("round or broad facial silhouette", re.compile(r"\b(?:round|broad)(?:\s+\w+){0,2}\s+(?:face|facial silhouette)\b", re.I)),
    ("square jaw", re.compile(r"\bsquare jaw(?:line)?\b", re.I)),
    ("angular masculine jaw", re.compile(r"\bangular(?: masculine)? jaw(?:line)?\b", re.I)),
    ("long angular face", re.compile(r"\blong angular face\b", re.I)),
    ("short round face", re.compile(r"\bshort round face\b", re.I)),
    ("hollow cheeks", re.compile(r"\bhollow cheeks?\b", re.I)),
    ("sharp jawline", re.compile(r"\bsharp jaw(?:line)?\b", re.I)),
    ("narrow close-set eyes", re.compile(r"\bnarrow close[- ]set eyes?\b", re.I)),
    ("tiny narrow mouth", re.compile(r"\btiny narrow mouth\b", re.I)),
    ("button nose", re.compile(r"\bbutton nose\b", re.I)),
    ("weak narrow jaw", re.compile(r"\bweak narrow jaw\b", re.I)),
    ("round full-cheek face", re.compile(r"\bround full[- ]cheek face\b", re.I)),
    ("narrow angular face", re.compile(r"\bnarrow angular face\b", re.I)),
    ("thin lips", re.compile(r"\bthin lips?\b", re.I)),
)
_BODY_CONTRADICTIONS = re.compile(
    r"\b(?:frail|underweight|gaunt|petite|heavily muscular|heavily muscled|"
    r"very lean|narrow athletic|straight narrow|exaggerated hourglass)\s+"
    r"(?:body|build|frame|physique|proportions?)\b|\b(?:frail|underweight|gaunt)\s+"
    r"(?:and\s+)?(?:heavily\s+)?muscular\b",
    re.IGNORECASE,
)
_DISTINGUISHING_MARK_REMOVAL = re.compile(
    r"\b(?:remove|omit|erase|hide|without|no longer has|missing)\b"
    r"[^.!?]{0,50}\b(?:beauty mark|freckles?|moles?|scars?)\b",
    re.IGNORECASE,
)
_FRAMING_OPPOSITES = {
    "full_body": re.compile(r"\b(?:medium portrait|close[- ]?up|waist[- ]up|cropped at the waist)\b", re.I),
    "portrait": re.compile(r"\b(?:full[- ]body|entire figure visible|wide environmental composition)\b", re.I),
    "environmental": re.compile(r"\b(?:close[- ]?up|tight portrait|face[- ]only crop)\b", re.I),
}
_HARSH_LIGHT = re.compile(r"\b(?:harsh flash|direct flash|hard flash lighting)\b", re.I)
_NEGATION = re.compile(r"\b(?:no|not|never|without|avoid|rather than|do not)\b", re.I)


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


def _normalized(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def _affirmative_match(pattern: re.Pattern[str], text: str) -> bool:
    """Ignore prohibited terms when they occur in an explicit negative clause."""
    for clause in re.split(r"[.!?;\n]+", text):
        if pattern.search(clause) and not _NEGATION.search(clause):
            return True
    return False


def validate_refined_output(
    prompt: PromptResult,
    candidate: str,
    profile: IdentityProfile,
    plan: dict[str, Any],
) -> tuple[str, ...]:
    """Reject refined text that drops protected identity or scene contracts."""
    violations: list[str] = []
    density = str(plan.get("density", prompt.source_metadata.get("density", "standard")))
    identity_block = (profile.prompt_identity_blocks or {}).get(density)
    candidate_text = _normalized(candidate)
    if identity_block and _normalized(identity_block) not in candidate_text:
        violations.append("locked facial, body, or distinguishing identity was omitted or rewritten")
    if any(_normalized(item["instruction"]) not in candidate_text for item in profile.drift_critical_features):
        violations.append("a drift-critical identity guard was omitted or rewritten")

    for category, field in _SCENE_CONTRACTS.items():
        value = plan.get(field)
        if isinstance(value, str) and value.strip() and _normalized(value) not in candidate_text:
            violations.append(f"{category} intent was omitted or changed")

    color_conflicts = find_identity_conflicts(prompt.character_id, candidate)
    violations.extend(color_conflicts)
    negative_text = " ".join(profile.negative_constraints).casefold()
    if any(
        forbidden.casefold() in negative_text and _affirmative_match(pattern, candidate)
        for forbidden, pattern in _FACE_CONTRADICTION_RULES
    ):
        violations.append("facial geometry contradicts the locked profile")
    if _affirmative_match(_BODY_CONTRADICTIONS, candidate):
        violations.append("body proportions contradict the locked profile")
    if _affirmative_match(_DISTINGUISHING_MARK_REMOVAL, candidate):
        violations.append("a distinguishing mark or freckle was removed")

    composition = str(plan.get("composition", "")).casefold()
    framing_type = (
        "full_body" if "full-body" in composition or "entire figure" in composition
        else "environmental" if "wide environmental" in composition
        else "portrait" if "portrait" in composition or "waist upward" in composition
        else None
    )
    if framing_type and _affirmative_match(_FRAMING_OPPOSITES[framing_type], candidate):
        violations.append("framing contradicts the compiled composition")
    if _affirmative_match(_HARSH_LIGHT, candidate) and any(
        term in str(plan.get("lighting", "")).casefold()
        for term in ("soft", "diffused", "overcast", "natural daylight")
    ):
        violations.append("lighting contradicts the compiled lighting intent")
    return tuple(dict.fromkeys(violations))


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
                    violations = validate_refined_output(prompt, candidate, identity, plan)
                    if violations:
                        warnings.append("Text refiner violated the protected prompt contract (" + "; ".join(violations) + "); using compiled prompt.")
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
