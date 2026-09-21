"""Registry for the deliberate, production-facing scene vocabulary."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from pool_models import PoolEntry
from pools import capture, environment, fashion, lighting, pose, realism


def _all_entries() -> tuple[PoolEntry, ...]:
    return (
        *environment.POOL,
        *fashion.POOL,
        *lighting.POOL,
        *pose.POOL,
        *capture.POOL,
        *realism.POOL,
    )


ENTRIES = _all_entries()
BY_ID = {entry.id: entry for entry in ENTRIES}
CURATED_MODULES = frozenset({"capture", "environment", "fashion", "lighting", "pose", "realism"})
# These existing files remain intentionally outside the v1 scene contract.
# They may be promoted later only through a vocabulary-contract change.
RESERVED_MODULES = frozenset({"build", "face", "hair", "photography", "skin"})

if len(BY_ID) != len(ENTRIES):
    raise RuntimeError("Scene pool IDs must be unique.")


def entries_for(category: str) -> tuple[PoolEntry, ...]:
    return tuple(entry for entry in ENTRIES if entry.metadata.get("category") == category)


def find(value: str | None, *, category: str | None = None) -> PoolEntry | None:
    """Resolve a stable public pool ID; internal callers must use this."""
    if not value:
        return None
    needle = value.strip().lower().replace("-", "_").replace(" ", "_")
    candidates: Iterable[PoolEntry] = ENTRIES
    if category:
        candidates = (entry for entry in candidates if entry.metadata.get("category") == category)
    matches = [entry for entry in candidates if entry.id == needle]
    return matches[0] if len(matches) == 1 else None


def find_display(value: str | None, *, category: str | None = None) -> PoolEntry | None:
    """Compatibility helper for a user-facing CLI value, never persisted as identity."""
    exact = find(value, category=category)
    if exact:
        return exact
    if not value:
        return None
    needle = value.strip().lower().replace("-", "_").replace(" ", "_")
    candidates = entries_for(category) if category else ENTRIES
    matches = [entry for entry in candidates if entry.text.lower().replace(" ", "_") == needle or needle in entry.tags]
    return matches[0] if len(matches) == 1 else None


def registry_issues() -> tuple[str, ...]:
    issues: list[str] = []
    for entry in ENTRIES:
        if not entry.id or not entry.text:
            issues.append("Pool entries need non-empty IDs and labels.")
        if not entry.metadata.get("category"):
            issues.append(f"Pool entry '{entry.id}' has no category.")
    labels: dict[tuple[str, str], int] = {}
    for entry in ENTRIES:
        key = (str(entry.metadata.get("category")), entry.text.casefold())
        labels[key] = labels.get(key, 0) + 1
    issues.extend(f"Ambiguous display label '{label}' in category '{category}'." for (category, label), count in labels.items() if count > 1)
    pool_directory = Path(__file__).parent
    known = CURATED_MODULES | RESERVED_MODULES | {"__init__", "registry"}
    actual = {path.stem for path in pool_directory.glob("*.py")}
    issues.extend(f"Orphaned pool module '{module}.py'." for module in sorted(actual - known))
    return tuple(issues)
