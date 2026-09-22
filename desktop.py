"""CharacterStudio Midnight Purple PySide6 desktop shell."""
from __future__ import annotations
import sys
from functools import partial
from pathlib import Path
from config import OUTPUT_DIR, reference_image_for
from engine.desktop_controller import DesktopStudioController
from engine.adapter_registry import list_adapters
from engine.generation_pipeline import generate_image
from engine.prompt_pipeline import build_prompt
from engine.provider_registry import list_providers
from engine.record_store import list_records, load_record
from engine.scene_defaults import SCENE_MODES
try:
    from PySide6.QtCore import QEasingCurve, QObject, QPropertyAnimation, QSettings, QThread, Qt, Signal
    from PySide6.QtGui import QColor, QKeySequence, QLinearGradient, QPainter, QPixmap, QShortcut
    from PySide6.QtWidgets import (QApplication,QButtonGroup,QCheckBox,QComboBox,QFrame,QGraphicsOpacityEffect,QGridLayout,QHBoxLayout,QLabel,QLineEdit,QListWidget,QMainWindow,QMessageBox,QPushButton,QScrollArea,QStackedWidget,QTextEdit,QVBoxLayout,QWidget)
except ImportError as exc: PYSIDE_ERROR=exc
else: PYSIDE_ERROR=None

