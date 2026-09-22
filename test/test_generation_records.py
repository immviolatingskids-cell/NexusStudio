import hashlib
from pathlib import Path

import pytest

from engine.generation_errors import GenerationError
from engine.generation_pipeline import generate_image
from engine.generation_records import RECORD_VERSION, RecordAsset, build_record
from engine.image_providers.fake import FakeImageProvider
from engine.record_store import find_by_fingerprint, list_records, load_record, save_record
from engine.reproduce import reproduce_generation


def _record() -> object:
    return build_record(character_id="luna_campbell", scene_mode="portrait", scene_overrides={"lighting": "soft daylight"}, adapter="generic", density="standard", provider="fake", model="deterministic-fake", positive_prompt="Luna prompt", negative_prompt="no watermark", assets=(RecordAsset("luna_campbell/portrait/image.txt", "text/plain", "abc"),), status="success", character_snapshot_hash="snapshot")


def test_record_serialization_round_trips_with_version():
    record = _record()
    loaded = record.from_dict(record.to_dict())

    assert loaded == record
    assert loaded.record_version == RECORD_VERSION


def test_distinct_events_share_fingerprint_for_identical_request():
    first = _record()
    second = _record()

    assert first.record_id != second.record_id
    assert first.request_fingerprint == second.request_fingerprint


def test_meaningful_input_and_prompt_changes_change_the_correct_fingerprints():
    base = _record()
    changed_override = build_record(character_id="luna_campbell", scene_mode="portrait", scene_overrides={"lighting": "neon"}, adapter="generic", density="standard", provider="fake", model="deterministic-fake", positive_prompt="Luna prompt", negative_prompt="no watermark", assets=(), status="success", character_snapshot_hash="snapshot")
    changed_density = build_record(character_id="luna_campbell", scene_mode="portrait", scene_overrides={"lighting": "soft daylight"}, adapter="generic", density="detailed", provider="fake", model="deterministic-fake", positive_prompt="Luna prompt", negative_prompt="no watermark", assets=(), status="success", character_snapshot_hash="snapshot")
    changed_prompt = build_record(character_id="luna_campbell", scene_mode="portrait", scene_overrides={"lighting": "soft daylight"}, adapter="generic", density="standard", provider="fake", model="deterministic-fake", positive_prompt="Changed prompt", negative_prompt="no watermark", assets=(), status="success", character_snapshot_hash="snapshot")

    assert changed_override.request_fingerprint != base.request_fingerprint
    assert changed_density.request_fingerprint != base.request_fingerprint
    assert changed_prompt.prompt_fingerprint != base.prompt_fingerprint


def test_store_save_load_list_find_and_immutability(tmp_path):
    record = _record()
    save_record(record, tmp_path)

    assert load_record(record.record_id, tmp_path) == record
    assert list_records(tmp_path) == (record,)
    assert find_by_fingerprint(record.request_fingerprint, tmp_path) == (record,)
    with pytest.raises(Exception, match="immutable"):
        save_record(record, tmp_path)
    with pytest.raises(FileNotFoundError, match="was not found"):
        load_record("gen_missing", tmp_path)


def test_complete_fake_record_workflow_and_dry_run_reproduction(tmp_path):
    original = generate_image("luna", "portrait", provider="fake", output_dir=tmp_path)
    record = load_record(original.record_id, tmp_path)
    asset = tmp_path / record.assets[0].relative_path

    assert asset.is_file()
    assert record.assets[0].content_hash == hashlib.sha256(asset.read_bytes()).hexdigest()
    dry_run = reproduce_generation(record.record_id, dry_run=True, output_root=tmp_path)
    assert dry_run.dry_run
    assert dry_run.provider_metadata["request"]["positive_prompt"] == record.positive_prompt
    recreated = reproduce_generation(record.record_id, output_root=tmp_path)
    recreated_record = load_record(recreated.record_id, tmp_path)
    assert recreated_record.record_id != record.record_id
    assert recreated_record.request_fingerprint == record.request_fingerprint


def test_modified_asset_no_longer_matches_recorded_integrity_hash(tmp_path):
    result = generate_image("luna", "portrait", provider="fake", output_dir=tmp_path)
    record = load_record(result.record_id, tmp_path)
    asset = tmp_path / record.assets[0].relative_path
    original_hash = record.assets[0].content_hash
    asset.write_bytes(b"changed")

    assert hashlib.sha256(asset.read_bytes()).hexdigest() != original_hash


def test_failed_attempt_record_is_safe_and_contains_no_secret(tmp_path, monkeypatch):
    import engine.generation_pipeline as pipeline

    monkeypatch.setattr(pipeline, "get_provider", lambda name: FakeImageProvider(fail=True))
    result = pipeline.generate_image("luna", "portrait", provider="fake", output_dir=tmp_path, record_failures=True)
    record = load_record(result.record_id, tmp_path)

    assert not result.success and record.status == "failed"
    assert "forced failure" in record.error
    assert "API_KEY" not in str(record.to_dict())


def test_recording_and_reproduction_do_not_mutate_record_or_result_data(tmp_path):
    result = generate_image("luna", "portrait", provider="fake", output_dir=tmp_path)
    record = load_record(result.record_id, tmp_path)
    before = (record.to_dict(), result.to_dict())

    reproduce_generation(record.record_id, dry_run=True, output_root=tmp_path)

    assert before == (record.to_dict(), result.to_dict())
