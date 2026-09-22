"""Read-only inspection for the canonical-character vocabulary bridge."""

from __future__ import annotations

import argparse

from engine.character_resolution import resolution_diagnostics
from engine.resolver import resolve_all_characters, resolve_character_by_id


def print_result(result) -> None:
    print("CharacterStudio Resolver\n")
    print(result.character_id)
    for item in result.resolved_entries:
        print(f"[ok] {item.source_path}: {item.entry.id} - {item.entry.text}")
    if result.unresolved_traits:
        print("\nUNRESOLVED")
        for trait in result.unresolved_traits:
            print(f"- {trait.source_path}: {trait.source_value} ({trait.reason})")
    print(f"\nResolved: {len(result.resolved_entries)}")
    print(f"Unresolved: {len(result.unresolved_traits)}")
    print("Resolution: PASS")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect canonical character vocabulary resolution")
    parser.add_argument("character_id", nargs="?")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if args.all:
        results = resolve_all_characters()
        diagnostics = resolution_diagnostics(results)
        print(f"Characters: {diagnostics['characters']}")
        print(f"Resolved traits: {diagnostics['resolved_traits']}")
        print(f"Unresolved traits: {diagnostics['unresolved_traits']}")
        print(f"Unsupported fields: {diagnostics['unsupported_traits']}")
        print(f"Vocabulary coverage: {diagnostics['coverage_percent']}%")
        print("\nCommon vocabulary gaps:")
        for path, count in diagnostics["common_gaps"]:
            print(f"{path}: {count}")
        return
    if not args.character_id:
        parser.error("character_id is required unless using --all")
    print_result(resolve_character_by_id(args.character_id))


if __name__ == "__main__":
    main()
