"""Read-only command-line inspection for the reusable pool vocabulary."""

from __future__ import annotations

import argparse

from engine.loader import load_all_characters
from pools.registry import get_pool, list_pools, validate_vocabulary
from tags import registered_tags


def character_coverage() -> dict[str, dict[str, tuple[str, ...]]]:
    """Approximate vocabulary coverage; this deliberately does not select entries."""
    signals = {
        "auburn hair": (("auburn",), {"hair", "auburn"}),
        "black hair": (("black",), {"hair", "black_hair"}),
        "freckles": (("freckle",), {"freckles"}),
        "athletic build": (("athletic",), {"athletic"}),
        "curvy build": (("curvy",), {"curvy"}),
        "petite build": (("petite",), {"petite"}),
        "green_hazel eyes": (("green-hazel", "green hazel"), {"green_hazel"}),
    }
    known_tags = registered_tags()
    report: dict[str, dict[str, tuple[str, ...]]] = {}
    for character in load_all_characters():
        source = repr(character.appearance).lower()
        covered = tuple(
            label for label, (source_tokens, tags) in signals.items()
            if any(token in source for token in source_tokens) and tags <= known_tags
        )
        missing = tuple(
            label for label, (source_tokens, tags) in signals.items()
            if any(token in source for token in source_tokens) and not tags <= known_tags
        )
        report[character.character_id] = {"covered": covered, "missing": missing}
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect CharacterStudio pool vocabulary")
    parser.add_argument("pool", nargs="?", help="Optional pool name")
    parser.add_argument("--coverage", action="store_true", help="Show approximate canonical-character vocabulary coverage.")
    args = parser.parse_args()
    validate_vocabulary()
    if args.pool:
        for entry in get_pool(args.pool):
            print(entry.id)
            print(f"  {entry.text}")
            print(f"  tags: {', '.join(sorted(entry.tags))}")
        return
    if args.coverage:
        for character_id, result in character_coverage().items():
            print(character_id)
            print("  covered: " + (", ".join(result["covered"]) or "none"))
            print("  missing: " + (", ".join(result["missing"]) or "none"))
        return
    pools = list_pools()
    print("CharacterStudio Pool Registry\n")
    for name, entries in pools.items():
        print(f"{name:<10} {len(entries)} entries")
    print(f"\nTotal: {sum(map(len, pools.values()))} entries")
    print(f"Tags: {len(registered_tags())}")
    print("Validation: PASS")


if __name__ == "__main__":
    main()
