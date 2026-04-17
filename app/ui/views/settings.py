"""SettingsView: Application settings for language and theme."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from app.ui.styles.settings import SETTINGS_STYLES
from app.utils.settings import get_language, set_language
from app.utils.ui_helpers import build_header
from translations.translation import get_translation_manager, translate
from app.core.registry import registry

from app.utils.logger import get_logger
logger = get_logger(__name__)


class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsView")
        self.setStyleSheet(SETTINGS_STYLES)
        self._build_ui()
        self._sync_language_buttons()
        self._retranslate_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(25, 30, 25, 80)
        root.setSpacing(28)

        header, self._page_title_lbl, self._page_subtitle_lbl = build_header(
            "Settings",
            "Customize your application preferences"
        )
        root.addWidget(header)
        
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        self._language_card = self._build_language_card()
        self._theme_card = self._build_theme_card()

        cards_layout.addWidget(self._language_card)
        cards_layout.addWidget(self._theme_card)
        cards_layout.addStretch()
        root.addLayout(cards_layout)

        root.addStretch()

    def _build_language_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("settingsCard")
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        self._lang_title_lbl = QLabel("")
        self._lang_title_lbl.setObjectName("settingsCardTitle")
        layout.addWidget(self._lang_title_lbl)

        self._lang_desc_lbl = QLabel("")
        self._lang_desc_lbl.setObjectName("settingsCardDescription")
        layout.addWidget(self._lang_desc_lbl)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.setContentsMargins(0, 0, 0, 0)

        self._lang_sk_btn = QPushButton("sk")
        self._lang_sk_btn.setObjectName("langBtn")
        self._lang_sk_btn.setProperty("active", "false")
        self._lang_sk_btn.clicked.connect(lambda: self._change_language("sk"))

        self._lang_en_btn = QPushButton("en")
        self._lang_en_btn.setObjectName("langBtn")
        self._lang_en_btn.setProperty("active", "false")
        self._lang_en_btn.clicked.connect(lambda: self._change_language("en"))

        btn_row.addWidget(self._lang_sk_btn)
        btn_row.addWidget(self._lang_en_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        return card

    def _build_theme_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("settingsCard")
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        self._theme_title_lbl = QLabel("")
        self._theme_title_lbl.setObjectName("settingsCardTitle")
        layout.addWidget(self._theme_title_lbl)

        self._theme_desc_lbl = QLabel("")
        self._theme_desc_lbl.setObjectName("settingsCardDescription")
        layout.addWidget(self._theme_desc_lbl)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.setContentsMargins(0, 0, 0, 0)

        self._theme_dark_btn = QPushButton("")
        self._theme_dark_btn.setObjectName("themeBtn")
        self._theme_dark_btn.setProperty("active", "true")

        self._theme_light_btn = QPushButton("")
        self._theme_light_btn.setObjectName("themeBtn")
        self._theme_light_btn.setProperty("active", "false")
        self._theme_light_btn.setEnabled(False)

        btn_row.addWidget(self._theme_dark_btn)
        btn_row.addWidget(self._theme_light_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        return card

    def _change_language(self, lang: str) -> None:
        set_language(lang)
        get_translation_manager().switch_language(lang)
        self._sync_language_buttons()
        self._retranslate_ui()
        logger.info("Language changed to %s", lang)

        from app.service.auth_service import sync_user_language

        def _on_sync_finished(_result) -> None:
            logger.debug("sync-language-thread finished")

        started = registry.operation("sync-language-thread").start(
            registry.run_thread,
            lambda: sync_user_language(lang),
            _on_sync_finished,
            name="sync-language-thread",
        )
        if started:
            logger.debug("sync-language-thread started")
        else:
            logger.debug("sync-language-thread already running, skipped")

    def _sync_language_buttons(self) -> None:
        current = get_language()
        for btn, code in ((self._lang_sk_btn, "sk"), (self._lang_en_btn, "en")):
            active = current == code
            btn.setProperty("active", "true" if active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()

    def _retranslate_ui(self) -> None:
        self._page_title_lbl.setText(translate("SettingsView", "Settings"))
        self._page_subtitle_lbl.setText(
            translate("SettingsView", "Customize your application preferences")
        )

        self._lang_title_lbl.setText(translate("SettingsView", "Language"))
        self._lang_desc_lbl.setText(
            translate("SettingsView", "Select your preferred language")
        )

        self._theme_title_lbl.setText(translate("SettingsView", "Theme"))
        self._theme_desc_lbl.setText(
            translate("SettingsView", "Choose the application appearance")
        )
        self._theme_dark_btn.setText(translate("SettingsView", "Dark"))
        self._theme_light_btn.setText(translate("SettingsView", "Light"))

    def changeEvent(self, event):
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.Type.LanguageChange:
            self._sync_language_buttons()
            self._retranslate_ui()
        super().changeEvent(event)
