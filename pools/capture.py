from pool_models import PoolEntry


def _capture(id: str, label: str, category: str, tags: set[str] = set(), **metadata) -> PoolEntry:
    return PoolEntry(id, label, {"capture", *tags}, metadata={"category": category, "label": label, **metadata})


CAPTURE_CATEGORIES = ("camera_elevation", "framing", "composition")

POOL = (
    *(_capture(f"capture_elevation_{name}", name.replace("_", " "), "camera_elevation", {name}) for name in ("high", "slightly_high", "eye_level", "slightly_low", "low")),
    *(_capture(f"capture_framing_{name}", name.replace("_", " "), "framing", {name}) for name in ("close_up", "medium", "full_body")),
    _capture("capture_composition_centered", "centered", "composition", {"centered"}, headroom="balanced"),
    _capture("capture_composition_rule_of_thirds", "rule of thirds", "composition", {"rule_of_thirds"}, headroom="intentional_space"),
    _capture("capture_composition_natural_frame", "natural frame", "composition", {"natural_frame"}, headroom="contextual_space"),
)
