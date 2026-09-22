"""Small deterministic scene defaults keyed by explicit composition mode."""

SCENE_MODES = ("portrait", "full_body", "lifestyle", "workplace", "hobby", "environmental")

MODE_DEFAULTS = {
    "portrait": {"environment": "a simple neutral environment", "wardrobe": "a simple everyday outfit", "pose": "a relaxed upright pose", "camera": "medium portrait framing at eye level", "lighting": "soft natural daylight", "mood": "calm"},
    "full_body": {"environment": "a simple unobtrusive setting", "wardrobe": "a practical everyday outfit", "pose": "standing naturally", "camera": "full-body framing at eye level", "lighting": "soft natural daylight", "mood": "relaxed"},
    "lifestyle": {"environment": "an everyday local setting", "wardrobe": "casual layered clothing", "pose": "seated casually", "camera": "three-quarter view at eye level", "lighting": "diffused window light", "mood": "relaxed"},
    "workplace": {"environment": "a practical work setting", "wardrobe": "simple workwear", "pose": "working naturally", "camera": "three-quarter view at eye level", "lighting": "soft indoor ambient light", "mood": "focused"},
    "hobby": {"environment": "a setting suited to a familiar hobby", "wardrobe": "comfortable casual clothing", "pose": "engaged naturally with the activity", "camera": "three-quarter view at eye level", "lighting": "soft natural daylight", "mood": "engaged"},
    "environmental": {"environment": "a clearly visible local setting", "wardrobe": "casual practical clothing", "pose": "standing naturally within the setting", "camera": "wide environmental shot at eye level", "lighting": "overcast daylight", "mood": "quiet"},
}
