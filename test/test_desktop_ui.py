import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

import desktop
from engine.generation_pipeline import generate_image


def _app():
    return QApplication.instance() or QApplication([])


def test_desktop_window_has_director_composition_and_canonical_cards():
    _app()
    window = desktop.DesktopWindow()

    assert window.stack.count() == 6
    assert len(window.character_cards) == 6
    assert len(window.nav) == 6
    assert len(window.tabs) == 6


def test_character_selection_populates_presentation_without_replacing_identity():
    _app()
    window = desktop.DesktopWindow()
    window.choose_character("luna_campbell")

    assert window.controller.character.character_id == "luna_campbell"
    assert window.character_cards["luna_campbell"].isChecked()
    assert window.controller.profile.character_id == "luna_campbell"


def test_navigation_switches_both_navigation_components():
    _app()
    window = desktop.DesktopWindow()
    window.choose_character("ayami_tanaka")
    window.navigate(4)

    assert window.stack.currentIndex() == 4
    assert window.nav[4].isChecked()
    assert window.tabs[4].isChecked()
    assert window.controller.character.character_id == "ayami_tanaka"


def test_scene_and_style_choices_update_presentation_state_only():
    _app()
    window = desktop.DesktopWindow()
    preview = desktop.Preview()
    window.select_catalog("Scenes", "Cozy Café", "environment_location_cafe", "Everyday", preview)
    window.select_catalog("Styles", "Casual", "casual", "Relaxed", preview)

    assert window.selected_scene == "environment_location_cafe"
    assert window.selected_style == "casual"
    assert window.controller.scene is None


def test_create_workflow_builds_the_v09_prompt_without_a_second_scene_pipeline():
    _app()
    window = desktop.DesktopWindow()
    window.choose_character("ayami_tanaka")
    window.create_mode.setCurrentIndex(window.create_mode.findData("lifestyle"))
    window.adapter_combo.setCurrentIndex(window.adapter_combo.findData("gemini"))
    window.idea.setPlainText("reading quietly")
    window.environment_override.setText("a quiet independent coffee shop")

    window.resolve_preview()

    assert window.create_stack.currentIndex() == 3
    assert window.current_prompt.adapter_name == "gemini"
    assert window.current_prompt.source_scene_mode == "lifestyle"
    assert "reading quietly" in window.prompt_preview.toPlainText()
    assert "quiet independent coffee shop" in window.prompt_preview.toPlainText()


def test_missing_preview_image_uses_safe_fallback(tmp_path):
    _app()
    label = desktop.picture(tmp_path / "missing.png")

    assert label.text() == ""
    assert not label.pixmap().isNull()


def test_settings_control_persists_value(monkeypatch):
    _app()
    window = desktop.DesktopWindow()
    field = window.setting_controls["Theme"]
    field.setText("Midnight Purple")
    window.persist_setting("Theme", field)

    assert window.preferences.value("settings/Theme") == "Midnight Purple"


def test_gallery_refresh_details_favorite_and_reuse(tmp_path, monkeypatch):
    _app()
    window = desktop.DesktopWindow()
    window.preferences.setValue("gallery/favorites", [])
    window.preferences.sync()
    window.controller.output_dir = tmp_path
    window.choose_character("luna_campbell")
    result = generate_image("luna_campbell", "lifestyle", provider="fake", output_dir=tmp_path)
    record_id = result.record_id

    window.refresh_gallery()
    window.select_record(record_id)

    assert window.selected_record_id == record_id
    assert "luna_campbell" in window.gallery_copy.text()
    assert window.use_take.isEnabled()

    window.toggle_favorite()
    assert record_id in window.favorite_ids()

    window.use_selected_take()
    assert window.stack.currentIndex() == 0
    assert window.create_stack.currentIndex() == 3
    assert window.create_mode.currentData() == "lifestyle"


def test_desktop_manual_qa_is_external_and_has_no_generation_wiring():
    _app()
    window = desktop.DesktopWindow()
    assert not hasattr(desktop, "GenerationWorker")
    assert not hasattr(window, "generate_take")
    assert not hasattr(window, "provider_combo")
    assert "external review notes" in window.manual_qa_text.text()


def test_character_filters_favorites_and_use_action():
    _app()
    window = desktop.DesktopWindow()
    window.preferences.setValue("characters/favorites", [])
    window.navigate(1)
    window.choose_character("ayami_tanaka")
    window.toggle_character_favorite()
    window.character_filter.setCurrentText("Favorites")
    _app().processEvents()

    assert window.character_cards["ayami_tanaka"].isVisibleTo(window.stack.widget(1))
    assert not window.character_cards["luna_campbell"].isVisibleTo(window.stack.widget(1))

    window.use_selected_character()
    assert window.stack.currentIndex() == 0
    assert window.create_stack.currentIndex() == 1


def test_empty_card_collection_renders_usable_empty_state():
    _app()
    window = desktop.DesktopWindow()
    area = window.grid([])
    host = area.widget()

    assert host.layout().count() == 1
    assert "Nothing to show" in host.layout().itemAt(0).widget().text()
