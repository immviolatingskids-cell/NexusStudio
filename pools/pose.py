from pool_models import PoolEntry


def _pose(id: str, label: str, category: str, tags: set[str] = set(), **metadata) -> PoolEntry:
    return PoolEntry(id, label, {"pose", *tags}, metadata={"category": category, "label": label, **metadata})


POSE_CATEGORIES = ("base_pose", "hand_pose", "sitting_pose", "body_orientation", "head_yaw", "head_pitch", "eye_line")

POOL = (
    *(_pose(f"pose_base_{name}", name.replace("_", " "), "base_pose", {name}) for name in ("standing", "leaning", "sitting", "walking")),
    *(_pose(f"pose_hand_{name}", name.replace("_", " "), "hand_pose", {name}) for name in ("hand_on_hip", "arms_crossed", "hand_to_face", "adjusting_hair", "hand_near_mouth", "hands_together", "holding_object")),
    *(_pose(f"pose_sitting_{name}", name.replace("_", " "), "sitting_pose", {name}) for name in ("cross_legged", "knees_up", "side_sit")),
    *(_pose(f"pose_orientation_{name}", name.replace("_", " "), "body_orientation", {name}) for name in ("front", "three_quarter", "profile", "looking_back")),
    _pose("pose_yaw_left_45", "left 45 degrees", "head_yaw", {"left_45"}, degrees=-45, direction="left"),
    _pose("pose_yaw_left_20", "left 20 degrees", "head_yaw", {"left_20"}, degrees=-20, direction="left"),
    _pose("pose_yaw_forward", "forward", "head_yaw", {"forward"}, degrees=0, direction="forward"),
    _pose("pose_yaw_right_20", "right 20 degrees", "head_yaw", {"right_20"}, degrees=20, direction="right"),
    _pose("pose_yaw_right_45", "right 45 degrees", "head_yaw", {"right_45"}, degrees=45, direction="right"),
    *(_pose(f"pose_pitch_{name}", name, "head_pitch", {name}) for name in ("down", "neutral", "up")),
    *(_pose(f"pose_eye_{name}", name.replace("_", " "), "eye_line", {name}) for name in ("camera", "away_left", "away_right", "down", "up", "side_glance")),
)
