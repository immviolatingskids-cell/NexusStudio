from studio import build_scene, guided_session, save_take
from engine import takes


def test_friendly_direct_flow_reuses_canonical_scene_contract():
    character, _, scene = build_scene("luna", "at a concert", location="bar", wardrobe_style="streetwear", seed=4)

    assert character.character_id == scene.brief.character_id
    assert scene.selections["location"] == "bar"
    assert scene.selection_ids["wardrobe"] == "fashion_streetwear"


def test_friendly_fake_generation_records_immutable_take(tmp_path, monkeypatch):
    _, _, scene = build_scene("luna", "at a concert", seed=4)
    monkeypatch.setattr(takes, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr("studio.OUTPUT_DIR", tmp_path)

    record = save_take(scene, provider_name="fake", character_key="luna")

    assert record.is_file()
    assert takes.verify_take(record.stem)


def test_guided_session_collects_direction_without_a_second_resolver():
    responses = iter(("luna", "at a concert", "bar", "streetwear", "", "", "", "", "q"))
    output: list[str] = []

    guided_session(input_fn=lambda _: next(responses), output_fn=output.append)

    assert any("Your directed take" in line for line in output)
    assert any("environment_location_bar" in line for line in output)
