"""Inspectable factual diagnostics for prompt compilation."""

from __future__ import annotations

from dataclasses import dataclass

from engine.prompt_plan import PromptPlan


@dataclass(frozen=True)
class PromptDiagnostics:
    identity_anchors_total: int
    identity_anchors_preserved: int
    scene_fields_included: tuple[str, ...]
    redundancies_removed: tuple[str, ...]
    conflicts: tuple[str, ...]
    fallback_fields_used: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "identity_anchors_total": self.identity_anchors_total,
            "identity_anchors_preserved": self.identity_anchors_preserved,
            "scene_fields_included": list(self.scene_fields_included),
            "redundancies_removed": list(self.redundancies_removed),
            "conflicts": list(self.conflicts),
            "fallback_fields_used": list(self.fallback_fields_used),
        }


def diagnostics_for(plan: PromptPlan) -> PromptDiagnostics:
    included = tuple(name for name, value in (
        ("activity", plan.activity), ("pose", plan.pose), ("environment", plan.environment),
        ("camera", plan.camera), ("lighting", plan.lighting), ("wardrobe", plan.wardrobe),
    ) if value)
    removed = tuple(plan.source_metadata.get("redundancies_removed", ()))
    fallbacks = tuple(plan.source_metadata.get("canonical_fallback_paths", ()))
    return PromptDiagnostics(len(plan.identity_anchors), len(plan.identity_anchors), included, removed, (), fallbacks)
