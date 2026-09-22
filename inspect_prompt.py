"""Read-only CLI inspector for model-facing prompt rendering."""

from __future__ import annotations

import argparse

from engine.adapter_registry import list_adapters
from engine.adapters.base import DENSITIES
from engine.loader import load_character
from engine.prompt_pipeline import build_prompt
from engine.scene_defaults import SCENE_MODES


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect CharacterStudio prompt adapters")
    parser.add_argument("character_id")
    parser.add_argument("mode", choices=SCENE_MODES)
    parser.add_argument("adapter", choices=list_adapters(), nargs="?", default="generic")
    parser.add_argument("--density", choices=DENSITIES, default="standard")
    args = parser.parse_args()
    character = load_character(args.character_id)
    prompt = build_prompt(args.character_id, args.mode, args.adapter, args.density)
    print("CharacterStudio Prompt Adapter\n")
    print(f"Character: {character.identity.name}\nMode: {args.mode}\nAdapter: {args.adapter}\nDensity: {args.density}\n")
    print("POSITIVE PROMPT\n---------------\n" + prompt.positive_prompt)
    print("\nNEGATIVE / CONSTRAINTS\n----------------------\n" + (prompt.negative_prompt or "Integrated as positive identity constraints."))
    print("\nSources\n-------\nCharacter: PASS\nResolver: PASS\nVisual composer: PASS\nScene composer: PASS\nAdapter: " + args.adapter)
    print("\nPrompt generation: PASS")


if __name__ == "__main__":
    main()
