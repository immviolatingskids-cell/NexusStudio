"""Controlled vocabulary for reusable pool tags.

The named constants cover the first public vocabulary concepts.  The registry
also records tags already present in the established pools, so validation can
protect the contract without rewriting later, resolver-owned vocabulary.
"""

from __future__ import annotations

import re
from collections.abc import Iterable


HAIR = "hair"
AUBURN = "auburn"
BLACK_HAIR = "black_hair"
BLONDE = "blonde"
FRECKLES = "freckles"
FAIR_SKIN = "fair_skin"
OLIVE_SKIN = "olive_skin"
ATHLETIC = "athletic"
CURVY = "curvy"
PETITE = "petite"
STREETWEAR = "streetwear"
CASUAL = "casual"
FORMAL = "formal"
WARM_LIGHT = "warm_light"
STUDIO_LIGHT = "studio_light"

_TAG_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_registered_tags: set[str] = {
    HAIR, AUBURN, BLACK_HAIR, BLONDE, FRECKLES, FAIR_SKIN, OLIVE_SKIN,
    ATHLETIC, CURVY, PETITE, STREETWEAR, CASUAL, FORMAL, WARM_LIGHT,
    STUDIO_LIGHT,
}


def is_valid_tag_name(tag: str) -> bool:
    return bool(_TAG_PATTERN.fullmatch(tag))


def register_tags(tags: Iterable[str]) -> None:
    """Register existing vocabulary tags after enforcing the naming contract."""
    tags = tuple(tags)
    invalid = sorted(tag for tag in tags if not isinstance(tag, str) or not is_valid_tag_name(tag))
    if invalid:
        raise ValueError(f"Invalid pool tag name(s): {', '.join(map(str, invalid))}")
    _registered_tags.update(tags)


def registered_tags() -> frozenset[str]:
    return frozenset(_registered_tags)
