from pool_models import PoolEntry


ENVIRONMENT_CATEGORIES = ("environment_family", "location", "setting_modifier", "weather", "time_of_day")


def _environment(id: str, label: str, category: str, tags: set[str] = set(), **metadata) -> PoolEntry:
    return PoolEntry(id, label, {"environment", *tags}, metadata={"category": category, "label": label, **metadata})


POOL = (
    *(_environment(f"environment_family_{name}", name.replace("_", " "), "environment_family", {name}) for name in ("home", "workspace", "urban", "nature", "hospitality")),
    *(_environment(f"environment_location_{name}", name.replace("_", " "), "location", {name}, family=family) for family, names in {
        "home": ("bedroom", "living_room", "kitchen", "bathroom", "personal_space"),
        "workspace": ("office", "study", "creative_studio", "workshop", "library"),
        "urban": ("city_street", "rooftop", "public_transport", "alleyway"),
        "nature": ("forest", "beach", "lakeside", "mountains", "park"),
        "hospitality": ("cafe", "restaurant", "bar", "outdoor_seating", "diner"),
    }.items() for name in names),
    *(_environment(f"environment_modifier_{name}", name.replace("_", " "), "setting_modifier", {name}) for name in (
        "cozy", "warm", "relaxed", "everyday", "messy", "modern", "academic", "creative", "hands_on",
        "calm", "adventure", "casual", "retro",
    )),
    *(_environment(f"environment_weather_{name}", name, "weather", {name}) for name in ("clear", "overcast", "rain", "snow", "fog")),
    *(_environment(f"environment_time_{name}", name.replace("_", " "), "time_of_day", {name}) for name in ("day", "sunset", "evening", "night", "blue_hour")),
)
