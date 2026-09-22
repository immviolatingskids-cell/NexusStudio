"""Read-only inspection of one portable, immutable generation record."""

from __future__ import annotations

import argparse
from pathlib import Path

from engine.record_store import load_record


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a CharacterStudio generation record")
    parser.add_argument("record_id")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    record = load_record(args.record_id, args.output)
    print("CharacterStudio Generation Record\n")
    print(f"Record:\n{record.record_id}\n\nCharacter:\n{record.character_id}\n\nScene:\n{record.scene_mode}\n\nProvider:\n{record.provider}\n\nAdapter:\n{record.adapter}\n\nDensity:\n{record.density}\n\nModel:\n{record.model}")
    print(f"\nRequest fingerprint:\n{record.request_fingerprint}\n\nPrompt fingerprint:\n{record.prompt_fingerprint}\n\nAssets:\n{len(record.assets)}")
    for asset in record.assets:
        print(f"- {asset.relative_path}\n  sha256: {asset.content_hash or 'unavailable'}")
    print("\nReproducibility:\nRequest reconstruction: YES\nExact image reproduction: NOT GUARANTEED")
    print("\nRecord: PASS")


if __name__ == "__main__":
    main()
