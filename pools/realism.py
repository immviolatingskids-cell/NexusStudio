from __future__ import annotations

from pool_models import PoolEntry

REALISM_CATEGORIES = ("skin_detail", "facial_variation", "hair_detail", "body_detail", "clothing_detail", "environment_detail", "camera_detail")
REALISM_PROFILES = ("clean", "natural", "documentary")


def _realism(id: str, text: str, category: str, **metadata) -> PoolEntry:
    return PoolEntry(id, text, {"realism", category}, metadata={"category": category, "label": text, **metadata})


POOL = (
    *(_realism(f"realism_skin_{name}", name.replace("_", " "), "skin_detail") for name in ("visible_pores", "natural_skin_texture", "slight_redness", "subtle_blemishes", "uneven_skin_tone", "fine_lines", "slight_dryness")),
    *(_realism(f"realism_face_{name}", name.replace("_", " "), "facial_variation") for name in ("subtle_asymmetry", "uneven_brows", "natural_feature_variation", "relaxed_expression")),
    *(_realism(f"realism_hair_{name}", name.replace("_", " "), "hair_detail") for name in ("flyaway_hairs", "baby_hairs", "loose_strands", "natural_parting", "slight_messiness", "realistic_hair_texture")),
    *(_realism(f"realism_body_{name}", name.replace("_", " "), "body_detail") for name in ("realistic_proportions", "natural_posture", "natural_skin_folds", "subtle_softness")),
    *(_realism(f"realism_clothing_{name}", name.replace("_", " "), "clothing_detail") for name in ("fabric_wrinkles", "natural_drape", "lived_in_fit", "fabric_texture")),
    *(_realism(f"realism_environment_{name}", name.replace("_", " "), "environment_detail") for name in ("lived_in_space", "everyday_details", "realistic_background", "physical_consistency")),
    *(_realism(f"realism_camera_{name}", name.replace("_", " "), "camera_detail") for name in ("realistic_photography", "shallow_depth_of_field", "slight_grain", "minimally_retouched", "documentary_feel", "smartphone_photo", "dslr_photo")),
)

PROFILE_WEIGHTS = {"clean": 3, "natural": 5, "documentary": 7}
PROFILE_INTENSITY = {"clean": "restrained", "natural": "natural", "documentary": "stronger"}
ANTI_PERFECTION_TERMS = ("flawless skin", "poreless skin", "perfect face", "perfect body", "perfect symmetry", "porcelain skin", "unreal engine", "render")


def realism_entries(category: str | None = None) -> tuple[PoolEntry, ...]:
    if category is None:
        return POOL
    if category not in REALISM_CATEGORIES:
        raise KeyError(f"Unknown realism category: {category}")
    return tuple(entry for entry in POOL if entry.metadata["category"] == category)


def select_realism_anchors(profile: str = "natural", *, framing: str | None = None, mode: str | None = None) -> tuple[PoolEntry, ...]:
    if profile not in REALISM_PROFILES:
        raise ValueError(f"Unsupported realism profile: {profile}")
    if framing == "close_up":
        categories = ("skin_detail", "facial_variation", "hair_detail", "camera_detail")
    elif framing == "full_body":
        categories = ("body_detail", "clothing_detail", "hair_detail", "camera_detail")
    elif mode == "environmental":
        categories = ("environment_detail", "camera_detail", "lighting_detail")
    else:
        categories = ("skin_detail", "hair_detail", "clothing_detail", "environment_detail", "camera_detail")
    by_category = {category: [entry for entry in POOL if entry.metadata["category"] == category] for category in categories}
    selected: list[PoolEntry] = []
    # Take one anchor from each relevant dimension first, then fill the small
    # profile budget. This keeps subsets representative without emitting all
    # available realism vocabulary.
    for category in categories:
        if by_category.get(category):
            selected.append(by_category[category].pop(0))
    for category in categories:
        if len(selected) >= PROFILE_WEIGHTS[profile]:
            break
        if by_category.get(category):
            selected.append(by_category[category][0])
    return tuple(selected[:PROFILE_WEIGHTS[profile]])


def realism_text(profile: str, *, framing: str | None = None, mode: str | None = None) -> str:
    entries = select_realism_anchors(profile, framing=framing, mode=mode)
    labels = ", ".join(entry.text for entry in entries)
    return f"{PROFILE_INTENSITY[profile]} photographic realism: {labels}." if labels else ""


def realism_for_scene(scene) -> str:
    camera = (scene.context.camera or "").lower()
    framing = "close_up" if "close" in camera else "full_body" if "full" in camera else None
    return realism_text(scene.realism_profile, framing=framing, mode=scene.mode)
