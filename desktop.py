"""CharacterStudio's local PySide6 desktop director.

This module owns widgets and navigation only.  ``DesktopStudioController``
remains the sole bridge from the presentation layer to NexusStudio's engine.
"""

from __future__ import annotations

import sys
from functools import partial

try:
    from PySide6.QtCore import QObject, QThread, Signal
    from PySide6.QtGui import QKeySequence, QPixmap, QShortcut
    from PySide6.QtWidgets import (
        QApplication, QButtonGroup, QComboBox, QFrame, QHBoxLayout, QLabel,
        QLineEdit, QListWidget, QMainWindow, QMessageBox, QPushButton,
        QScrollArea, QStackedWidget, QTextEdit, QVBoxLayout, QWidget,
    )
except ImportError as exc:  # keeps CLI and maintenance tools dependency-free
    PYSIDE_ERROR = exc
else:
    PYSIDE_ERROR = None

from engine.desktop_controller import DesktopStudioController


if PYSIDE_ERROR is None:
    class GenerationWorker(QObject):
        completed = Signal(int, str)
        failed = Signal(int, str)

        def __init__(self, controller: DesktopStudioController, session: int, scene, parent_take_id: str | None) -> None:
            super().__init__()
            self.controller = controller
            self.session = session
            self.scene = scene
            self.parent_take_id = parent_take_id

        def run(self) -> None:
            try:
                self.completed.emit(self.session, str(self.controller.generate("fake", scene=self.scene, parent_take_id=self.parent_take_id)))
            except Exception as exc:  # displayed as a recoverable local failure
                self.failed.emit(self.session, str(exc))


    class DesktopWindow(QMainWindow):
        steps = ("Character", "Scene", "Visual Treatment", "Preview", "Generate")

        def __init__(self) -> None:
            super().__init__()
            self.controller = DesktopStudioController()
            self.session = 0
            self.setWindowTitle("CharacterStudio — NexusStudio Director")
            self.resize(1160, 760)
            self.setStyleSheet("""
                QWidget { background: #17191f; color: #e9e8ed; font-size: 14px; }
                QPushButton, QComboBox, QLineEdit, QTextEdit, QListWidget { background: #262a33; border: 1px solid #414754; border-radius: 6px; padding: 8px; }
                QPushButton:hover, QPushButton:focus { border: 1px solid #9c8cff; background: #302e45; }
                QPushButton:checked { background: #6253bf; border-color: #b7abff; }
                QLabel#muted { color: #aaa8b4; } QLabel#title { font-size: 24px; font-weight: 600; }
            """)
            root = QWidget(); self.setCentralWidget(root)
            layout = QHBoxLayout(root); layout.setContentsMargins(24, 24, 24, 24); layout.setSpacing(28)
            rail = QVBoxLayout(); rail.setSpacing(8); layout.addLayout(rail, 1)
            self.step_buttons: list[QPushButton] = []
            for index, label in enumerate(self.steps):
                button = QPushButton(f"{index + 1}. {label}"); button.setCheckable(True); button.clicked.connect(partial(self.go_to, index))
                rail.addWidget(button); self.step_buttons.append(button)
            rail.addStretch()
            self.stack = QStackedWidget(); layout.addWidget(self.stack, 5)
            self._build_character_page(); self._build_scene_page(); self._build_treatment_page(); self._build_preview_page(); self._build_generate_page()
            QShortcut(QKeySequence("Return"), self, activated=self.next_step)
            QShortcut(QKeySequence("Backspace"), self, activated=self.previous_step)
            self.go_to(0)

        def _page(self, title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
            page = QWidget(); layout = QVBoxLayout(page); layout.setSpacing(14)
            heading = QLabel(title); heading.setObjectName("title"); layout.addWidget(heading)
            muted = QLabel(subtitle); muted.setObjectName("muted"); muted.setWordWrap(True); layout.addWidget(muted)
            self.stack.addWidget(page); return page, layout

        def _build_character_page(self) -> None:
            _, layout = self._page("Choose a character", "The selected canonical record and protected identity profile remain authoritative for this session.")
            scroll = QScrollArea(); scroll.setWidgetResizable(True); body = QWidget(); cards = QVBoxLayout(body)
            for character in self.controller.list_characters():
                card = QPushButton(); card.setMinimumHeight(90)
                interests = ", ".join(character.interests[:2])
                card.setText(f"{character.identity.name} · {character.identity.age} · {character.identity.home}\n{character.occupation.primary} — {', '.join(character.personality[:2])}; {interests}")
                card.clicked.connect(partial(self.choose_character, character.character_id)); cards.addWidget(card)
            cards.addStretch(); scroll.setWidget(body); layout.addWidget(scroll)

        def _build_scene_page(self) -> None:
            _, layout = self._page("Direct the scene", "Choose from the current curated vocabulary. Your wording is kept as direction text; it is not parsed into identity or hidden scene fields.")
            self.activity = QTextEdit(); self.activity.setPlaceholderText("What is happening? e.g. getting ready for a concert")
            layout.addWidget(self.activity)
            self.combos: dict[str, QComboBox] = {}
            for dimension in ("location", "atmosphere", "wardrobe", "pose", "lighting", "framing"):
                combo = QComboBox(); combo.addItem("Suggested by engine", None)
                for entry in self.controller.choices(dimension): combo.addItem(entry.text, entry.id)
                layout.addWidget(QLabel(dimension.replace("_", " ").title())); layout.addWidget(combo); self.combos[dimension] = combo
            continue_button = QPushButton("Continue to visual treatment"); continue_button.clicked.connect(self.build_scene); layout.addWidget(continue_button)

        def _build_treatment_page(self) -> None:
            _, layout = self._page("Visual treatment", "Only visual treatments backed by the current engine are available.")
            self.styles = QButtonGroup(self); self.styles.setExclusive(True)
            for style in ("clean", "natural", "documentary"):
                button = QPushButton(style.title()); button.setCheckable(True); self.styles.addButton(button); layout.addWidget(button)
                if style == "natural": button.setChecked(True)
            button = QPushButton("Preview resolved scene"); button.clicked.connect(self.apply_treatment); layout.addWidget(button)

        def _build_preview_page(self) -> None:
            _, layout = self._page("Preview", "Identity protections are separate from adjustable scene choices.")
            self.preview_text = QTextEdit(); self.preview_text.setReadOnly(True); layout.addWidget(self.preview_text, 1)
            row = QHBoxLayout(); self.lock_combo = QComboBox(); row.addWidget(self.lock_combo)
            lock_button = QPushButton("Toggle lock"); lock_button.clicked.connect(self.toggle_lock); row.addWidget(lock_button)
            reroll_button = QPushButton("Reroll unlocked"); reroll_button.clicked.connect(lambda: self.reroll(None)); row.addWidget(reroll_button)
            one_button = QPushButton("Reroll selected"); one_button.clicked.connect(self.reroll_selected); row.addWidget(one_button); layout.addLayout(row)
            save = QPushButton("Save immutable preview take"); save.clicked.connect(self.save_take); layout.addWidget(save)

        def _build_generate_page(self) -> None:
            _, layout = self._page("Generate", "Fake generation is local and deterministic. Gemini is intentionally unavailable here until its environment key and optional package are configured.")
            self.generate_status = QLabel("Ready to create a local fake-generation take."); self.generate_status.setWordWrap(True); layout.addWidget(self.generate_status)
            generate = QPushButton("Generate with fake provider"); generate.clicked.connect(self.generate); layout.addWidget(generate)
            layout.addWidget(QLabel("Local take history")); self.history = QListWidget(); layout.addWidget(self.history, 1)

        def choose_character(self, character_id: str) -> None:
            character = self.controller.choose_character(character_id); self.session += 1
            reference = self.controller.reference_image()
            self.statusBar().showMessage(f"{character.identity.name} selected" + (f" · reference: {reference.name}" if reference else " · no mapped reference"))
            self.go_to(1)

        def build_scene(self) -> None:
            try:
                direction = {"wardrobe_style" if key == "wardrobe" else key: combo.currentData() for key, combo in self.combos.items()}
                self.controller.build_scene(self.activity.toPlainText().strip() or None, **direction); self.go_to(2)
            except Exception as exc: self.error(exc)

        def apply_treatment(self) -> None:
            try:
                style = self.styles.checkedButton().text().lower(); self.controller.update_direction(image_style=style); self.refresh_preview(); self.go_to(3)
            except Exception as exc: self.error(exc)

        def refresh_preview(self) -> None:
            scene, prompt = self.controller.preview()
            adjustable = "\n".join(f"{key}: {value} [{scene.selection_ids.get(key, 'free text')}]" for key, value in scene.selections.items())
            self.preview_text.setPlainText("ADJUSTABLE SCENE\n" + adjustable + "\n\nIDENTITY PROTECTIONS\n" + "\n".join(scene.identity_anchors) + "\n\nEXCLUSIONS\n" + "\n".join(scene.negative_constraints) + "\n\nPROMPT DOCUMENT\n" + prompt.render())
            self.lock_combo.clear(); self.lock_combo.addItems(scene.selection_ids.keys())

        def toggle_lock(self) -> None:
            try: self.controller.lock(self.lock_combo.currentText(), self.lock_combo.currentText() not in self.controller.scene.brief.locks); self.refresh_preview()
            except Exception as exc: self.error(exc)

        def reroll(self, dimension: str | None) -> None:
            try: self.controller.reroll(dimension); self.refresh_preview()
            except Exception as exc: self.error(exc)

        def reroll_selected(self) -> None: self.reroll(self.lock_combo.currentText())

        def save_take(self) -> None:
            try: self.statusBar().showMessage(f"Saved {self.controller.save().name}")
            except Exception as exc: self.error(exc)

        def generate(self) -> None:
            self.generate_status.setText("Generating locally…")
            scene, _ = self.controller.preview()
            self.thread = QThread(self); self.worker = GenerationWorker(self.controller, self.session, scene, self.controller.parent_take_id); self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run); self.worker.completed.connect(self.generation_complete); self.worker.failed.connect(self.error)
            self.worker.completed.connect(self.thread.quit); self.worker.failed.connect(self.thread.quit); self.thread.start()

        def generation_complete(self, session: int, path: str) -> None:
            if session != self.session:
                return
            self.generate_status.setText(f"Generated and recorded: {path}"); self.refresh_history()

        def refresh_history(self) -> None:
            self.history.clear()
            for take in self.controller.inspect_takes(): self.history.addItem(f"{take['take_id']} · {take['character_id']} · {take['provider']} · integrity: {self.controller.verify_take(take['take_id'])}")

        def go_to(self, index: int) -> None:
            self.stack.setCurrentIndex(index)
            for position, button in enumerate(self.step_buttons): button.setChecked(position == index)
            if index == 4: self.refresh_history()

        def next_step(self) -> None: self.go_to(min(self.stack.currentIndex() + 1, len(self.steps) - 1))
        def previous_step(self) -> None: self.go_to(max(self.stack.currentIndex() - 1, 0))
        def error(self, *details: object) -> None: QMessageBox.warning(self, "CharacterStudio", str(details[-1]))


def main() -> int:
    if PYSIDE_ERROR is not None:
        print("PySide6 is required for the desktop app. Install the desktop extra: pip install -e .[desktop]", file=sys.stderr)
        return 2
    app = QApplication(sys.argv); window = DesktopWindow(); window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
