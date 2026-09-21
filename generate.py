from __future__ import annotations

import argparse

from engine.loader import (
    CharacterNotFoundError,
    load_character,
)
from engine.identity import load_identity_profile
from engine.composer import compose_negative_prompt, compose_prompt
from engine.resolver import resolve_scene
from engine.rules import CharacterValidationError
from engine.scene_models import SceneBrief
from engine.takes import record_take


def print_character_summary(character) -> None:
    identity = character.identity

    print()
    print("Character loaded successfully")
    print("-----------------------------")
    print(f"ID:          {character.character_id}")
    print(f"Name:        {identity.name}")
    print(f"Age:         {identity.age}")
    print(f"Gender:      {identity.gender}")
    print(f"Nationality: {identity.nationality}")
    print(f"Home:        {identity.home}")
    print(f"Occupation:  {character.occupation.primary}")

    if character.personality:
        print(
            "Personality: "
            + ", ".join(character.personality)
        )

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Character Studio generator"
    )

    parser.add_argument(
        "character",
        help="Character filename key, e.g. ayami, luna, zara",
    )
    parser.add_argument("--activity")
    parser.add_argument("--location")
    parser.add_argument("--atmosphere")
    parser.add_argument("--wardrobe-style")
    parser.add_argument("--hair-style")
    parser.add_argument("--pose")
    parser.add_argument("--expression")
    parser.add_argument("--lighting")
    parser.add_argument("--season")
    parser.add_argument("--framing")
    parser.add_argument("--image-style", choices=("clean", "natural", "documentary"), default="natural")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--record", action="store_true", help="Save this offline preview as an immutable take record.")

    args = parser.parse_args()

    try:
        character = load_character(args.character)

    except (
        CharacterNotFoundError,
        CharacterValidationError,
    ) as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)

    print_character_summary(character)

    direction_requested = any((
        args.activity, args.location, args.atmosphere, args.wardrobe_style,
        args.hair_style, args.pose, args.expression, args.lighting,
        args.season, args.framing, args.record, args.seed != 0,
        args.image_style != "natural",
    ))
    if direction_requested:
        brief = SceneBrief(
            character_id=character.character_id,
            activity=args.activity,
            location=args.location,
            atmosphere=args.atmosphere,
            wardrobe_style=args.wardrobe_style,
            hair_style=args.hair_style,
            pose=args.pose,
            expression=args.expression,
            lighting=args.lighting,
            season=args.season,
            framing=args.framing,
            image_style=args.image_style,
            seed=args.seed,
        )
        scene = resolve_scene(brief, load_identity_profile(character.character_id), character.affinities)
        print("Prompt preview:")
        print(compose_prompt(scene))
        print("Negative identity constraints:")
        print(compose_negative_prompt(scene))
        if args.record:
            print(f"Take record: {record_take(scene)}")


if __name__ == "__main__":
    main()
