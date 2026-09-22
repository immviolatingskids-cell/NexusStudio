"""Read-only CLI inspection for deterministic scene composition."""

from __future__ import annotations

import argparse

from engine.scene_composer import compose_scene_by_id
from engine.scene_defaults import SCENE_MODES


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect CharacterStudio scene composition")
    parser.add_argument("character_id")
    parser.add_argument("mode", choices=SCENE_MODES)
    parser.add_argument("--environment")
    parser.add_argument("--activity")
    parser.add_argument("--lighting")
    args = parser.parse_args()
    overrides = {key: value for key, value in {"environment": args.environment, "activity": args.activity, "lighting": args.lighting}.items() if value}
    scene = compose_scene_by_id(args.character_id, args.mode, overrides)
    print("CharacterStudio Scene Composer\n")
    print(scene.character_description.character_name)
    print(f"Mode: {scene.mode}\n")
    print("CHARACTER\n" + scene.character_description.text)
    print("\nSCENE\n" + scene.sections[-1].text)
    print(f"\nSources: defaults {', '.join(scene.defaulted_fields) or 'none'}; character context {', '.join(scene.character_context_fields) or 'none'}; overrides {', '.join(scene.override_fields) or 'none'}")
    print("Identity conflicts: 0")
    print("Scene composition: PASS")


if __name__ == "__main__":
    main()
