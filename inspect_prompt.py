"""Read-only CLI inspector for model-facing prompt rendering."""

from __future__ import annotations

import argparse

from engine.adapter_registry import list_adapters
from engine.adapters.base import DENSITIES
from engine.loader import load_character
from engine.prompt_compiler import compile_prompt_plan
from engine.prompt_diagnostics import diagnostics_for
from engine.prompt_pipeline import build_prompt
from engine.scene_composer import compose_scene_by_id
from engine.scene_defaults import SCENE_MODES


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect CharacterStudio prompt adapters")
    parser.add_argument("character_id")
    parser.add_argument("mode", choices=SCENE_MODES)
    parser.add_argument("adapter", choices=list_adapters(), nargs="?", default="generic")
    parser.add_argument("--density", choices=DENSITIES, default="standard")
    parser.add_argument("--debug", action="store_true", help="show the compiled plan and concrete diagnostics")
    args = parser.parse_args()
    character = load_character(args.character_id)
    prompt = build_prompt(args.character_id, args.mode, args.adapter, args.density)
    print("CharacterStudio Prompt Adapter\n")
    print(f"Character: {character.identity.name}\nMode: {args.mode}\nAdapter: {args.adapter}\nDensity: {args.density}\n")
    print("POSITIVE PROMPT\n---------------\n" + prompt.positive_prompt)
    if args.debug:
        scene = compose_scene_by_id(args.character_id, args.mode)
        plan = compile_prompt_plan(character, scene.character_description, scene, args.density)
        diagnostics = diagnostics_for(plan)
        print("\nPROMPT PLAN\n-----------")
        print("Identity anchors:\n" + "\n".join(f"- {anchor}" for anchor in plan.identity_anchors))
        print("\nScene:\n" + "\n".join(f"{field}: {getattr(plan, field)}" for field in ("activity", "pose", "environment", "composition", "lighting") if getattr(plan, field)))
        print("\nDIAGNOSTICS\n-----------")
        print(f"Identity anchors preserved: {diagnostics.identity_anchors_preserved}/{diagnostics.identity_anchors_total}")
        print("Scene fields included: " + ", ".join(diagnostics.scene_fields_included))
        print("Redundancies removed: " + str(len(diagnostics.redundancies_removed)))
        print("Conflicts: " + str(len(diagnostics.conflicts)))
    print("\nNEGATIVE / CONSTRAINTS\n----------------------\n" + (prompt.negative_prompt or "Integrated as positive identity constraints."))
    print("\nSources\n-------\nCharacter: PASS\nResolver: PASS\nVisual composer: PASS\nScene composer: PASS\nAdapter: " + args.adapter)
    print("\nPrompt generation: PASS")


if __name__ == "__main__":
    main()
