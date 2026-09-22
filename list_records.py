"""Compact filesystem-backed generation history listing."""

from __future__ import annotations

import argparse
from pathlib import Path

from engine.record_store import list_records


def main() -> None:
    parser = argparse.ArgumentParser(description="List CharacterStudio generation records")
    parser.add_argument("--character")
    parser.add_argument("--provider")
    parser.add_argument("--mode")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print("Generation History\n")
    for record in list_records(args.output, character_id=args.character, provider=args.provider, mode=args.mode):
        print(f"{record.record_id}  {record.character_id:<24} {record.scene_mode:<12} {record.provider}")
