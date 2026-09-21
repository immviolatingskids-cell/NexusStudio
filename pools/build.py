from pool_models import PoolEntry


def _body(id: str, label: str, category: str, tags: set[str] = set()) -> PoolEntry:
    return PoolEntry(id, label, {"body", *tags}, metadata={"category": category, "label": label})


# Atomic descriptors transcribed from the approved Body & Build Reference Guide.
# Categories are intentionally composable; no body type is a rigid preset.
POOL = (
    # Primary body families
    _body("body_type_very_slim", "very slim", "body_type", {"very_slim"}),
    _body("body_type_slim", "slim", "body_type", {"slim"}),
    _body("body_type_athletic", "athletic", "body_type", {"athletic"}),
    _body("body_type_average", "average", "body_type", {"average"}),
    _body("body_type_curvy", "curvy", "body_type", {"curvy"}),
    _body("body_type_plus_size", "plus size", "body_type", {"plus_size"}),
    _body("body_type_bbw", "bbw", "body_type", {"bbw"}),
    # Reference descriptors, kept independent from body type
    _body("body_shape_minimal_curves", "minimal curves", "body_shape", {"minimal_curves"}),
    _body("body_shape_subtle_curves", "subtle curves", "body_shape", {"subtle_curves"}),
    _body("body_shape_balanced", "balanced shape", "body_shape", {"balanced_shape"}),
    _body("body_shape_defined_curves", "defined curves", "body_shape", {"defined_curves"}),
    _body("body_shape_wider_hips", "wider hips", "body_shape", {"wider_hips"}),
    _body("body_shape_fuller_overall", "fuller overall shape", "body_shape", {"fuller_shape"}),
    _body("body_shape_larger_bust_hips", "larger bust and hips", "body_shape", {"larger_bust_hips"}),
    _body("body_shape_big_natural", "big, beautiful, natural shape", "body_shape", {"fuller_shape", "natural"}),
    _body("body_frame_smaller", "smaller frame", "frame", {"smaller_frame"}),
    _body("body_frame_average", "average frame", "frame", {"average_frame"}),
    _body("body_frame_larger", "larger frame", "frame", {"larger_frame"}),
    _body("body_muscle_visible", "visible muscle tone", "muscle_tone", {"visible_muscle"}),
    _body("body_muscle_firm", "firm shape", "muscle_tone", {"firm_muscle"}),
    _body("body_muscle_light", "light muscle tone", "muscle_tone", {"light_muscle"}),
    _body("body_muscle_soft_definition", "soft definition", "muscle_tone", {"soft_definition"}),
    _body("body_softness_low_fat", "low body fat", "softness", {"low_body_fat"}),
    _body("body_softness_less_tissue", "less soft tissue", "softness", {"less_soft_tissue"}),
    _body("body_softness_soft_features", "soft features", "softness", {"soft_features"}),
    _body("body_softness_natural_folds", "natural body folds", "softness", {"natural_folds"}),
    _body("body_proportions_lean", "lean proportions", "proportions", {"lean_proportions"}),
    _body("body_proportions_athletic", "athletic proportions", "proportions", {"athletic_proportions"}),
    _body("body_proportions_balanced", "natural, balanced proportions", "proportions", {"balanced_proportions"}),
    _body("body_proportions_strong_upper", "strong upper body", "proportions", {"strong_upper_body"}),
    _body("body_proportions_smaller_waist", "smaller waist", "proportions", {"smaller_waist"}),
    _body("body_proportions_larger_hips", "larger hips", "proportions", {"larger_hips"}),
    # Localized details can coexist with any body type.
    _body("body_detail_waist_slim", "slim waist", "body_detail", {"slim_waist"}),
    _body("body_detail_waist_defined", "defined waist", "body_detail", {"defined_waist"}),
    _body("body_detail_stomach_natural", "natural stomach", "body_detail", {"natural_stomach"}),
    _body("body_detail_stomach_plus_size", "plus-size stomach", "body_detail", {"plus_size_stomach"}),
    _body("body_detail_arms_toned", "toned arms", "body_detail", {"toned_arms"}),
    _body("body_detail_arms_soft", "soft arms", "body_detail", {"soft_arms"}),
    _body("body_detail_thighs_athletic", "athletic thighs", "body_detail", {"athletic_thighs"}),
    _body("body_detail_thighs_curvy", "curvy thighs", "body_detail", {"curvy_thighs"}),
    _body("body_detail_natural_folds", "natural skin folds", "body_detail", {"natural_folds"}),
    # Compatibility entries for the existing character resolver.
    PoolEntry("build_petite", "petite build", {"petite", "soft"}, metadata={"category": "body_type", "label": "petite build", "source": "legacy compatibility"}),
    PoolEntry("build_soft_athletic", "soft athletic build", {"soft", "athletic"}, metadata={"category": "body_type", "label": "soft athletic build", "source": "legacy compatibility"}),
    PoolEntry("build_curvy", "naturally curvy build", {"curvy", "soft"}, metadata={"category": "body_type", "label": "naturally curvy build", "source": "legacy compatibility"}),
    PoolEntry("build_tall_sturdy", "tall sturdy build", {"tall", "sturdy"}, metadata={"category": "body_type", "label": "tall sturdy build", "source": "legacy compatibility"}),
    PoolEntry("build_slender", "slender build", {"slender", "athletic"}, metadata={"category": "body_type", "label": "slender build", "source": "legacy compatibility"}),
)
