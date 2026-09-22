"""Deterministic normalization of canonical descriptive text."""

from __future__ import annotations

import re

from engine.aliases import ALIASES


def normalize_traits(value: str) -> frozenset[str]:
    """Return normalized words plus explicit alias tokens, without changing data."""
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    tokens = set(normalized.split())
    words = normalized.split()
    tokens.update(f"{left}_{right}" for left, right in zip(words, words[1:]))
    for phrase, aliases in ALIASES.items():
        if phrase in normalized:
            tokens.update(aliases)
    return frozenset(tokens)
