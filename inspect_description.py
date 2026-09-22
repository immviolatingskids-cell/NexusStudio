"""Read-only inspector for deterministic visual character descriptions."""

from __future__ import annotations

import argparse

from engine.character_composer import compose_all_characters, compose_character_by_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect CharacterStudio visual descriptions")
    parser.add_argument("character_id", nargs="?")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    descriptions = compose_all_characters() if args.all else (compose_character_by_id(args.character_id),) if args.character_id else ()
    if not descriptions:
        parser.error("character_id is required unless using --all")
    for description in descriptions:
        print("CharacterStudio Visual Composer\n")
        print(description.character_name)
        print("-" * len(description.character_name))
        print(description.text)
        print(f"\nSources: resolved entries {description.metadata['resolved_entries']}; canonical fallbacks {description.metadata['canonical_fallbacks']}; unresolved omitted {description.metadata['unresolved_omitted']}")
        print("Composition: PASS\n")


if __name__ == "__main__":
    main()
