"""Small filesystem-backed store for immutable generation records."""

from __future__ import annotations

import json
from pathlib import Path

from config import OUTPUT_DIR
from engine.generation_errors import OutputWriteError
from engine.generation_records import GenerationRecord


def _directory(output_root: Path | None = None) -> Path:
    return (output_root or OUTPUT_DIR) / "records"


def save_record(record: GenerationRecord, output_root: Path | None = None) -> Path:
    path = _directory(output_root) / f"{record.record_id}.json"
    if path.exists():
        raise OutputWriteError(f"Generation record '{record.record_id}' already exists and is immutable.")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as error:
        raise OutputWriteError(f"Could not save generation record '{record.record_id}': {error}") from error
    return path


def load_record(record_id: str, output_root: Path | None = None) -> GenerationRecord:
    path = _directory(output_root) / f"{record_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Generation record '{record_id}' was not found.")
    return GenerationRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))


def list_records(output_root: Path | None = None, *, character_id: str | None = None, provider: str | None = None, mode: str | None = None) -> tuple[GenerationRecord, ...]:
    records = tuple(load_record(path.stem, output_root) for path in sorted(_directory(output_root).glob("gen_*.json"), reverse=True))
    return tuple(record for record in records if (character_id is None or record.character_id == character_id) and (provider is None or record.provider == provider) and (mode is None or record.scene_mode == mode))


def find_by_fingerprint(fingerprint: str, output_root: Path | None = None) -> tuple[GenerationRecord, ...]:
    return tuple(record for record in list_records(output_root) if record.request_fingerprint == fingerprint)
