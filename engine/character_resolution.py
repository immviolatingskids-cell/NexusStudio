"""Pure deterministic bridge from validated canonical characters to pool entries."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from engine.normalization import normalize_traits
from engine.resolver_models import ResolutionResult, ResolvedEntry, UnresolvedTrait
from pool_models import PoolEntry
from pools.registry import get_pool


SUPPORTED_PATHS = {
    "appearance.hair.color": ("hair", "colour"), "appearance.hair.length": ("hair", "length"),
    "appearance.hair.density": ("hair", "density"), "appearance.hair.texture": ("hair", "texture"),
    "appearance.hair.framing": ("hair", "detail"), "appearance.skin.tone": ("skin", "complexion"),
    "appearance.skin.texture": ("skin", "skin_detail"), "appearance.skin.features": ("skin", "skin_detail"),
    "appearance.body.build": ("build", "body_type"), "appearance.body.proportions": ("build", "proportions"),
    "appearance.body.physical_features": ("build", "body_detail"), "appearance.face.shape": ("face", "face_shape"),
    "appearance.face.jaw": ("face", "face_shape"), "appearance.face.cheekbones": ("face", "distinguishing_feature"),
    "appearance.face.nose.bridge": ("face", "nose_shape"), "appearance.face.nose.tip": ("face", "nose_shape"),
    "appearance.face.nose.width": ("face", "nose_shape"), "appearance.face.lips.shape": ("face", "lip_shape"),
    "appearance.face.lips.fullness": ("face", "lip_fullness"), "appearance.face.brows.shape": ("face", "brow_shape"),
    "appearance.face.brows.density": ("face", "brow_density"), "appearance.face.brows.color": ("face", "brow_density"),
    "appearance.eyes.color": ("face", "eye_colour"), "appearance.eyes.shape": ("face", "eye_shape"),
}


_MISSING = object()


def _value_at(data: dict[str, Any], path: str) -> Any:
    value: Any = data
    for part in path.removeprefix("appearance.").split("."):
        if not isinstance(value, dict) or part not in value:
            return _MISSING
        value = value[part]
    return value


def _best_matches(entries: Iterable[PoolEntry], tokens: frozenset[str], category: str) -> tuple[PoolEntry, ...]:
    base_tags = {"hair", "face", "body", "fashion"}
    candidates: list[tuple[int, int, str, frozenset[str], PoolEntry]] = []
    for entry in entries:
        if entry.metadata.get("category") != category:
            continue
        meaningful = entry.tags - base_tags
        overlap = meaningful & tokens
        if overlap:
            candidates.append((len(overlap), len(meaningful), entry.id, frozenset(overlap), entry))
    if not candidates:
        return ()
    # More matching concepts wins, then the more specific entry, then stable ID.
    selected: list[PoolEntry] = []
    covered: set[str] = set()
    for _, _, _, overlap, entry in sorted(candidates, key=lambda item: (-item[0], -item[1], item[2])):
        if overlap - covered:
            selected.append(entry)
            covered.update(overlap)
    return tuple(selected)


def resolve_character(character) -> ResolutionResult:
    """Resolve supported appearance values without mutating character or pools."""
    appearance = character.appearance
    resolved: list[ResolvedEntry] = []
    unresolved: list[UnresolvedTrait] = []
    used_ids: set[str] = set()
    for path, (pool_name, category) in SUPPORTED_PATHS.items():
        value = _value_at(appearance, path)
        if value is _MISSING:
            continue
        values = value if isinstance(value, list) else (value,)
        for raw_value in values:
            if not isinstance(raw_value, str):
                continue
            entries = _best_matches(get_pool(pool_name), normalize_traits(raw_value), category)
            if not entries:
                unresolved.append(UnresolvedTrait(path, raw_value, "no matching vocabulary entry"))
            else:
                for entry in entries:
                    if entry.id not in used_ids:
                        used_ids.add(entry.id)
                        resolved.append(ResolvedEntry(path, raw_value, entry, "token_match"))
    skipped = (
        "identity", "occupation", "hobbies", "interests", "personality", "affinities",
        "appearance.body.height", "appearance.eyes.size", "appearance.distinguishing_features",
        "appearance.physicality", "appearance.common_accessories",
    )
    return ResolutionResult(character.character_id, tuple(resolved), tuple(unresolved), skipped)


def resolution_diagnostics(results: Iterable[ResolutionResult]) -> dict[str, Any]:
    results = tuple(results)
    unresolved: dict[str, int] = {}
    for result in results:
        for trait in result.unresolved_traits:
            unresolved[trait.source_path] = unresolved.get(trait.source_path, 0) + 1
    resolved_count = sum(len(result.resolved_entries) for result in results)
    unresolved_count = sum(len(result.unresolved_traits) for result in results)
    total = resolved_count + unresolved_count
    return {"characters": len(results), "resolved_traits": resolved_count, "unresolved_traits": unresolved_count, "unsupported_traits": sum(len(result.skipped_traits) for result in results), "coverage_percent": round(100 * resolved_count / total) if total else 100, "common_gaps": tuple(sorted(unresolved.items(), key=lambda item: (-item[1], item[0])))}
