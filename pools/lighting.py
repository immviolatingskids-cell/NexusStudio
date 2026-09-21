from pool_models import PoolEntry


LIGHTING_CATEGORIES = ("light_direction", "light_quality", "colour_temperature", "lighting_setup", "atmosphere")


def _light(id: str, label: str, category: str, tags: set[str] = set(), **metadata) -> PoolEntry:
    return PoolEntry(id, label, {"lighting", *tags}, metadata={"category": category, "label": label, **metadata})


POOL = (
    *(_light(f"lighting_direction_{name}", name.replace("_", " "), "light_direction", {name}) for name in ("front", "side_left", "side_right", "back", "above", "below")),
    *(_light(f"lighting_quality_{name}", f"{name} light", "light_quality", {name}) for name in ("soft", "hard")),
    _light("lighting_temperature_warm", "warm", "colour_temperature", {"warm"}, approximate_kelvin=2700),
    _light("lighting_temperature_neutral", "neutral", "colour_temperature", {"neutral"}, approximate_kelvin=4000),
    _light("lighting_temperature_cool", "cool", "colour_temperature", {"cool"}, approximate_kelvin=6500),
    *(_light(f"lighting_setup_{name}", name.replace("_", " "), "lighting_setup", {name}, **({"preferred_contexts": ("outdoor", "sunrise_sunset")} if name == "golden_hour" else {})) for name in (
        "daylight", "golden_hour", "overcast_daylight", "window_light", "indoor_ambient", "artificial_warm",
        "artificial_cool", "mixed_lighting", "backlight", "rim_light", "dappled_light", "low_light",
        "neon_coloured", "candlelight", "firelight", "moonlight",
    )),
    *(_light(f"lighting_atmosphere_{name}", name, "atmosphere", {name}) for name in (
        "natural", "clear", "soft", "warm", "cozy", "intimate", "cool", "modern", "dramatic", "moody",
        "cinematic", "atmospheric", "dreamy",
    )),
)
