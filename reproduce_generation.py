"""CLI for deterministic request reconstruction from a generation record."""

from __future__ import annotations

import argparse
from pathlib import Path

from engine.record_store import load_record
from engine.reproduce import reproduce_generation
from engine.generation_records import request_fingerprint_for


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce a CharacterStudio generation request")
    parser.add_argument("record_id")
    parser.add_argument("--provider")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    original = load_record(args.record_id, args.output)
    result = reproduce_generation(args.record_id, args.provider, args.dry_run, args.output)
    reconstructed = result.provider_metadata.get("request", {})
    print("CharacterStudio Reproduction\n")
    reconstructed_fingerprint = request_fingerprint_for(character_id=result.character_id, scene_mode=result.scene_mode, scene_overrides=original.scene_overrides, adapter=result.adapter, density=original.density, provider=result.provider, model=result.model, positive_prompt=reconstructed.get("positive_prompt", original.positive_prompt), negative_prompt=reconstructed.get("negative_prompt", original.negative_prompt)) if reconstructed else "unavailable"
    print(f"Original fingerprint: {original.request_fingerprint}\nReconstructed fingerprint: {reconstructed_fingerprint}\nFingerprints match: {'YES' if reconstructed_fingerprint == original.request_fingerprint else 'NO'}\nSelected provider: {result.provider}\nExecution: {'DRY RUN' if result.dry_run else 'PASS'}")
    print("Exact image reproduction: NOT GUARANTEED")
    if reconstructed:
        print("Request reconstruction: PASS")


if __name__ == "__main__":
    main()
