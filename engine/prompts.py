"""Structured prompt output and identity-safety linting."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from engine.identity import load_identity_profile
from engine.scene_models import ResolvedScene
from engine.versions import PROMPT_DOCUMENT_VERSION
from pools.realism import realism_text


class PromptLintError(ValueError):
    pass


@dataclass(frozen=True)
class PromptDocument:
    schema_version: str
    identity: tuple[str, ...]
    direction: tuple[str, ...]
    technical: tuple[str, ...]
    negative: tuple[str, ...]
    identity_diagnostics: dict[str, Any] | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    def render(self) -> str:
        identity = "; ".join(
            item.strip().rstrip(".!?")
            for item in self.identity
            if item and item.strip()
        )
        return " ".join((
            "Photograph of the established character.",
            "Identity anchors: " + identity + ".",
            "Scene direction: " + "; ".join(self.direction) + ".",
            "Technical guidance: " + "; ".join(self.technical) + ".",
        ))


def lint_prompt(document: PromptDocument) -> None:
    if not document.identity:
        raise PromptLintError("Prompt is missing immutable identity anchors.")
    if not document.direction:
        raise PromptLintError("Prompt is missing scene direction.")
    normalized = [item.casefold().strip() for section in (document.identity, document.direction, document.technical) for item in section]
    if len(normalized) != len(set(normalized)):
        raise PromptLintError("Prompt contains duplicate clauses.")
    direction_text = " ".join(document.direction).casefold()
    for negative in document.negative:
        prohibited = negative.removeprefix("no ").strip().casefold()
        if prohibited and prohibited in direction_text:
            raise PromptLintError(f"Scene direction conflicts with identity constraint: {negative}")


def compose_prompt_document(scene: ResolvedScene, density: str = "standard") -> PromptDocument:
    if density not in {"compact", "standard", "detailed"}:
        raise ValueError(f"Unknown prompt density '{density}'.")
    profile = load_identity_profile(scene.brief.character_id)
    drift = tuple(item["instruction"] for item in profile.drift_critical_features)
    identity_block = (profile.prompt_identity_blocks or {}).get(density)
    if identity_block:
        identity = (identity_block,) + drift
    elif density == "compact":
        identity = profile.critical_anchors + drift
    else:
        identity = profile.critical_anchors + profile.strong_anchors + drift
        if profile.identity_relationships:
            identity += tuple(
                f"{key.replace('_', ' ')}: {value}"
                for key, value in profile.identity_relationships.items()
                if key != "priority"
            )
        if density == "detailed" and profile.expression_behavior:
            expressions = profile.expression_behavior
            identity += tuple(
                f"expression behavior ({key}): {value}"
                for key, value in expressions.items()
                if key != "priority"
            )
    selection = scene.selections
    direction = [
        f"{selection['pose']} in a {selection['location']}",
        selection["wardrobe"],
        f"{selection['lighting']} lighting",
        f"{selection['atmosphere']} atmosphere",
    ]
    for key, prefix in (("activity", "activity: "), ("hair_style", "hair styling: "), ("expression", "expression: "), ("season", "season: ")):
        if key in selection:
            direction.append(prefix + selection[key])
    technical = [
        f"{selection['framing']} framing",
        realism_text(scene.brief.image_style, framing=selection["framing"]),
    ]
    document = PromptDocument(
        schema_version=PROMPT_DOCUMENT_VERSION,
        identity=identity,
        direction=tuple(direction),
        technical=tuple(item for item in technical if item),
        negative=scene.negative_constraints,
        identity_diagnostics={
            "identity_lock_version": profile.version,
            "critical_traits": len(profile.critical_anchors),
            "strong_traits": len(profile.strong_anchors),
            "drift_critical_traits": len(profile.drift_critical_features),
            "scene_conflicts": 0,
            "style_conflicts": 0,
            "protected_traits": list(profile.immutable_features),
            "mutable_traits": sorted(profile.mutable_features),
            "reference_confidence": (profile.reference_consensus or {}).get("confidence"),
        },
    )
    lint_prompt(document)
    return document
