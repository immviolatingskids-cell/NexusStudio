"""Structured prompt output and identity-safety linting."""

from __future__ import annotations

from dataclasses import asdict, dataclass

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

    def to_dict(self) -> dict:
        return asdict(self)

    def render(self) -> str:
        return " ".join((
            "Photograph of the established character.",
            "Identity anchors: " + "; ".join(self.identity) + ".",
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


def compose_prompt_document(scene: ResolvedScene) -> PromptDocument:
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
        identity=scene.identity_anchors,
        direction=tuple(direction),
        technical=tuple(item for item in technical if item),
        negative=scene.negative_constraints,
    )
    lint_prompt(document)
    return document