if PYSIDE_ERROR is None:
    DESTINATIONS=(("Create","Guide & generate"),("Characters","Meet the cast"),("Scenes","Places & situations"),("Styles","Visual moods"),("Gallery","Your creations"),("Settings","Preferences"))
    SCENES=(("Cozy Café","environment_location_cafe","Everyday · Indoor · Warm"),("Home Workspace","environment_location_study","Home · Focus · Modern"),("City Streets","environment_location_city_street","Urban · Night · Neon"),("Nature Escape","environment_location_lakeside","Outdoor · Nature · Travel"),("At Work","environment_location_office","Work · Indoor · Modern"),("Bookstore","environment_location_library","Leisure · Books · Cozy"),("Travel Adventure","environment_location_mountains","Travel · Outdoor · Active"),("Quiet Evening","environment_location_living_room","Home · Peaceful · Warm"))
    STYLES=(("Casual","fashion_casual","Everyday · Relaxed · Modern"),("Streetwear","fashion_streetwear","Urban · Trendy · Modern"),("Smart Casual","fashion_smart_casual","Polished · Clean · Versatile"),("Professional","fashion_workwear","Office · Smart · Realistic"),("Sport & Active","fashion_casual","Gym · Sport · Active"),("Loungewear","fashion_cozy","Home · Cozy · Relaxed"),("Fashion","fashion_minimalist","Trendy · Chic · Bold"),("Alternative","fashion_streetwear","Creative · Unique · Edgy"))

    class GenerationWorker(QObject):
        finished = Signal(object)
        failed = Signal(str)
        def __init__(self, character_id, mode, provider, adapter, density, overrides, output_dir, dry_run):
            super().__init__(); self.character_id=character_id; self.mode=mode; self.provider=provider; self.adapter=adapter; self.density=density; self.overrides=overrides; self.output_dir=output_dir; self.dry_run=dry_run
        def run(self):
            try: self.finished.emit(generate_image(self.character_id,self.mode,self.provider,self.adapter,self.density,self.overrides,self.dry_run,self.output_dir))
            except Exception as exc: self.failed.emit(str(exc))

    def picture(path:Path|None,height=170):
        label=QLabel(); label.setObjectName("image"); label.setAlignment(Qt.AlignCenter); label.setMinimumHeight(height)
        if path and path.is_file():
            pix=QPixmap(str(path))
            if not pix.isNull():
                scaled=pix.scaled(500,height,Qt.KeepAspectRatioByExpanding,Qt.SmoothTransformation); x=max(0,(scaled.width()-500)//2); y=min(max(0,scaled.height()-height),int(scaled.height()*.07)); label.setPixmap(scaled.copy(x,y,min(500,scaled.width()),min(height,scaled.height()-y)))
        if label.pixmap().isNull():
            pix=QPixmap(500,height); painter=QPainter(pix); gradient=QLinearGradient(0,0,500,height); gradient.setColorAt(0,QColor("#21113f")); gradient.setColorAt(.55,QColor("#111a3b")); gradient.setColorAt(1,QColor("#321352")); painter.fillRect(pix.rect(),gradient); painter.setPen(QColor("#9b52df")); painter.drawEllipse(330,-45,190,190); painter.setPen(QColor("#51336f")); painter.drawEllipse(-60,height-95,175,175); painter.end(); label.setPixmap(pix)
        return label

    class Card(QPushButton):
        def __init__(self,title,subtitle,tags,image=None):
            super().__init__(); self.setAccessibleName(title); self.setAccessibleDescription(subtitle); self.setObjectName("card"); self.setCheckable(True); self.setMinimumSize(190,250); self.search=(title+" "+subtitle+" "+tags).lower()
            box=QVBoxLayout(self); box.setContentsMargins(7,7,7,10); box.addWidget(picture(image)); name=QLabel(title); name.setObjectName("cardTitle"); box.addWidget(name); sub=QLabel(subtitle); sub.setObjectName("muted"); sub.setWordWrap(True); box.addWidget(sub); chip=QLabel(tags); chip.setObjectName("chip"); chip.setWordWrap(True); box.addWidget(chip)

    class Preview(QFrame):
        def __init__(self): super().__init__(); self.setObjectName("panel"); self.box=QVBoxLayout(self); self.show("Select an item","Details update immediately.")
        def show(self,title,detail,image=None):
            while self.box.count():
                w=self.box.takeAt(0).widget()
                if w: w.deleteLater()
            self.box.addWidget(picture(image,280)); h=QLabel(title); h.setObjectName("previewTitle"); self.box.addWidget(h); text=QLabel(detail); text.setObjectName("muted"); text.setWordWrap(True); self.box.addWidget(text); self.box.addStretch()

    class DesktopWindow(QMainWindow):
        def __init__(self):
            super().__init__(); self.controller=DesktopStudioController(); OUTPUT_DIR.mkdir(parents=True,exist_ok=True); self.preferences=QSettings(str(OUTPUT_DIR / "desktop-settings.ini"),QSettings.IniFormat); self.selected_scene=None; self.selected_style=None; self.character_cards={}
            self.setWindowTitle("CharacterStudio"); self.resize(1536,960); self.setMinimumSize(1080,700); self.setStyleSheet(self.qss())
            root=QWidget(); root.setObjectName("root"); self.setCentralWidget(root); shell=QHBoxLayout(root); shell.setContentsMargins(0,0,0,0); shell.setSpacing(0); shell.addWidget(self.sidebar()); main=QVBoxLayout(); main.setContentsMargins(18,14,18,12); main.addWidget(self.topbar()); self.stack=QStackedWidget(); main.addWidget(self.stack,1); main.addWidget(self.footer()); shell.addLayout(main,1)
            for page in (self.create_page(),self.characters_page(),self.catalog_page("Scenes",SCENES),self.catalog_page("Styles",STYLES),self.gallery_page(),self.settings_page()): self.stack.addWidget(page)
            for i in range(6): QShortcut(QKeySequence(f"Alt+{i+1}"),self,activated=partial(self.navigate,i))
            self.restore_session_preferences()
            self.navigate(0)
        @staticmethod
        def qss(): return """QWidget#root{background:#07091c;color:#f5f1ff;font:13px 'Segoe UI'} QFrame#side{background:#0b0d28;border-right:1px solid #29224f} QLabel#brand{font-size:23px;font-weight:700} QLabel#title{font-size:30px;font-weight:700;color:#d875ff} QLabel#previewTitle{font-size:20px;font-weight:700} QLabel#cardTitle{font-size:15px;font-weight:700} QLabel#muted{color:#bcb4dc} QLabel#image{background:#12162f;border-radius:7px;color:#77709a} QLabel#chip{background:#22204d;color:#ded5ff;border-radius:5px;padding:5px} QPushButton{color:#eeeaff;background:#111431;border:1px solid #2b2c59;border-radius:9px;padding:10px} QPushButton:hover{background:#191642;border-color:#9845df} QPushButton#nav{text-align:left;border-color:transparent;background:transparent;min-height:48px} QPushButton#nav:checked{background:#281451;border:1px solid #843bd2;border-left:3px solid #cf61ff} QPushButton#top:checked{background:#351064;border-color:#bd55ff} QPushButton#step:checked{background:#351064;border-color:#bd55ff} QPushButton#step[complete=true]{color:#d99cff;border-color:#61408a;background:#171431} QPushButton#card{text-align:left;padding:0;background:#0b1429} QPushButton#card:checked{border:2px solid #c05cff;background:#17143b} QPushButton#primary{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #c34dff,stop:1 #8d5cff);color:#090316;font-weight:700;text-align:center;border:0} QFrame#panel{background:#0b1027;border:1px solid #292d56;border-radius:12px} QLineEdit,QTextEdit,QComboBox{background:#090d22;border:1px solid #30335d;border-radius:8px;padding:10px;color:#eeeaff} QScrollArea{border:0;background:transparent} QScrollArea>QWidget>QWidget{background:transparent}"""
        def sidebar(self):
            side=QFrame(); self.side=side; side.setObjectName("side"); side.setFixedWidth(285); box=QVBoxLayout(side); box.setContentsMargins(14,22,14,16); brand=QLabel("◈  CharacterStudio"); brand.setObjectName("brand"); box.addWidget(brand); muted=QLabel("Real People. Infinite Moments."); muted.setObjectName("muted"); box.addWidget(muted); box.addSpacing(22); self.nav=[]; group=QButtonGroup(self); group.setExclusive(True)
            for i,(title,sub) in enumerate(DESTINATIONS): b=QPushButton(f"{title}\n{sub}"); b.setObjectName("nav"); b.setCheckable(True); b.clicked.connect(partial(self.navigate,i)); group.addButton(b); self.nav.append(b); box.addWidget(b)
            box.addStretch(); quote=QLabel('“Same characters.\n Endless possibilities.”'); quote.setStyleSheet("color:#c89df5;font-style:italic"); box.addWidget(quote); return side
        def topbar(self):
            w=QWidget(); row=QHBoxLayout(w); row.setContentsMargins(0,0,0,0); self.tabs=[]; group=QButtonGroup(self); group.setExclusive(True)
            for i,(title,_) in enumerate(DESTINATIONS): b=QPushButton(title); b.setObjectName("top"); b.setCheckable(True); b.clicked.connect(partial(self.navigate,i)); group.addButton(b); self.tabs.append(b); row.addWidget(b)
            row.addStretch(); return w
        def footer(self):
            f=QFrame(); f.setObjectName("panel"); row=QHBoxLayout(f); row.addWidget(QLabel("✦  Tip: Browse visually or describe your idea naturally.")); row.addStretch(); ready=QLabel("Local Mode  ●  Ready"); ready.setStyleSheet("color:#4ee6d2"); row.addWidget(ready); return f
        def navigate(self,index):
            self.stack.setCurrentIndex(index)
            for i,b in enumerate(self.nav): b.setChecked(i==index)
            for i,b in enumerate(self.tabs): b.setChecked(i==index)
            if not self.preferences.value("appearance/reduced_motion",False,type=bool):
                page=self.stack.currentWidget(); effect=QGraphicsOpacityEffect(page); page.setGraphicsEffect(effect); self._page_animation=QPropertyAnimation(effect,b"opacity",self); self._page_animation.setDuration(160); self._page_animation.setStartValue(.55); self._page_animation.setEndValue(1.0); self._page_animation.setEasingCurve(QEasingCurve.OutCubic); self._page_animation.finished.connect(lambda p=page:p.setGraphicsEffect(None)); self._page_animation.start()
            if index==4: self.refresh_gallery()
        def header(self,title,subtitle,search=False):
            w=QWidget(); row=QHBoxLayout(w); row.setContentsMargins(0,0,0,8); copy=QVBoxLayout(); h=QLabel(title); h.setObjectName("title"); copy.addWidget(h); s=QLabel(subtitle); s.setObjectName("muted"); copy.addWidget(s); row.addLayout(copy); row.addStretch()
            field=QLineEdit() if search else None
            if field: field.setPlaceholderText(f"⌕  Search {title.lower()}…"); field.setMinimumWidth(280); row.addWidget(field)
            return w,field
        def grid(self,cards,cols=3):
            host=QWidget(); grid=QGridLayout(host); grid.setContentsMargins(0,0,5,0); grid.setSpacing(10)
            if not cards:
                empty=QLabel("Nothing to show yet.\nTry changing the filters or adding content."); empty.setObjectName("muted"); empty.setAlignment(Qt.AlignCenter); grid.addWidget(empty,0,0)
            for i,c in enumerate(cards): grid.addWidget(c,i//cols,i%cols)
            grid.setRowStretch((len(cards)+cols-1)//cols,1); area=QScrollArea(); area.setWidgetResizable(True); area.setWidget(host); return area
        def create_page(self):
            page=QWidget(); box=QVBoxLayout(page); head,_=self.header("Create a new image","A simple guided flow for consistent images."); box.addWidget(head)
            steps=QHBoxLayout(); self.create_steps=[]
            for i,name in enumerate(("1  Character","2  Scene","3  Style","4  Preview","5  Generate")):
                button=QPushButton(name); button.setObjectName("step"); button.setCheckable(True); button.clicked.connect(partial(self.show_create_step,i)); self.create_steps.append(button); steps.addWidget(button)
            box.addLayout(steps); self.create_stack=QStackedWidget(); box.addWidget(self.create_stack,1)

            character=QFrame(); character.setObjectName("panel"); cbox=QVBoxLayout(character); cbox.addWidget(QLabel("Choose a character")); create_cards=[]; self.create_character_buttons={}; group=QButtonGroup(self); group.setExclusive(True)
            for c in self.controller.list_characters():
                b=Card(c.identity.name,f"{c.identity.age} · {c.identity.nationality}"," · ".join(c.interests[:2]),reference_image_for(c.character_id)); b.setMinimumSize(145,215); b.clicked.connect(partial(self.choose_character,c.character_id)); group.addButton(b); self.create_character_buttons[c.character_id]=b; create_cards.append(b)
            cbox.addWidget(self.grid(create_cards,3),1); self.idea=QTextEdit(); self.idea.setPlaceholderText("Or describe your idea naturally…\nAyami in a cosy café, drinking coffee and reading a book"); self.idea.setMaximumHeight(82); cbox.addWidget(self.idea); cbox.addWidget(self.next_button("Choose a scene",1)); self.create_stack.addWidget(character)

            scene=QFrame(); scene.setObjectName("panel"); sbox=QVBoxLayout(scene); sbox.addWidget(QLabel("Scene context")); self.create_mode=QComboBox()
            for mode in SCENE_MODES: self.create_mode.addItem(mode.replace("_"," ").title(),mode)
            sbox.addWidget(self.create_mode); sbox.addWidget(QLabel("Optional context overrides")); self.environment_override=QLineEdit(); self.environment_override.setPlaceholderText("Environment, e.g. a quiet independent coffee shop"); self.lighting_override=QLineEdit(); self.lighting_override.setPlaceholderText("Lighting, e.g. soft overcast daylight"); sbox.addWidget(self.environment_override); sbox.addWidget(self.lighting_override)
            sbox.addStretch(); sbox.addWidget(self.next_button("Choose a style",2)); self.create_stack.addWidget(scene)

            style=QFrame(); style.setObjectName("panel"); stbox=QVBoxLayout(style); stbox.addWidget(QLabel("Prompt and execution")); self.adapter_combo=QComboBox(); self.provider_combo=QComboBox(); self.density_combo=QComboBox()
            for adapter in list_adapters(): self.adapter_combo.addItem(adapter.title(),adapter)
            for provider in list_providers(): self.provider_combo.addItem(provider.title(),provider)
            for density in ("compact","standard","detailed"): self.density_combo.addItem(density.title(),density)
            stbox.addWidget(QLabel("Prompt adapter")); stbox.addWidget(self.adapter_combo); stbox.addWidget(QLabel("Image provider")); stbox.addWidget(self.provider_combo); stbox.addWidget(QLabel("Prompt density")); stbox.addWidget(self.density_combo); stbox.addStretch(); preview=QPushButton("Build prompt preview  →"); preview.setObjectName("primary"); preview.clicked.connect(self.resolve_preview); stbox.addWidget(preview); self.create_stack.addWidget(style)

            review=QFrame(); review.setObjectName("panel"); rbox=QHBoxLayout(review); self.prompt_preview=QTextEdit(); self.prompt_preview.setReadOnly(True); rbox.addWidget(self.prompt_preview,3); controls=QVBoxLayout(); controls.addWidget(QLabel("The prompt is built by the authoritative v0.9 pipeline.")); self.prompt_toggle=QPushButton("Show prompt sections"); self.prompt_toggle.clicked.connect(self.toggle_prompt_detail); controls.addWidget(self.prompt_toggle); controls.addStretch(); controls.addWidget(self.next_button("Ready to generate",4)); rbox.addLayout(controls,1); self.create_stack.addWidget(review); self.show_full_prompt=False

            generate=QFrame(); generate.setObjectName("panel"); gbox=QVBoxLayout(generate); self.generate_status=QLabel("Your v0.9 prompt is ready."); self.generate_status.setObjectName("muted"); gbox.addWidget(self.generate_status); self.dry_run=QCheckBox("Dry run — build prompt and output plan only"); gbox.addWidget(self.dry_run); self.generate_button=QPushButton("Generate image  →"); self.generate_button.setObjectName("primary"); self.generate_button.clicked.connect(self.generate_take); gbox.addWidget(self.generate_button); self.take_history=QListWidget(); gbox.addWidget(self.take_history,1); self.create_stack.addWidget(generate)
            self.show_create_step(0); return page

        def next_button(self,label,index):
            button=QPushButton(label+"  →"); button.setObjectName("primary"); button.clicked.connect(partial(self.show_create_step,index)); return button

        def show_create_step(self,index):
            if index>0 and self.controller.character is None:
                QMessageBox.information(self,"Choose a character","Choose a canonical character before continuing."); index=0
            self.create_stack.setCurrentIndex(index)
            for i,button in enumerate(self.create_steps): button.setChecked(i==index); button.setProperty("complete",i<index); button.style().unpolish(button); button.style().polish(button)
            if index==4: self.refresh_history()
        def characters_page(self):
            page=QWidget(); box=QVBoxLayout(page); head,self.character_search=self.header("Characters","Distinct personalities. Unique perspectives.",True); box.addWidget(head); filters=QHBoxLayout(); self.character_filter=QComboBox(); self.character_filter.addItems(("All","Favorites","Region","Occupation","Traits")); self.character_filter_value=QComboBox(); filters.addWidget(self.character_filter); filters.addWidget(self.character_filter_value); filters.addStretch(); box.addLayout(filters); body=QHBoxLayout(); cards=[]; self.characters_data=self.controller.list_characters(); group=QButtonGroup(self); group.setExclusive(True)
            for c in self.characters_data:
                card=Card(c.identity.name,f"{c.identity.age} · {c.identity.nationality}"," · ".join(c.personality[:3]),reference_image_for(c.character_id)); card.clicked.connect(partial(self.choose_character,c.character_id)); group.addButton(card); cards.append(card); self.character_cards[c.character_id]=card
            self.character_search.textChanged.connect(self.apply_character_filter); self.character_filter.currentTextChanged.connect(self.populate_character_filter); self.character_filter_value.currentTextChanged.connect(self.apply_character_filter); body.addWidget(self.grid(cards),3); self.character_preview=Preview(); body.addWidget(self.character_preview,2); box.addLayout(body,1); self.populate_character_filter("All"); return page

        def populate_character_filter(self,mode):
            self.character_filter_value.blockSignals(True); self.character_filter_value.clear()
            if mode=="Region": values=sorted({c.identity.nationality for c in self.characters_data})
            elif mode=="Occupation": values=sorted({c.occupation.primary for c in self.characters_data})
            elif mode=="Traits": values=sorted({trait for c in self.characters_data for trait in c.personality})
            else: values=[]
            self.character_filter_value.addItems(values); self.character_filter_value.setVisible(bool(values)); self.character_filter_value.blockSignals(False); self.apply_character_filter()

        def character_favorites(self): return set(self.preferences.value("characters/favorites",[],type=list))
        def apply_character_filter(self,*_):
            if not hasattr(self,"character_filter"): return
            mode=self.character_filter.currentText(); value=self.character_filter_value.currentText().lower(); needle=self.character_search.text().strip().lower(); favorites=self.character_favorites()
            for c in self.characters_data:
                haystack=" ".join((c.identity.name,c.identity.nationality,c.occupation.primary,*c.personality,*c.interests)).lower(); visible=not needle or needle in haystack
                if mode=="Favorites": visible=visible and c.character_id in favorites
                elif mode=="Region": visible=visible and c.identity.nationality.lower()==value
                elif mode=="Occupation": visible=visible and c.occupation.primary.lower()==value
                elif mode=="Traits": visible=visible and value in (trait.lower() for trait in c.personality)
                self.character_cards[c.character_id].setVisible(visible)
        def choose_character(self,key):
            c=self.controller.choose_character(key); self.selected_character_id=key
            if hasattr(self,"remember") and self.remember.isChecked(): self.preferences.setValue("session/character",key)
            if key in self.character_cards: self.character_cards[key].setChecked(True)
            if key in self.create_character_buttons: self.create_character_buttons[key].setChecked(True)
            if hasattr(self,"character_preview"):
                self.character_preview.show(c.identity.name,f"{c.identity.age} · {c.identity.home}\n\n{c.occupation.primary.title()}\n\n"+", ".join(c.personality)+"\n\nInterests: "+", ".join(c.interests),reference_image_for(key)); use=QPushButton("Use This Character  →"); use.setObjectName("primary"); use.clicked.connect(self.use_selected_character); favorite=QPushButton("Remove favorite" if key in self.character_favorites() else "Add to favorites"); favorite.clicked.connect(self.toggle_character_favorite); self.character_preview.box.addWidget(use); self.character_preview.box.addWidget(favorite); self.character_favorite_button=favorite

        def use_selected_character(self): self.navigate(0); self.show_create_step(1)
        def toggle_character_favorite(self):
            key=getattr(self,"selected_character_id",None)
            if not key: return
            favorites=self.character_favorites()
            if key in favorites: favorites.remove(key)
            else: favorites.add(key)
            self.preferences.setValue("characters/favorites",sorted(favorites)); self.preferences.sync(); self.character_favorite_button.setText("Remove favorite" if key in favorites else "Add to favorites"); self.apply_character_filter()

        def resolve_preview(self):
            try:
                if self.controller.character is None: raise RuntimeError("Choose a canonical character before building a prompt.")
                overrides=self.current_overrides(); self.current_prompt=build_prompt(self.controller.character.character_id,self.create_mode.currentData(),self.adapter_combo.currentData(),self.density_combo.currentData(),overrides)
                if self.remember.isChecked(): self.preferences.setValue("session/mode",self.create_mode.currentData()); self.preferences.setValue("session/adapter",self.adapter_combo.currentData()); self.preferences.setValue("session/provider",self.provider_combo.currentData()); self.preferences.sync()
                self.refresh_preview(); self.show_create_step(3)
            except Exception as exc: QMessageBox.warning(self,"Could not resolve scene",str(exc))

        def current_overrides(self):
            values={"activity":self.idea.toPlainText().strip(),"environment":self.environment_override.text().strip(),"lighting":self.lighting_override.text().strip()}
            return {key:value for key,value in values.items() if value}

        def refresh_preview(self):
            prompt=self.current_prompt
            self.preview_summary=f"PROMPT READY\n\nCharacter: {prompt.character_id}\nMode: {prompt.source_scene_mode}\nAdapter: {prompt.adapter_name}\n\n"+prompt.positive_prompt
            sections="\n\n".join(f"{section.id.upper()}\n{section.text}" for section in prompt.sections)
            self.full_prompt_text=self.preview_summary+"\n\nPROMPT SECTIONS\n\n"+sections+(f"\n\nNEGATIVE / CONSTRAINTS\n\n{prompt.negative_prompt}" if prompt.negative_prompt else "")
            self.prompt_preview.setPlainText(self.full_prompt_text if self.show_full_prompt else self.preview_summary)

        def toggle_prompt_detail(self):
            self.show_full_prompt=not self.show_full_prompt; self.prompt_preview.setPlainText(self.full_prompt_text if self.show_full_prompt else self.preview_summary); self.prompt_toggle.setText("Hide full prompt" if self.show_full_prompt else "View full prompt")

        def generate_take(self):
            try:
                if not hasattr(self,"current_prompt"): self.resolve_preview()
                if not hasattr(self,"current_prompt"): return
                self.generate_status.setText("Generating through the v0.9 pipeline…"); self.generate_button.setEnabled(False); self.worker_thread=QThread(self); self.worker=GenerationWorker(self.controller.character.character_id,self.create_mode.currentData(),self.provider_combo.currentData(),self.adapter_combo.currentData(),self.density_combo.currentData(),self.current_overrides(),self.controller.output_dir,self.dry_run.isChecked()); self.worker.moveToThread(self.worker_thread); self.worker_thread.started.connect(self.worker.run); self.worker.finished.connect(self.generation_finished); self.worker.failed.connect(self.generation_failed); self.worker.finished.connect(self.worker_thread.quit); self.worker.failed.connect(self.worker_thread.quit); self.worker.finished.connect(self.worker.deleteLater); self.worker.failed.connect(self.worker.deleteLater); self.worker_thread.finished.connect(self.worker_thread.deleteLater); self.worker_thread.start()
            except Exception as exc: QMessageBox.warning(self,"Generate",str(exc))

        def generation_finished(self,result):
            self.generate_button.setEnabled(True); self.generate_status.setText(("Dry run planned: " if result.dry_run else "Generated and recorded: ")+ (result.record_id or result.assets[0].file_path)); self.refresh_history(); self.refresh_gallery()
        def generation_failed(self,message): self.generate_button.setEnabled(True); self.generate_status.setText("Generation failed."); QMessageBox.warning(self,"Generation failed",message)
        def refresh_history(self):
            self.take_history.clear()
            for record in list_records(self.controller.output_dir): self.take_history.addItem(f"{record.created_at[:16].replace('T',' ')}  ·  {record.character_id}  ·  {record.provider}")
        def catalog_page(self,title,data):
            page=QWidget(); box=QVBoxLayout(page); head,search=self.header(title,"Visual choices backed by the existing engine.",True); box.addWidget(head); body=QHBoxLayout(); preview=Preview(); cards=[]; group=QButtonGroup(self); group.setExclusive(True)
            for name,value,tags in data:
                card=Card(name,"A friendly creative direction.",tags); card.clicked.connect(partial(self.select_catalog,title,name,value,tags,preview)); group.addButton(card); cards.append(card)
            search.textChanged.connect(lambda t:self.filter(cards,t)); body.addWidget(self.grid(cards,3),4); body.addWidget(preview,2); box.addLayout(body,1); return page
        def select_catalog(self,kind,name,value,tags,preview):
            if kind=="Scenes": self.selected_scene=value; session_key="scene"
            else: self.selected_style=value; session_key="style"
            if hasattr(self,"remember") and self.remember.isChecked(): self.preferences.setValue(f"session/{session_key}",value)
            preview.show(name,tags+"\n\nThis selection maps into the authoritative engine during creation.")
        @staticmethod
        def filter(cards,text):
            needle=text.strip().lower()
            for c in cards: c.setVisible(not needle or needle in c.search)
        def gallery_page(self):
            page=QWidget(); box=QVBoxLayout(page); head,self.gallery_search=self.header("Gallery","Previous creations, ready to revisit.",True); box.addWidget(head); filters=QHBoxLayout(); self.gallery_character=QComboBox(); self.gallery_character.addItem("All characters",None)
            for c in self.controller.list_characters(): self.gallery_character.addItem(c.identity.name,c.character_id)
            self.gallery_favorites=QCheckBox("Favorites only"); filters.addWidget(self.gallery_character); filters.addWidget(self.gallery_favorites); filters.addStretch(); box.addLayout(filters)
            body=QHBoxLayout(); self.gallery_host=QWidget(); self.gallery_grid=QGridLayout(self.gallery_host); self.gallery_grid.setAlignment(Qt.AlignTop); area=QScrollArea(); area.setWidgetResizable(True); area.setWidget(self.gallery_host); body.addWidget(area,4)
            details=QFrame(); details.setObjectName("panel"); self.gallery_detail=QVBoxLayout(details); self.gallery_title=QLabel("Select a creation"); self.gallery_title.setObjectName("previewTitle"); self.gallery_copy=QLabel("Generation details and reuse actions appear here."); self.gallery_copy.setObjectName("muted"); self.gallery_copy.setWordWrap(True); self.gallery_detail.addWidget(self.gallery_title); self.gallery_detail.addWidget(self.gallery_copy); self.gallery_detail.addStretch(); self.use_take=QPushButton("Use in Create  →"); self.use_take.setObjectName("primary"); self.use_take.setEnabled(False); self.use_take.clicked.connect(self.use_selected_take); self.copy_prompt=QPushButton("Copy prompt"); self.copy_prompt.setEnabled(False); self.copy_prompt.clicked.connect(self.copy_selected_prompt); self.favorite_take=QPushButton("Add to favorites"); self.favorite_take.setEnabled(False); self.favorite_take.clicked.connect(self.toggle_favorite); self.gallery_detail.addWidget(self.use_take); self.gallery_detail.addWidget(self.copy_prompt); self.gallery_detail.addWidget(self.favorite_take); body.addWidget(details,2); box.addLayout(body,1)
            self.gallery_search.textChanged.connect(self.refresh_gallery); self.gallery_character.currentIndexChanged.connect(self.refresh_gallery); self.gallery_favorites.toggled.connect(self.refresh_gallery); self.selected_record_id=None; self.refresh_gallery()
            return page

        def favorite_ids(self): return set(self.preferences.value("gallery/favorites",[],type=list))
        def refresh_gallery(self,*_):
            if not hasattr(self,"gallery_grid"): return
            while self.gallery_grid.count():
                item=self.gallery_grid.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            needle=self.gallery_search.text().strip().lower(); character=self.gallery_character.currentData(); favorites=self.favorite_ids(); shown=0
            for record in list_records(self.controller.output_dir):
                if character and record.character_id!=character: continue
                haystack=f"{record.character_id} {record.provider} {record.created_at}".lower()
                if needle and needle not in haystack: continue
                if self.gallery_favorites.isChecked() and record.record_id not in favorites: continue
                title=record.character_id.replace("_"," ").title(); tags=("★  " if record.record_id in favorites else "")+record.provider; card=Card(title,record.created_at[:16].replace("T"," · "),tags); card.setMinimumSize(180,235); card.clicked.connect(partial(self.select_record,record.record_id)); self.gallery_grid.addWidget(card,shown//3,shown%3); shown+=1
            if not shown:
                empty=QLabel("No creations match these filters.\nGenerate a take or broaden the filters."); empty.setObjectName("muted"); empty.setAlignment(Qt.AlignCenter); self.gallery_grid.addWidget(empty,0,0,1,3)

        def select_record(self,record_id):
            try:
                record=load_record(record_id,self.controller.output_dir); self.selected_record_id=record_id
                self.gallery_title.setText(record.record_id[:18]); self.gallery_copy.setText(f"Character: {record.character_id}\nMode: {record.scene_mode}\nAdapter: {record.adapter}\nDensity: {record.density}\nGenerated: {record.created_at[:19].replace('T',' ')}\nProvider: {record.provider}\nAssets: {len(record.assets)}")
                self.use_take.setEnabled(True); self.copy_prompt.setEnabled(True); self.favorite_take.setEnabled(True); self.favorite_take.setText("Remove favorite" if record_id in self.favorite_ids() else "Add to favorites")
            except Exception as exc: QMessageBox.warning(self,"Gallery",str(exc))

        def use_selected_take(self):
            if self.selected_record_id: self.reuse(self.selected_record_id)
        def copy_selected_prompt(self):
            if not self.selected_record_id: return
            QApplication.clipboard().setText(load_record(self.selected_record_id,self.controller.output_dir).positive_prompt); self.statusBar().showMessage("Prompt copied",2500)
        def toggle_favorite(self):
            if not self.selected_record_id: return
            favorites=self.favorite_ids()
            if self.selected_record_id in favorites: favorites.remove(self.selected_record_id)
            else: favorites.add(self.selected_record_id)
            self.preferences.setValue("gallery/favorites",sorted(favorites)); self.preferences.sync(); self.favorite_take.setText("Remove favorite" if self.selected_record_id in favorites else "Add to favorites"); self.refresh_gallery()
        def reuse(self,record_id):
            try:
                record=load_record(record_id,self.controller.output_dir); self.choose_character(record.character_id); self.create_mode.setCurrentIndex(max(0,self.create_mode.findData(record.scene_mode))); self.adapter_combo.setCurrentIndex(max(0,self.adapter_combo.findData(record.adapter))); self.provider_combo.setCurrentIndex(max(0,self.provider_combo.findData(record.provider))); self.density_combo.setCurrentIndex(max(0,self.density_combo.findData(record.density))); self.idea.setPlainText(record.scene_overrides.get("activity","")); self.environment_override.setText(record.scene_overrides.get("environment","")); self.lighting_override.setText(record.scene_overrides.get("lighting","")); self.resolve_preview(); self.navigate(0); self.show_create_step(3)
            except Exception as exc: QMessageBox.warning(self,"CharacterStudio",str(exc))
        def settings_page(self):
            page=QWidget(); box=QVBoxLayout(page); head,_=self.header("Settings","Good defaults first. Configuration when needed."); box.addWidget(head); grid=QGridLayout(); self.setting_controls={}
            groups=(("Appearance",("Theme","Midnight Purple","Density","Comfortable")),("Generation Defaults",("Default character","Random","Default style","Casual")),("File & Storage",("Output folder","project/output","Organisation","Character / Date")),("Image Settings",("Resolution","1024 × 1365","Format","PNG")),("Privacy & Safety",("Processing","Local first","Identity","Protected")),("Advanced",("Configuration","Engine owned","Diagnostics","Available")))
            for i,(title,items) in enumerate(groups):
                panel=QFrame(); panel.setObjectName("panel"); p=QVBoxLayout(panel); h=QLabel(title); h.setObjectName("previewTitle"); p.addWidget(h)
                for label,value in zip(items[::2],items[1::2]): p.addWidget(QLabel(label)); field=QLineEdit(str(self.preferences.value(f"settings/{label}",value))); field.editingFinished.connect(partial(self.persist_setting,label,field)); self.setting_controls[label]=field; p.addWidget(field)
                if title=="Appearance": self.reduced_motion=QCheckBox("Reduce motion"); self.reduced_motion.setChecked(self.preferences.value("appearance/reduced_motion",False,type=bool)); self.reduced_motion.toggled.connect(lambda v:self.preferences.setValue("appearance/reduced_motion",v)); p.addWidget(self.reduced_motion)
                if title=="Generation Defaults": self.remember=QCheckBox("Remember last-used choices"); self.remember.setChecked(self.preferences.value("settings/remember",True,type=bool)); self.remember.toggled.connect(lambda v:self.preferences.setValue("settings/remember",v)); p.addWidget(self.remember)
                p.addStretch(); grid.addWidget(panel,i//3,i%3)
            box.addLayout(grid,1); return page

        def persist_setting(self,key,field):
            self.preferences.setValue(f"settings/{key}",field.text())
            self.preferences.sync()

        def restore_session_preferences(self):
            if not self.preferences.value("settings/remember",True,type=bool): return
            character=self.preferences.value("session/character",None); mode=self.preferences.value("session/mode",None); adapter=self.preferences.value("session/adapter",None); provider=self.preferences.value("session/provider",None)
            if character:
                try: self.choose_character(character)
                except Exception: self.preferences.remove("session/character")
            for combo,value in ((self.create_mode,mode),(self.adapter_combo,adapter),(self.provider_combo,provider)):
                if value:
                    index=combo.findData(value)
                    if index>=0: combo.setCurrentIndex(index)

        def resizeEvent(self,event):
            super().resizeEvent(event)
            if hasattr(self,"side"): self.side.setFixedWidth(230 if self.width()<1250 else 285)
            if hasattr(self,"character_preview"): self.character_preview.setVisible(self.width()>=1180)

def main():
    if PYSIDE_ERROR is not None: print("PySide6 is required. Install: pip install -e .[desktop]",file=sys.stderr); return 2
    app=QApplication(sys.argv); window=DesktopWindow(); window.show(); return app.exec()
if __name__=="__main__": raise SystemExit(main())
