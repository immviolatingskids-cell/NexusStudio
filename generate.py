from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.loader import (
    CharacterNotFoundError,
    load_all_characters,
    load_character,
)
from engine.identity import load_identity_profile
from engine.composer import compose_negative_prompt, compose_prompt
from engine.resolver import resolve_scene
from engine.rules import CharacterValidationError
from engine.scene_models import SceneBrief
from engine.takes import new_take_id, record_take
from engine.takes import list_takes, load_take, verify_take
from engine.audit import run_audit
from engine.migrations import migrate_character_file
from engine.providers import get_provider, ProviderError
from engine.providers import GeminiProvider
from engine.prompt_models import PromptResult, PromptSection
from engine.prompt_refiner import refine_prompt
from engine.prompt_export import render_json_export, render_text_export
from engine.resolver import reroll_scene
from engine.prompts import compose_prompt_document
from config import CHARACTERS_DIR, OUTPUT_DIR, reference_image_for


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


def print_foundation_summary() -> None:
    """Print the v0.2 character-loading smoke test without resolving a scene."""
    characters = load_all_characters()
    print("CharacterStudio")
    print()
    print(f"{len(characters)} characters loaded")
    print()
    for character in characters:
        identity = character.identity
        print(character.character_id)
        print(f"  {identity.name} · {identity.age} · {identity.home}")
    print()
    print("Validation: PASS")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CharacterStudio deterministic prompt compiler and manual-generation exporter"
    )

    parser.add_argument(
        "character",
        nargs="?",
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
    parser.add_argument("--provider", choices=("fake", "gemini"), default="fake")
    parser.add_argument("--generate", action="store_true", help="Experimental legacy image-provider path; v1.1 exports prompts for manual generation.")
    parser.add_argument("--audit", action="store_true", help="Print a read-only project health report.")
    parser.add_argument("--list-takes", action="store_true")
    parser.add_argument("--inspect-take")
    parser.add_argument("--verify-take")
    parser.add_argument("--reroll-take")
    parser.add_argument("--reroll-dimension")
    parser.add_argument("--replay-take")
    parser.add_argument("--json", action="store_true", help="Emit the resolved scene and prompt document as JSON.")
    parser.add_argument("--density", choices=("compact", "standard", "detailed"), default="standard", help="Identity and scene detail level.")
    parser.add_argument("--refinement", choices=("off", "balanced", "rich"), default="off", help="Optional text-only prompt refinement mode.")
    parser.add_argument("--export", help="Write a paste-ready prompt export (.txt or .json).")
    parser.add_argument("--migrate-character", help="Preview migration of one character JSON filename or path.")
    parser.add_argument("--apply", action="store_true", help="Apply the requested migration after its preview.")

    args = parser.parse_args()

    if args.audit:
        print(json.dumps(run_audit().to_dict(), indent=2))
        return
    if args.list_takes:
        print(json.dumps(list_takes(), indent=2))
        return
    if args.inspect_take:
        print(json.dumps(load_take(args.inspect_take), indent=2))
        return
    if args.verify_take:
        print(json.dumps({"take_id": args.verify_take, "valid": verify_take(args.verify_take)}))
        return
    if args.migrate_character:
        path = Path(args.migrate_character)
        if not path.is_file():
            path = CHARACTERS_DIR / f"{args.migrate_character.removesuffix('.json')}.json"
        print(json.dumps(migrate_character_file(path, apply=args.apply), indent=2))
        return
    if not args.character:
        try:
            print_foundation_summary()
        except CharacterValidationError as exc:
            print(f"Validation: FAIL\n{exc}")
            raise SystemExit(1)
        return

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
        args.season, args.framing, args.record, args.generate, args.reroll_take, args.replay_take, args.seed != 0,
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
        profile = load_identity_profile(character.character_id)
        scene = resolve_scene(brief, profile, character.affinities)
        if args.reroll_take:
            stored = load_take(args.reroll_take)
            stored_brief = stored["scene"]["brief"]
            stored_brief["locks"] = frozenset(stored_brief.get("locks", ()))
            restored = SceneBrief(**stored_brief)
            scene = reroll_scene(resolve_scene(restored, profile, character.affinities), profile, character.affinities, dimension=args.reroll_dimension)
        if args.replay_take:
            stored = load_take(args.replay_take)
            stored_brief = stored["scene"]["brief"]
            stored_brief["locks"] = frozenset(stored_brief.get("locks", ()))
            scene = resolve_scene(SceneBrief(**stored_brief), profile, character.affinities)
        document = compose_prompt_document(scene, args.density)
        compiled_text = document.render()
        prompt_result = PromptResult(
            character_id=scene.brief.character_id,
            adapter_name="deterministic-compiler",
            positive_prompt=compiled_text,
            source_scene_mode=args.location or "custom",
            sections=tuple(PromptSection(str(index), text) for index, text in enumerate((*document.identity, *document.direction, *document.technical))),
            source_metadata={
                "density": args.density,
                "prompt_plan": {
                    "mode": args.location or "custom",
                    "image_intent": "photorealistic image prompt",
                    "style": scene.brief.image_style,
                    "wardrobe": scene.selections.get("wardrobe"),
                    "activity": scene.selections.get("activity"),
                    "pose": scene.selections.get("pose"),
                    "environment": scene.selections.get("location"),
                    "composition": scene.selections.get("framing"),
                    "lighting": scene.selections.get("lighting"),
                    "atmosphere": scene.selections.get("atmosphere"),
                    "identity_constraints": list(scene.negative_constraints),
                },
                "identity_diagnostics": document.identity_diagnostics,
            },
        )
        refined_result = refine_prompt(prompt_result, args.refinement, GeminiProvider() if args.refinement != "off" else None)
        print("Compiled prompt:")
        print(refined_result.compiled_prompt)
        if args.refinement != "off":
            print(f"\nRefined prompt ({args.refinement}):")
            print(refined_result.refined_prompt)
            for warning in refined_result.warnings:
                print(f"Refinement warning: {warning}")
        if args.export:
            target = Path(args.export)
            target.parent.mkdir(parents=True, exist_ok=True)
            serialized = render_json_export(refined_result) if target.suffix.casefold() == ".json" else render_text_export(refined_result)
            target.write_text(serialized, encoding="utf-8")
            print(f"Prompt export: {target}")
        print("Negative identity constraints:")
        print(compose_negative_prompt(scene))
        if args.json:
            print(json.dumps({"scene": scene.to_dict(), "prompt_document": document.to_dict(), "prompt_result": refined_result.to_dict()}, indent=2))
        if args.record and not args.generate:
            print(f"Take record: {record_take(scene)}")
        if args.replay_take:
            print(f"Replayed take record: {record_take(scene, parent_take_id=args.replay_take)}")
        if args.generate:
            try:
                provider = get_provider(args.provider)
                reference = reference_image_for(character.character_id)
                result = provider.generate(compose_prompt_document(scene), (reference,) if reference.is_file() else ())
                suffix = ".png" if result.mime_type == "image/png" else ".txt"
                image_dir = OUTPUT_DIR / "images"
                image_dir.mkdir(parents=True, exist_ok=True)
                take_id = new_take_id()
                output = image_dir / f"{take_id}{suffix}"
                output.write_bytes(result.image_bytes)
                print(f"Generated output: {output}")
                print(f"Take record: {record_take(scene, provider=result.provider, model=result.model, output_path=output, provider_metadata=result.metadata, take_id=take_id)}")
            except ProviderError as exc:
                print(f"Provider error: {exc}")
                raise SystemExit(2)


if __name__ == "__main__":
    main()
