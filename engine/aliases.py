"""Small, explicit canonical-to-vocabulary terminology bridge."""

ALIASES: dict[str, frozenset[str]] = {
    "espresso": frozenset({"dark", "brown"}),
    "copper": frozenset({"auburn"}),
    "wave": frozenset({"wavy"}),
    "waves": frozenset({"wavy"}),
    "softly": frozenset({"soft"}),
    "chubby": frozenset({"plus_size"}),
    "light to olive": frozenset({"light", "olive"}),
    "dark blonde": frozenset({"blonde"}),
    "fair": frozenset({"fair_skin"}),
    "olive": frozenset({"olive_skin"}),
    "warm": frozenset({"warm_skin"}),
    "movement": frozenset({"wavy"}),
    "thick": frozenset({"thick_hair"}),
    "athletic curvy": frozenset({"soft", "athletic", "curvy"}),
}
