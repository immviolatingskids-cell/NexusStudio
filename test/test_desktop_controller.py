import json

from config import CHARACTER_REFERENCE_IMAGES
from engine import takes
from engine.desktop_controller import DesktopStudioController


def test_controller_keeps_canonical_identity_outside_scene_state():
    controller = DesktopStudioController()
    character = controller.choose_character("luna")
    scene = controller.build_scene("getting ready", location="environment_location_bar", wardrobe_style="fashion_streetwear", seed=7)

    assert character.character_id == "luna_campbell"
    assert scene.brief.character_id == character.character_id
    assert scene.selection_ids["location"] == "environment_location_bar"
    assert scene.identity_anchors == controller.profile.anchors


def test_controller_locks_and_rerolls_only_adjustable_dimensions():
    controller = DesktopStudioController()
    controller.choose_character("luna")
    first = controller.build_scene(seed=1)
    locked = controller.lock("location")
    rerolled = controller.reroll()

    assert "location" in locked.brief.locks
    assert rerolled.selection_ids["location"] == first.selection_ids["location"]
    assert rerolled.brief.seed == first.brief.seed + 1


def test_fake_generation_uses_take_id_for_distinct_output_filenames(tmp_path, monkeypatch):
    monkeypatch.setattr(takes, "OUTPUT_DIR", tmp_path)
    controller = DesktopStudioController(output_dir=tmp_path)
    controller.choose_character("luna")
    controller.build_scene(seed=3)

    first = controller.generate()
    second = controller.generate()
    first_payload = json.loads(first.read_text(encoding="utf-8"))
    second_payload = json.loads(second.read_text(encoding="utf-8"))

    assert first_payload["take_id"] != second_payload["take_id"]
    assert first_payload["output"]["path"] != second_payload["output"]["path"]
    assert takes.verify_take(first_payload["take_id"])


def test_every_character_id_has_an_explicit_reference_mapping():
    controller = DesktopStudioController()
    for character in controller.list_characters():
        assert character.character_id in CHARACTER_REFERENCE_IMAGES
