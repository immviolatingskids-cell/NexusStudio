from pool_models import PoolEntry

FACE_CATEGORIES = ("face_shape", "eye_shape", "eye_colour", "brow_shape", "brow_density", "nose_shape", "lip_shape", "lip_fullness", "distinguishing_feature", "expression", "makeup")

def _face(id: str, label: str, category: str, tags: set[str] = set(), **metadata) -> PoolEntry:
    return PoolEntry(id, label, {"face", *tags}, metadata={"category": category, "label": label, **metadata})

POOL = (
    *(_face(f"face_shape_{name}", name, "face_shape", {name}) for name in ("oval", "round", "square", "heart", "oblong", "diamond")),
    *(_face(f"face_eye_shape_{name}", name, "eye_shape", {name}) for name in ("almond", "round", "hooded", "monolid", "upturned", "downturned")),
    *(_face(f"face_eye_colour_{name}", name, "eye_colour", {name}) for name in ("brown", "hazel", "green", "blue", "grey", "amber")),
    *(_face(f"face_brow_shape_{name}", name.replace("_", " "), "brow_shape", {name}) for name in ("straight", "arched", "soft_arch", "untamed")),
    *(_face(f"face_brow_density_{name}", name, "brow_density", {name}) for name in ("thin", "medium", "thick")),
    *(_face(f"face_nose_shape_{name}", name, "nose_shape", {name}) for name in ("straight", "button", "upturned", "roman", "wide", "narrow")),
    *(_face(f"face_lip_shape_{name}", name.replace("_", " "), "lip_shape", {name}) for name in ("natural", "cupids_bow", "wide", "downturned")),
    *(_face(f"face_lip_fullness_{name}", name, "lip_fullness", {name}) for name in ("thin", "medium", "full")),
    _face("face_feature_freckles", "freckles", "distinguishing_feature", {"freckles"}, feature_type="skin_detail", intensity="variable", size="variable", prominence="variable"),
    _face("face_feature_mole", "mole", "distinguishing_feature", {"mole"}, feature_type="skin_detail", location="variable", size="variable", prominence="variable"),
    _face("face_feature_dimples", "dimples", "distinguishing_feature", {"dimples"}, feature_type="skin_detail", location="cheeks_or_chin", prominence="variable"),
    _face("face_feature_scar", "scar", "distinguishing_feature", {"scar"}, feature_type="skin_detail", location="variable", intensity="variable", prominence="variable"),
    _face("face_feature_piercing", "piercing", "distinguishing_feature", {"piercing"}, feature_type="jewellery", location="ear_nose_or_face", prominence="variable"),
    _face("face_feature_birthmark", "birthmark", "distinguishing_feature", {"birthmark"}, feature_type="skin_detail", location="variable", size="variable", prominence="variable"),
    *(_face(f"face_expression_{name}", name, "expression", {name}) for name in ("neutral", "happy", "sad", "angry", "surprised", "playful", "thoughtful")),
    *(_face(f"face_makeup_{name}", name.replace("_", " "), "makeup", {name}) for name in ("none", "natural", "soft_glam", "full_glam", "winged_eyeliner", "bold_lipstick")),
    PoolEntry("face_defined_cheekbones", "defined cheekbones", {"cheekbones"}, metadata={"category": "distinguishing_feature", "label": "defined cheekbones", "feature_type": "anatomy", "source": "legacy compatibility"}),
    PoolEntry("face_soft_rounded", "soft rounded features", {"rounded_features", "soft"}, metadata={"category": "face_shape", "label": "soft rounded features", "source": "legacy compatibility"}),
    PoolEntry("face_full_lips", "full natural lips", {"full_lips", "natural"}, metadata={"category": "lip_fullness", "label": "full natural lips", "source": "legacy compatibility"}),
    PoolEntry("face_thick_brows", "thick natural brows", {"thick_brows", "natural"}, metadata={"category": "brow_density", "label": "thick natural brows", "source": "legacy compatibility"}),
    PoolEntry("face_prominent_nose", "straight prominent nose", {"prominent_nose"}, metadata={"category": "nose_shape", "label": "straight prominent nose", "source": "legacy compatibility"}),
)
