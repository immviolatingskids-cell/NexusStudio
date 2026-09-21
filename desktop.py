"""CharacterStudio's polished local PySide6 director.

Widgets only present canonical character and scene data. Resolution, identity
protection, persistence, and provider work remain in DesktopStudioController.
"""

from __future__ import annotations

import sys
from functools import partial
from pathlib import Path

from config import REFERENCE_IMAGES_DIR
from engine.desktop_controller import DesktopStudioController

try:
    from PySide6.QtCore import QObject, Qt, QThread, Signal
    from PySide6.QtGui import QKeySequence, QPixmap, QShortcut
    from PySide6.QtWidgets import (
        QApplication, QButtonGroup, QComboBox, QFrame, QGridLayout, QHBoxLayout,
        QLabel, QListWidget, QMainWindow, QMessageBox, QPushButton, QSizePolicy,
        QScrollArea, QStackedWidget, QTextEdit, QVBoxLayout, QWidget,
    )
except ImportError as exc:
    PYSIDE_ERROR = exc
else:
    PYSIDE_ERROR = None


if PYSIDE_ERROR is None:
    ACCENT, PANEL, MUTED = "#69efac", "#0d1c22", "#9eafc4"
    CHARACTER_IMAGES = {
        "ayami_tanaka": "ayami.png", "charlotte_taylor_rose": "charlotte.png",
        "idun_braten": "idun.png", "luna_campbell": "luna.png",
        "naomi": "naomi.png", "zara": "zara.png",
    }

    class GenerationWorker(QObject):
        completed = Signal(int, str)
        failed = Signal(int, str)

        def __init__(self, controller, session, scene, parent_take_id):
            super().__init__()
            self.controller, self.session, self.scene, self.parent_take_id = controller, session, scene, parent_take_id

        def run(self):
            try:
                result = self.controller.generate("fake", scene=self.scene, parent_take_id=self.parent_take_id)
                self.completed.emit(self.session, str(result))
            except Exception as exc:
                self.failed.emit(self.session, str(exc))

    def _ui_asset() -> Path | None:
        """Optional purely decorative asset; never used as character identity."""
        folder = REFERENCE_IMAGES_DIR / "UI_asset"
        for pattern in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
            matches = sorted(folder.glob(pattern))
            if matches:
                return matches[0]
        return None

    def _image(path: Path | None, width: int, height: int) -> QLabel:
        label = QLabel("No preview asset")
        label.setObjectName("imagePlaceholder")
        label.setAlignment(Qt.AlignCenter)
        label.setFixedSize(width, height)
        if path and path.is_file():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                label.setPixmap(pixmap.scaled(width, height, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        return label

    class CharacterCard(QPushButton):
        def __init__(self, character, image_path):
            super().__init__()
            self.character_id = character.character_id
            self.setObjectName("characterCard")
            self.setCheckable(True)
            self.setMinimumWidth(126)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            content = QVBoxLayout(self)
            content.setContentsMargins(8, 8, 8, 10)
            content.setSpacing(5)
            content.addWidget(_image(image_path, 108, 116))
            name = QLabel(character.identity.name.split()[0]); name.setObjectName("cardName"); content.addWidget(name)
            detail = QLabel(f"{character.identity.age}  ·  {character.identity.nationality}"); detail.setObjectName("cardDetail"); content.addWidget(detail)
            tags = QLabel("  ".join(character.interests[:2])); tags.setObjectName("tagText"); tags.setWordWrap(True); content.addWidget(tags)

    class DesktopWindow(QMainWindow):
        steps = ("Character", "Scene", "Style", "Preview", "Generate")

        def __init__(self):
            super().__init__()
            self.controller = DesktopStudioController()
            self.session = 0
            self.character_cards = {}
            self.setWindowTitle("CharacterStudio — NexusStudio Director")
            self.resize(1440, 900)
            self.setMinimumSize(1080, 720)
            self.setStyleSheet(self._stylesheet())
            root = QWidget(); root.setObjectName("root"); self.setCentralWidget(root)
            shell = QVBoxLayout(root); shell.setContentsMargins(26, 18, 26, 18); shell.setSpacing(14)
            shell.addWidget(self._header())
            body = QHBoxLayout(); body.setSpacing(16); shell.addLayout(body, 1)
            body.addWidget(self._rail(), 2)
            self.stack = QStackedWidget(); self.stack.setObjectName("stage"); body.addWidget(self.stack, 7)
            body.addWidget(self._quick_preview(), 2)
            self._character_page(); self._scene_page(); self._style_page(); self._preview_page(); self._generate_page()
            shell.addWidget(self._footer())
            QShortcut(QKeySequence("Return"), self, activated=self.next_step)
            QShortcut(QKeySequence("Backspace"), self, activated=self.previous_step)
            self.go_to(0)

        @staticmethod
        def _stylesheet():
            return f"""
                QWidget#root {{ background: #071217; color: #edf4fa; font-family: 'Segoe UI'; font-size: 13px; }}
                QFrame#topBar {{ border-bottom: 1px solid #26404a; }}
                QFrame#panel, QFrame#rail, QFrame#previewRail, QWidget#stage, QFrame#nextBar {{ background: {PANEL}; border: 1px solid #294752; border-radius: 12px; }}
                QLabel#brand {{ font-family: 'Segoe UI'; font-size: 31px; font-weight: 700; color: #fbfcff; }}
                QLabel#brandAccent, QLabel#sectionTitle {{ color: {ACCENT}; }}
                QLabel#eyebrow, QLabel#muted, QLabel#cardDetail {{ color: {MUTED}; }}
                QLabel#eyebrow {{ font-size: 10px; font-weight: 700; letter-spacing: 1.6px; }} QLabel#sectionTitle {{ font-size: 22px; font-weight: 700; }}
                QLabel#cardName {{ font-size: 15px; font-weight: 700; }} QLabel#tagText {{ color: #bfd1ea; font-size: 11px; }}
                QLabel#imagePlaceholder {{ background: #12272e; border: 1px solid #365862; border-radius: 8px; color: {MUTED}; }}
                QPushButton {{ background: #102229; border: 1px solid #31535e; border-radius: 8px; padding: 10px; text-align: left; }}
                QPushButton:hover, QPushButton:focus {{ border: 1px solid {ACCENT}; background: #15322f; }}
                QPushButton#characterCard {{ background: #0b181e; padding: 8px; }} QPushButton#characterCard:checked {{ border: 2px solid {ACCENT}; background: #102b28; }}
                QPushButton#stepButton {{ color: #d9e7f7; min-height: 42px; border-color: transparent; background: transparent; }} QPushButton#stepButton:checked {{ color: {ACCENT}; background: #102c29; border-color: #347b63; }}
                QPushButton#treatmentCard {{ min-height: 100px; font-size: 14px; font-weight: 600; }} QPushButton#treatmentCard:checked {{ border: 2px solid {ACCENT}; background: #102d29; color: {ACCENT}; }}
                QPushButton#primary {{ background: {ACCENT}; border-color: {ACCENT}; color: #06150f; font-weight: 800; text-align: center; min-height: 32px; padding-left: 18px; padding-right: 18px; }}
                QPushButton#secondary {{ text-align: center; }}
                QComboBox, QTextEdit, QListWidget {{ background: #09191f; border: 1px solid #31535e; border-radius: 8px; padding: 9px; color: #edf4fa; selection-background-color: #1d7056; }}
                QComboBox:focus, QTextEdit:focus {{ border-color: {ACCENT}; }}
                QScrollArea {{ border: none; background: transparent; }} QScrollArea > QWidget > QWidget {{ background: transparent; }}
                QScrollBar:horizontal {{ height: 8px; background: transparent; margin: 3px 0; }} QScrollBar::handle:horizontal {{ background: #31535e; border-radius: 4px; min-width: 44px; }}
            """

        def _header(self):
            panel = QFrame(); panel.setObjectName("topBar"); layout = QHBoxLayout(panel); layout.setContentsMargins(8, 4, 8, 12)
            left = QVBoxLayout(); brand = QHBoxLayout(); first = QLabel("Character"); first.setObjectName("brand"); second = QLabel("Studio"); second.setObjectName("brandAccent"); second.setStyleSheet("font-size: 33px; font-weight: 700;"); brand.addWidget(first); brand.addWidget(second); brand.addStretch(); left.addLayout(brand)
            eyebrow = QLabel("REAL PEOPLE, INFINITE MOMENTS."); eyebrow.setObjectName("eyebrow"); left.addWidget(eyebrow); layout.addLayout(left, 2)
            quote = QLabel("A local studio for consistent people and new moments."); quote.setObjectName("muted"); quote.setAlignment(Qt.AlignCenter); quote.setStyleSheet("font-style: italic;"); layout.addWidget(quote, 2)
            status = QLabel("LOCAL STUDIO  ·  6 CHARACTERS  ·  READY"); status.setObjectName("eyebrow"); status.setAlignment(Qt.AlignRight | Qt.AlignVCenter); status.setStyleSheet(f"color: {ACCENT};"); layout.addWidget(status, 3)
            return panel

        def _rail(self):
            rail = QFrame(); rail.setObjectName("rail"); rail.setMinimumWidth(235); rail.setMaximumWidth(270); layout = QVBoxLayout(rail); layout.setContentsMargins(15, 18, 15, 15); layout.setSpacing(8)
            title = QLabel("Scene Director"); title.setObjectName("sectionTitle"); layout.addWidget(title)
            blurb = QLabel("A calm, guided flow to create beautiful, consistent takes."); blurb.setObjectName("muted"); blurb.setWordWrap(True); layout.addWidget(blurb); layout.addSpacing(14)
            self.step_buttons = []; descriptions = ("Choose who is in the scene", "Set the moment and setting", "Choose the visual language", "Review and protect choices", "Create a local take")
            for index, (label, description) in enumerate(zip(self.steps, descriptions), 1):
                button = QPushButton(f"{index:02d}  {label}\n      {description}"); button.setObjectName("stepButton"); button.setCheckable(True); button.clicked.connect(partial(self.go_to, index - 1)); layout.addWidget(button); self.step_buttons.append(button)
            layout.addStretch(); note = QLabel("Simple choices.\nBeautiful results."); note.setObjectName("muted"); note.setAlignment(Qt.AlignCenter); note.setStyleSheet("font-style: italic;"); layout.addWidget(note)
            return rail

        def _quick_preview(self):
            rail = QFrame(); rail.setObjectName("previewRail"); rail.setMinimumWidth(225); rail.setMaximumWidth(250); self.quick_rail = rail; layout = QVBoxLayout(rail); layout.setContentsMargins(15, 18, 15, 15)
            title = QLabel("Reference Preview"); title.setObjectName("sectionTitle"); layout.addWidget(title)
            self.quick_image = _image(None, 195, 292); layout.addWidget(self.quick_image, alignment=Qt.AlignHCenter)
            self.quick_caption = QLabel("Choose a character to load their approved visual reference."); self.quick_caption.setObjectName("muted"); self.quick_caption.setWordWrap(True); layout.addWidget(self.quick_caption)
            layout.addStretch(); tagline = QLabel("Identity stays steady.\nThe moment can change."); tagline.setAlignment(Qt.AlignCenter); tagline.setStyleSheet("color: #b9c9ef; font-style: italic;"); layout.addWidget(tagline)
            return rail

        def _page(self, step, title, detail):
            page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(24, 22, 24, 18); layout.setSpacing(11)
            eyebrow = QLabel(f"STEP {step} OF 5"); eyebrow.setObjectName("eyebrow"); layout.addWidget(eyebrow)
            heading = QLabel(title); heading.setObjectName("sectionTitle"); heading.setStyleSheet("font-size: 24px;"); layout.addWidget(heading)
            muted = QLabel(detail); muted.setObjectName("muted"); muted.setWordWrap(True); layout.addWidget(muted)
            self.stack.addWidget(page); return page, layout

        def _character_page(self):
            _, layout = self._page(1, "Choose a Character", "Select a canonical character to feature in your scene. Their protected identity remains outside the scene controls.")
            cards = QWidget(); row = QHBoxLayout(cards); row.setContentsMargins(0, 0, 0, 0); row.setSpacing(10); group = QButtonGroup(self); group.setExclusive(True)
            for character in self.controller.list_characters():
                card = CharacterCard(character, REFERENCE_IMAGES_DIR / CHARACTER_IMAGES[character.character_id]); card.setMinimumHeight(214); group.addButton(card); card.clicked.connect(partial(self.choose_character, character.character_id)); row.addWidget(card); self.character_cards[character.character_id] = card
            row.addStretch()
            self.character_scroller = QScrollArea(); self.character_scroller.setWidgetResizable(False); self.character_scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded); self.character_scroller.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.character_scroller.setWidget(cards); self.character_scroller.setFixedHeight(232)
            layout.addWidget(self.character_scroller)
            self.selected_summary = QFrame(); self.selected_summary.setObjectName("panel"); summary = QHBoxLayout(self.selected_summary); self.summary_image = _image(None, 94, 112); summary.addWidget(self.summary_image)
            self.summary_copy = QLabel("Choose a card to see canonical identity context."); self.summary_copy.setWordWrap(True); summary.addWidget(self.summary_copy, 3)
            self.summary_traits = QLabel("Identity protections remain separate from this presentation."); self.summary_traits.setObjectName("muted"); self.summary_traits.setWordWrap(True); summary.addWidget(self.summary_traits, 2); layout.addWidget(self.selected_summary)
            layout.addStretch(); layout.addWidget(self._next_bar("Continue", self.build_scene_from_selection))

        def _scene_page(self):
            _, layout = self._page(2, "Direct the Scene", "Friendly labels are backed by stable pool IDs. Natural wording is preserved as direction text only.")
            self.activity = QTextEdit(); self.activity.setFixedHeight(74); self.activity.setPlaceholderText("What is happening? e.g. getting ready for a concert"); layout.addWidget(self.activity)
            self.combos = {}; grid = QGridLayout(); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(9)
            for index, dimension in enumerate(("location", "atmosphere", "wardrobe", "pose", "lighting", "framing")):
                grid.addWidget(QLabel(dimension.title()), index // 2 * 2, index % 2); combo = QComboBox(); combo.addItem("Suggested by engine", None)
                for entry in self.controller.choices(dimension): combo.addItem(entry.text, entry.id)
                grid.addWidget(combo, index // 2 * 2 + 1, index % 2); self.combos[dimension] = combo
            layout.addLayout(grid); layout.addStretch(); layout.addWidget(self._next_bar("Choose visual treatment", self.build_scene))

        def _style_page(self):
            _, layout = self._page(3, "Set the Visual Treatment", "Choose only the current engine-backed treatment. This changes technical guidance, never character identity.")
            self.styles = QButtonGroup(self); self.styles.setExclusive(True); row = QHBoxLayout()
            for style, copy in (("clean", "Clean\nClear and intentional."), ("natural", "Natural\nGrounded photographic realism."), ("documentary", "Documentary\nObserved, lived-in detail.")):
                button = QPushButton(copy); button.setObjectName("treatmentCard"); button.setCheckable(True); button.setMinimumHeight(100); button.setProperty("style_id", style); self.styles.addButton(button); row.addWidget(button)
                if style == "natural": button.setChecked(True)
            layout.addLayout(row); layout.addStretch(); layout.addWidget(self._next_bar("Preview resolved take", self.apply_treatment))

        def _preview_page(self):
            _, layout = self._page(4, "Preview & Lock", "Resolved choices can be locked or rerolled. Identity protections are shown separately and cannot be edited here.")
            content = QHBoxLayout(); self.preview_text = QTextEdit(); self.preview_text.setReadOnly(True); content.addWidget(self.preview_text, 3)
            actions = QVBoxLayout(); actions.addWidget(QLabel("Adjust a resolved choice")); self.lock_combo = QComboBox(); self.lock_combo.currentTextChanged.connect(self._refresh_lock_label); actions.addWidget(self.lock_combo)
            self.lock_button = QPushButton("Lock selected choice"); self.lock_button.clicked.connect(self.toggle_lock); actions.addWidget(self.lock_button)
            reroll_one = QPushButton("Reroll selected choice"); reroll_one.clicked.connect(self.reroll_selected); actions.addWidget(reroll_one)
            reroll_all = QPushButton("Reroll unlocked choices"); reroll_all.clicked.connect(lambda: self.reroll(None)); actions.addWidget(reroll_all); actions.addStretch()
            save = QPushButton("Save immutable preview"); save.setObjectName("secondary"); save.clicked.connect(self.save_take); actions.addWidget(save); content.addLayout(actions, 1); layout.addLayout(content, 1); layout.addWidget(self._next_bar("Continue to generate", lambda: self.go_to(4)))

        def _generate_page(self):
            _, layout = self._page(5, "Generate a Take", "Fake generation is deterministic and local. Gemini appears only when its local credential and optional package are available.")
            self.generate_status = QLabel("Ready for a local fake-generation take."); self.generate_status.setObjectName("muted"); self.generate_status.setWordWrap(True); layout.addWidget(self.generate_status)
            generate = QPushButton("Generate with fake provider  →"); generate.setObjectName("primary"); generate.clicked.connect(self.generate); layout.addWidget(generate)
            layout.addWidget(QLabel("Local take history")); self.history = QListWidget(); layout.addWidget(self.history, 1)

        def _next_bar(self, label, callback):
            bar = QFrame(); bar.setObjectName("nextBar"); row = QHBoxLayout(bar); row.setContentsMargins(14, 11, 14, 11); cue = QLabel("NEXT\nPress Enter to continue."); cue.setObjectName("eyebrow"); row.addWidget(cue); row.addStretch(); action = QPushButton(f"{label}  →"); action.setObjectName("primary"); action.clicked.connect(callback); row.addWidget(action); return bar

        def _footer(self):
            footer = QFrame(); footer.setObjectName("topBar"); row = QHBoxLayout(footer); row.setContentsMargins(8, 10, 8, 0); brand = QLabel("CHARACTERSTUDIO"); brand.setObjectName("eyebrow"); row.addWidget(brand); copy = QLabel("Direct scenes. Protect identity."); copy.setObjectName("muted"); row.addWidget(copy); row.addStretch(); keys = QLabel("Enter  Continue     Backspace  Back"); keys.setObjectName("muted"); row.addWidget(keys); return footer

        def choose_character(self, character_id):
            character = self.controller.choose_character(character_id); self.session += 1; self.character_cards[character_id].setChecked(True); reference = self.controller.reference_image()
            self.quick_rail.layout().removeWidget(self.quick_image); self.quick_image.deleteLater(); self.quick_image = _image(reference or _ui_asset(), 220, 330); self.quick_rail.layout().insertWidget(1, self.quick_image, alignment=Qt.AlignHCenter)
            self.quick_caption.setText(f"Approved reference for {character.identity.name}. It supports generation but does not alter canonical identity.")
            self.selected_summary.layout().removeWidget(self.summary_image); self.summary_image.deleteLater(); self.summary_image = _image(reference, 94, 112); self.selected_summary.layout().insertWidget(0, self.summary_image)
            self.summary_copy.setText(f"<b>{character.identity.name}</b><br>{character.identity.age} · {character.identity.home}<br>{character.occupation.primary}<br>{', '.join(character.personality[:3])}")
            self.summary_traits.setText("Interests\n" + " · ".join(character.interests[:4]) + "\n\nProtected identity stays in the canonical profile.")

        def build_scene_from_selection(self):
            if self.controller.character is None: self.error("Choose a character first.")
            else: self.go_to(1)

        def build_scene(self):
            try:
                direction = {"wardrobe_style" if key == "wardrobe" else key: combo.currentData() for key, combo in self.combos.items()}
                self.controller.build_scene(self.activity.toPlainText().strip() or None, **direction); self.go_to(2)
            except Exception as exc: self.error(exc)

        def apply_treatment(self):
            try:
                self.controller.update_direction(image_style=self.styles.checkedButton().property("style_id")); self.refresh_preview(); self.go_to(3)
            except Exception as exc: self.error(exc)

        def refresh_preview(self):
            scene, prompt = self.controller.preview()
            choices = "\n".join(f"- {key.title()}: {value}" + ("  [locked]" if key in scene.brief.locks else "") for key, value in scene.selections.items())
            self.preview_text.setPlainText("ADJUSTABLE SCENE\n\n" + choices + "\n\nIDENTITY PROTECTIONS\n\n" + "\n".join(f"- {item}" for item in scene.identity_anchors) + "\n\nEXCLUSIONS\n\n" + "\n".join(f"- {item}" for item in scene.negative_constraints) + "\n\nPROMPT DOCUMENT\n\n" + prompt.render())
            self.lock_combo.clear(); self.lock_combo.addItems(scene.selection_ids.keys()); self._refresh_lock_label()

        def _refresh_lock_label(self):
            if self.controller.scene is None: return
            dimension = self.lock_combo.currentText(); self.lock_button.setText("Unlock selected choice" if dimension in self.controller.scene.brief.locks else "Lock selected choice")

        def toggle_lock(self):
            try:
                dimension = self.lock_combo.currentText(); self.controller.lock(dimension, dimension not in self.controller.scene.brief.locks); self.refresh_preview()
            except Exception as exc: self.error(exc)

        def reroll(self, dimension):
            try: self.controller.reroll(dimension); self.refresh_preview()
            except Exception as exc: self.error(exc)

        def reroll_selected(self): self.reroll(self.lock_combo.currentText())

        def save_take(self):
            try: self.statusBar().showMessage(f"Saved immutable take: {self.controller.save().name}", 5000)
            except Exception as exc: self.error(exc)

        def generate(self):
            try: scene, _ = self.controller.preview()
            except Exception as exc: self.error(exc); return
            self.generate_status.setText("Generating locally…"); self.thread = QThread(self); self.worker = GenerationWorker(self.controller, self.session, scene, self.controller.parent_take_id); self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run); self.worker.completed.connect(self.generation_complete); self.worker.failed.connect(self.error); self.worker.completed.connect(self.thread.quit); self.worker.failed.connect(self.thread.quit); self.thread.start()

        def generation_complete(self, session, path):
            if session == self.session: self.generate_status.setText(f"Generated and recorded: {path}"); self.refresh_history()

        def refresh_history(self):
            self.history.clear()
            for take in self.controller.inspect_takes(): self.history.addItem(f"{take['take_id']}  ·  {take['character_id']}  ·  {take['provider']}  ·  integrity {self.controller.verify_take(take['take_id'])}")

        def go_to(self, index):
            self.stack.setCurrentIndex(index)
            for position, button in enumerate(self.step_buttons): button.setChecked(position == index)
            if index == 4: self.refresh_history()

        def next_step(self): self.go_to(min(self.stack.currentIndex() + 1, len(self.steps) - 1))
        def previous_step(self): self.go_to(max(self.stack.currentIndex() - 1, 0))
        def error(self, *details): QMessageBox.warning(self, "CharacterStudio", str(details[-1]))


def main():
    if PYSIDE_ERROR is not None:
        print("PySide6 is required for the desktop app. Install the desktop extra: pip install -e .[desktop]", file=sys.stderr)
        return 2
    app = QApplication(sys.argv); window = DesktopWindow(); window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
