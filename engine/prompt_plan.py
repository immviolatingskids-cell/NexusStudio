"""Model-independent semantic plan for a generation-ready character prompt."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class PromptPlan:
    """The selected visual direction before an adapter renders prose.

    Fields are deliberately small, ordered prose units rather than raw source
    dictionaries.  This makes the compiler's priority decisions inspectable
    while keeping adapters free of semantic selection logic.
    """

    character_id: str
    character_name: str
    mode: str
    density: str
    image_intent: str
    subject_identity: str
    identity_anchors: tuple[str, ...]
    body_description: str | None = None
    face_description: str | None = None
    hair_description: str | None = None
    wardrobe: str | None = None
    activity: str | None = None
    pose: str | None = None
    environment: str | None = None
    composition: str | None = None
    camera: str | None = None
    lighting: str | None = None
    atmosphere: str | None = None
    quality_constraints: tuple[str, ...] = ()
    identity_constraints: tuple[str, ...] = ()
    omitted_fields: tuple[str, ...] = ()
    source_metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
