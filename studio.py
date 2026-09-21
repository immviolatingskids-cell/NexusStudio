"""Friendly, guided CLI for directing NexusStudio takes.

This layer only collects direction and calls the canonical engine.  It does
not contain identity, resolver, or prompt logic of its own.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from config import OUTPUT_DIR, REFERENCE_IMAGES_DIR
from engine.composer import compose_negative_prompt, compose_prompt
from engine.identity import load_identity_profile
from engine.loader import list_character_ids, load_character
from engine.prompts import compose_prompt_document
from engine.providers import ProviderError, get_provider
from engine.resolver import reroll_scene, resolve_scene
from engine.scene_models import ResolvedScene, SceneBrief
from engine.takes import list_takes, record_take


def _optional(prompt: str, input_fn=input) -> str | None:
    value = input_fn(prompt).strip()
    return value or None


def _character_choices() -> str:
    return ", ".join(list_character_ids())


def build_scene(character_key: str, idea: str | None = None, **direction: object) -> tuple[object, object, ResolvedScene]:
    """Build a take through the same scene contract used by `generate.py`."""
    character = load_character(character_key)
    profile = load_identity_profile(character.character_id)
    brief = SceneBrief(character_id=character.character_id, activity=idea or None, **direction)
    return character, profile, resolve_scene(brief, profile, character.affinities)


def print_take(scene: ResolvedScene, output_fn=print) -> None:
    output_fn("\nYour directed take")
    output_fn("=" * 18)
    for dimension, label in scene.selections.items():
        if dimension in scene.selection_ids:
            output_fn(f"{dimension.title()}: {label} ({scene.selection_ids[dimension]})")
        else:
            output_fn(f"{dimension.title()}: {label}")
    output_fn("\nPrompt preview:\n" + compose_prompt(scene))
    output_fn("\nIdentity protections:\n" + compose_negative_prompt(scene))


def save_take(scene: ResolvedScene, *, provider_name: str | None = None, character_key: str | None = None) -> Path:
    if provider_name is None:
        return record_take(scene)
    provider = get_provider(provider_name)
    reference = REFERENCE_IMAGES_DIR / f"{character_key}.png" if character_key else None
    result = provider.generate(compose_prompt_document(scene), (reference,) if reference and reference.is_file() else ())
    suffix = ".png" if result.mime_type == "image/png" else ".txt"
    target = OUTPUT_DIR / "images" / f"{scene.brief.character_id}-{scene.brief.seed}{suffix}"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(result.image_bytes)
    return record_take(scene, provider=result.provider, model=result.model, output_path=target, provider_metadata=result.metadata)


def guided_session(input_fn=input, output_fn=print) -> None:
    output_fn("Welcome to NexusStudio. You are directing a take, not writing a prompt.")
    output_fn(f"Available characters: {_character_choices()}")
    while True:
        key = _optional("Choose a character: ", input_fn)
        if key in list_character_ids():
            break
        output_fn("Please choose one of the listed character keys.")
    idea = _optional("What is happening? (for example, 'getting ready for a concert'): ", input_fn)
    direction = {
        "location": _optional("Where? Leave blank for a suggested location: ", input_fn),
        "wardrobe_style": _optional("What should they wear? Leave blank for a suggested style: ", input_fn),
        "atmosphere": _optional("What atmosphere? Leave blank for a suggestion: ", input_fn),
        "lighting": _optional("What lighting? Leave blank for a suggestion: ", input_fn),
        "hair_style": _optional("Any temporary hair styling? Leave blank to keep it open: ", input_fn),
        "season": _optional("Season or time of year? Leave blank to keep it open: ", input_fn),
    }
    character, profile, scene = build_scene(key, idea, **direction)
    while True:
        print_take(scene, output_fn)
        action = _optional("[S]ave preview, [R]eroll, [L]ock a detail, [G]enerate with fake provider, or [Q]uit: ", input_fn)
        action = (action or "q").lower()
        if action == "s":
            output_fn(f"Saved: {save_take(scene)}")
        elif action == "g":
            output_fn(f"Generated and saved: {save_take(scene, provider_name='fake', character_key=key)}")
        elif action == "l":
            dimension = _optional("Lock which detail? (location, wardrobe, pose, lighting, atmosphere, framing): ", input_fn)
            if dimension not in scene.selection_ids:
                output_fn("That detail cannot be locked.")
                continue
            locks = scene.brief.locks | frozenset({dimension})
            locked = {name: scene.selection_ids[name] for name in locks}
            scene = resolve_scene(replace(scene.brief, locks=locks, locked_selections=locked), profile, character.affinities)
        elif action == "r":
            dimension = _optional("Reroll one detail, or leave blank to reroll all unlocked details: ", input_fn)
            try:
                scene = reroll_scene(scene, profile, character.affinities, dimension=dimension)
            except ValueError as exc:
                output_fn(str(exc))
        elif action == "q":
            return
        else:
            output_fn("Choose S, R, L, G, or Q.")


def main() -> None:
    parser = argparse.ArgumentParser(description="NexusStudio's friendly directing CLI")
    subcommands = parser.add_subparsers(dest="command")
    direct = subcommands.add_parser("direct", help="Create a take from a character and natural direction.")
    direct.add_argument("character")
    direct.add_argument("idea", nargs="?", default="")
    direct.add_argument("--location")
    direct.add_argument("--style", dest="wardrobe_style")
    direct.add_argument("--mood", dest="atmosphere")
    direct.add_argument("--lighting")
    direct.add_argument("--hair", dest="hair_style")
    direct.add_argument("--season")
    direct.add_argument("--seed", type=int, default=0)
    direct.add_argument("--save", action="store_true")
    direct.add_argument("--generate", choices=("fake", "gemini"))
    subcommands.add_parser("characters", help="Show the available cast.")
    subcommands.add_parser("takes", help="Show saved take history.")
    args = parser.parse_args()

    if args.command is None:
        guided_session()
        return
    if args.command == "characters":
        for key in list_character_ids():
            character = load_character(key)
            print(f"{key}: {character.identity.name} — {character.occupation.primary}")
        return
    if args.command == "takes":
        for take in list_takes():
            print(f"{take['take_id']}  {take['character_id']}  {take['provider']}  {take['created_at']}")
        return
    character, _, scene = build_scene(
        args.character, args.idea, location=args.location, wardrobe_style=args.wardrobe_style,
        atmosphere=args.atmosphere, lighting=args.lighting, hair_style=args.hair_style,
        season=args.season, seed=args.seed,
    )
    print_take(scene)
    try:
        if args.generate:
            print(f"Generated and saved: {save_take(scene, provider_name=args.generate, character_key=args.character)}")
        elif args.save:
            print(f"Saved: {save_take(scene)}")
    except ProviderError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
