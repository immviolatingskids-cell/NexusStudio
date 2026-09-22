"""CLI for one deterministic or live CharacterStudio image generation."""

from __future__ import annotations

import argparse

from engine.adapters.base import DENSITIES
from engine.adapter_registry import list_adapters
from engine.generation_errors import ConfigurationError, GenerationError, ProviderUnavailableError
from engine.generation_pipeline import generate_image
from engine.provider_registry import list_providers
from engine.scene_defaults import SCENE_MODES


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one CharacterStudio image")
    parser.add_argument("character_id")
    parser.add_argument("mode", choices=SCENE_MODES)
    parser.add_argument("--provider", choices=list_providers(), default="fake")
    parser.add_argument("--adapter", choices=list_adapters())
    parser.add_argument("--density", choices=DENSITIES, default="standard")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        result = generate_image(args.character_id, args.mode, args.provider, args.adapter, args.density, dry_run=args.dry_run, output_dir=args.output)
    except (ConfigurationError, ProviderUnavailableError, GenerationError) as error:
        print("CharacterStudio Image Generation\n\nGeneration: FAILED\nReason: " + str(error))
        return 1
    print("CharacterStudio Image Generation\n")
    print(f"Character: {result.character_id}\nMode: {result.scene_mode}\nProvider: {result.provider}\nAdapter: {result.adapter}\nDensity: {args.density}\n")
    print("Prompt: PASS\nProvider configuration: PASS\nGeneration: " + ("DRY RUN" if result.dry_run else "PASS"))
    if result.assets:
        print("\nOutput:\n" + result.assets[0].file_path)
    if result.warnings:
        print("\nWarnings:\n" + "\n".join(result.warnings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
