import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import desktop


def _app():
    return QApplication.instance() or QApplication([])


def test_desktop_window_has_director_composition_and_canonical_cards():
    _app()
    window = desktop.DesktopWindow()

    assert window.stack.count() == 5
    assert len(window.character_cards) == 6
    assert window.quick_rail.objectName() == "previewRail"


def test_ui_asset_loader_reads_optional_presentation_asset_only(tmp_path, monkeypatch):
    assets = tmp_path / "UI_asset"
    assets.mkdir()
    image = assets / "hero.png"
    image.write_bytes(b"presentation-only")
    monkeypatch.setattr(desktop, "REFERENCE_IMAGES_DIR", tmp_path)

    assert desktop._ui_asset() == image


def test_character_selection_populates_presentation_without_replacing_identity():
    _app()
    window = desktop.DesktopWindow()
    window.choose_character("luna_campbell")

    assert window.controller.character.character_id == "luna_campbell"
    assert "Luna Campbell" in window.summary_copy.text()
    assert "canonical profile" in window.summary_traits.text()
