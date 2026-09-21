from pool_models import PoolEntry


def _fashion(id: str, label: str, category: str, tags: set[str] = set()) -> PoolEntry:
    return PoolEntry(id, label, {"fashion", *tags}, metadata={"category": category, "label": label})


# Baseline clothing taxonomy from the approved Clothing & Style Reference Guide.
# Garment identity is separate from fabric, fit, colour and style.
POOL = (
    # Style families
    *(_fashion(f"fashion_style_{name}", name.replace("_", " "), "style", {name}) for name in (
        "casual", "athleisure", "smart_casual", "professional", "formal_evening",
        "loungewear", "seasonal", "alternative", "swimwear", "costume_themed",
    )),
    # Garment categories
    *(_fashion(f"fashion_garment_category_{name}", name.replace("_", " "), "garment_category", {name}) for name in (
        "top", "bottom", "outerwear", "dress", "footwear", "accessory",
    )),
    # Tops, bottoms, layers, dresses, footwear and accessories
    *(_fashion(f"fashion_garment_{name}", name.replace("_", " "), "garment", {category}) for category, names in {
        "top": ("tank", "t_shirt", "blouse", "sweater", "hoodie"),
        "bottom": ("jeans", "shorts", "skirt", "trousers", "leggings"),
        "outerwear": ("jacket", "coat", "cardigan", "blazer"),
        "dress": ("dress", "bodycon_dress", "sundress", "formal_dress", "maxi_dress"),
        "footwear": ("sneakers", "boots", "heels", "sandals", "slippers"),
        "accessory": (),
    }.items() for name in names),
    # Fabrics
    *(_fashion(f"fashion_fabric_{name}", name, "fabric", {name}) for name in (
        "cotton", "denim", "linen", "knit", "leather", "wool", "silk", "satin",
        "chiffon", "fleece", "mesh", "corduroy",
    )),
    # Fabric/finish texture descriptors
    *(_fashion(f"fashion_texture_{name}", name, "texture", {name}) for name in (
        "matte", "durable", "light", "soft", "smooth", "warm", "reflective", "shiny",
        "sheer", "cozy", "see_through", "ribbed",
    )),
    # Baseline fit and silhouette vocabulary
    *(_fashion(f"fashion_fit_{name}", name, "fit", {name}) for name in (
        "relaxed", "fitted", "oversized", "tailored", "flowing", "layered", "soft", "structured",
    )),
    # Reference colours
    *(_fashion(f"fashion_colour_{name}", name.replace("_", " "), "colour", {name}) for name in (
        "black", "white", "grey", "beige", "brown", "olive", "khaki", "rust", "mustard", "taupe",
        "blush", "mint", "lavender", "baby_blue", "cream", "red", "royal_blue", "emerald", "purple", "pink",
    )),
    # Palette families and monochrome examples
    *(_fashion(f"fashion_palette_{name}", name.replace("_", " "), "palette", {name}) for name in (
        "neutrals", "earth_tones", "pastels", "bold_colours", "monochrome",
    )),
    *(_fashion(f"fashion_palette_all_{name}", f"all {name.replace('_', ' ')}", "palette", {"monochrome", name}) for name in (
        "black", "white", "beige", "grey", "denim",
    )),
    # Accessory dimension entries are deliberately independent of garment identity.
    *(_fashion(f"fashion_accessory_{name}", name, "accessory", {name}) for name in (
        "bag", "belt", "scarf", "hat", "jewellery",
    )),
    # Existing compatibility entries.
    _fashion("fashion_casual", "casual clothing", "style", {"casual"}),
    _fashion("fashion_streetwear", "modern streetwear", "style", {"streetwear"}),
    _fashion("fashion_minimalist", "minimalist styling", "style", {"minimalist"}),
    _fashion("fashion_workwear", "practical workwear", "style", {"workwear"}),
    _fashion("fashion_smart_casual", "smart casual outfit", "style", {"smart_casual", "casual"}),
    _fashion("fashion_cozy", "cozy layered clothing", "style", {"cozy"}),
)
