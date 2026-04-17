from __future__ import annotations

import re
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, QSize
from PySide6.QtGui import QIcon, QPixmap, QDesktopServices
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QTextEdit, QWidget, QScrollArea, QStackedWidget


from app.utils.logger import get_logger

logger = get_logger(__name__)
from app.utils.settings import get_language
from app.utils.ui_helpers import build_header
from translations.translation import translate


BUILT_WITH = [
    ("Python", "3.12"),
    ("PySide6", "UI framework"),
    ("Supabase", "2.28.0"),
]

def get_project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent.parent.parent

def _parse_all_changelogs() -> list[dict]:
    root = get_project_root()
    lang = get_language()
    localized_path = root / f"CHANGELOG.{lang}.md"
    default_path = root / "CHANGELOG.md"

    changelog_path = localized_path if localized_path.exists() else default_path

    try:
        content = changelog_path.read_text(encoding="utf-8")

        version_matches = list(
            re.finditer(r"^##\s+v(\d+\.\d+\.\d+)\s*$", content, re.MULTILINE)
        )

        if not version_matches:
            return []

        results = []

        for i, match in enumerate(version_matches):
            start = match.end()
            end = version_matches[i + 1].start() if i + 1 < len(version_matches) else len(content)
            block = content[start:end].strip()

            version = match.group(1).strip()
            date = None
            summary_lines = []
            sections: dict[str, list[str]] = {}
            current_section = None

            for raw_line in block.splitlines():
                line = raw_line.strip()

                if not line:
                    continue

                date_match = re.match(r"^(\d{4}-\d{2}-\d{2})$", line)
                if date_match and date is None:
                    date = date_match.group(1)
                    continue

                section_match = re.match(r"^###\s+(.+)$", line)
                if section_match:
                    current_section = section_match.group(1).strip()
                    sections[current_section] = []
                    continue

                item_match = re.match(r"^-\s+(.+)$", line)
                if item_match and current_section:
                    sections[current_section].append(item_match.group(1).strip())
                    continue

                if current_section is None:
                    summary_lines.append(line)

            results.append(
                {
                    "version": version,
                    "date": date,
                    "summary": " ".join(summary_lines).strip() or None,
                    "sections": sections,
                }
            )

        return results

    except Exception:
        logger.exception("Error parsing changelog")
        return []


class AboutView(QWidget):
    def __init__(self, user_id: str, parent=None):
        super().__init__(parent)
        self.setObjectName("aboutView")
        self.user_id = user_id
        self._build_ui()
        self._retranslate_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(25, 30, 25, 80)
        root.setSpacing(30)

        header, self._page_title_lbl, self._page_subtitle_lbl = build_header(
            "About",
            "Learn more about the application and its development"
        )
        root.addWidget(header)

        main_row = QHBoxLayout()
        main_row.setSpacing(40)
        main_row.setContentsMargins(0, 0, 0, 0)
        main_row.setAlignment(Qt.AlignmentFlag.AlignTop)

        left_col_widget = QWidget()
        self._left_col_layout = QVBoxLayout(left_col_widget)
        self._left_col_layout.setContentsMargins(0, 0, 0, 0)
        self._left_col_layout.setSpacing(20)
        self._left_col_layout.addWidget(self._build_about_card())
        self._left_col_layout.addWidget(self._build_changelog_card())
        self._left_col_layout.addStretch()

        right_col_widget = QWidget()
        right_col_layout = QVBoxLayout(right_col_widget)
        right_col_layout.setContentsMargins(0, 0, 0, 0)
        right_col_layout.setSpacing(20)
        right_col_layout.addWidget(self._build_built_with_card())
        right_col_layout.addWidget(self._build_sponsor_card())
        right_col_layout.addWidget(self._build_report_card())
        right_col_layout.addStretch()

        main_row.addWidget(left_col_widget, 2)
        main_row.addWidget(right_col_widget, 1)
        main_row.addStretch()

        root.addLayout(main_row)
        root.addStretch()

    def _build_about_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("aboutCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setMinimumWidth(360)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        self._intro_title_lbl = QLabel("")
        self._intro_title_lbl.setObjectName("aboutCardTitle")
        layout.addWidget(self._intro_title_lbl)

        layout.addWidget(self._make_divider())

        self._desc_lbl = QLabel("")
        self._desc_lbl.setObjectName("aboutDescriptionText")
        self._desc_lbl.setWordWrap(True)
        self._desc_lbl.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self._desc_lbl)

        layout.addStretch()
        return card

    def _build_changelog_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("aboutCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        card.setMinimumWidth(360)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        all_changelogs = _parse_all_changelogs()

        header_row = QWidget()
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        title_wrap = QVBoxLayout()
        title_wrap.setContentsMargins(0, 0, 0, 0)
        title_wrap.setSpacing(2)

        self._changelog_title_lbl = QLabel("")
        self._changelog_title_lbl.setObjectName("aboutCardTitle")
        title_wrap.addWidget(self._changelog_title_lbl)

        version_combo = QComboBox()
        version_combo.setObjectName("changelogCombo")
        for entry in all_changelogs:
            version_combo.addItem(f"v{entry['version']}")

        header_layout.addLayout(title_wrap, 1)
        header_layout.addWidget(version_combo, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(header_row)

        stack = QStackedWidget()
        stack.setMinimumHeight(180)

        for entry in all_changelogs:
            page = self._build_changelog_page(entry)
            stack.addWidget(page)

        if not all_changelogs:
            empty_lbl = QLabel("No changelog entries found.")
            empty_lbl.setObjectName("aboutMetaText")
            layout.addWidget(empty_lbl)
        else:
            version_combo.currentIndexChanged.connect(stack.setCurrentIndex)
            layout.addWidget(stack)

        return card

    def _build_changelog_page(self, entry: dict) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("changelogScroll")

        container = QWidget()
        container.setObjectName("changelogScrollContent")
        inner = QVBoxLayout(container)
        inner.setContentsMargins(0, 0, 8, 0)
        inner.setSpacing(10)

        if entry["date"]:
            date_lbl = QLabel(entry["date"])
            date_lbl.setObjectName("aboutMetaText")
            inner.addWidget(date_lbl)

        if entry["summary"]:
            summary_lbl = QLabel(entry["summary"])
            summary_lbl.setObjectName("aboutMetaText")
            summary_lbl.setWordWrap(True)
            inner.addWidget(summary_lbl)

        section_order = ["Added", "Changed", "Improved", "Fixed", "Removed"]
        ordered_keys = [k for k in section_order if k in entry["sections"]]
        ordered_keys += [k for k in entry["sections"] if k not in ordered_keys]

        for section_name in ordered_keys:
            items = entry["sections"].get(section_name, [])
            if not items:
                continue
            inner.addWidget(self._build_changelog_section(section_name, items))

        if not entry["summary"] and not entry["sections"]:
            empty_lbl = QLabel("No detailed release notes.")
            empty_lbl.setObjectName("aboutMetaText")
            inner.addWidget(empty_lbl)

        inner.addStretch()
        scroll.setWidget(container)
        return scroll

    def _build_changelog_section(self, title: str, items: list[str]) -> QWidget:
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(6)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("aboutSectionTitle")
        section_layout.addWidget(title_lbl)

        for item in items:
            item_wrap = QWidget()
            item_row = QHBoxLayout(item_wrap)
            item_row.setContentsMargins(4, 0, 0, 0)
            item_row.setSpacing(8)

            bullet = QLabel("•")
            bullet.setObjectName("changelogBullet")
            bullet.setFixedWidth(10)

            text = QLabel(item)
            text.setObjectName("aboutMetaText")
            text.setWordWrap(True)

            item_row.addWidget(bullet, 0, Qt.AlignmentFlag.AlignTop)
            item_row.addWidget(text, 1)
            section_layout.addWidget(item_wrap)

        return section

    def _build_report_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("aboutCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setMinimumWidth(360)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        self._report_card_title_lbl = QLabel("")
        self._report_card_title_lbl.setObjectName("aboutCardTitle")
        layout.addWidget(self._report_card_title_lbl)

        self._report_hint_lbl = QLabel("")
        self._report_hint_lbl.setObjectName("aboutMetaText")
        self._report_hint_lbl.setWordWrap(True)
        layout.addWidget(self._report_hint_lbl)

        self._report_editor = QTextEdit()
        self._report_editor.setObjectName("reportEditor")
        self._report_editor.setFixedHeight(80)
        layout.addWidget(self._report_editor)

        btn_row = QWidget()
        row = QHBoxLayout(btn_row)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        self._report_send_btn = QPushButton("")
        self._report_send_btn.setObjectName("reportSendButton")

        def _reset_send_btn():
            self._report_send_btn.setEnabled(True)
            self._report_editor.setReadOnly(False)
            self._report_editor.clear()

        def _send():
            body = self._report_editor.toPlainText().strip()
            if not body:
                return

            from app.service.report_service import submit_report

            saved = submit_report(self.user_id, body)
            if saved:
                self._report_editor.setPlainText(
                    translate("AboutView", "Your report was successfully sent. Thank you!")
                )
                self._report_editor.setReadOnly(True)
                self._report_send_btn.setEnabled(False)
                QTimer.singleShot(3000, _reset_send_btn)
                logger.info("Report submitted successfully")
            else:
                logger.error("Failed to submit report")

        self._report_send_btn.clicked.connect(_send)

        row.addWidget(self._report_send_btn)
        row.addStretch()
        layout.addWidget(btn_row)

        return card

    def _build_built_with_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("aboutCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setMinimumWidth(360)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        self._built_with_title_lbl = QLabel("")
        self._built_with_title_lbl.setObjectName("aboutCardTitle")
        layout.addWidget(self._built_with_title_lbl)

        for name, desc in BUILT_WITH:
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(10)

            dot = QLabel("·")
            dot.setObjectName("builtWithDot")
            dot.setFixedWidth(12)

            name_lbl = QLabel(name)
            name_lbl.setObjectName("builtWithName")
            name_lbl.setFixedWidth(90)

            desc_lbl = QLabel(desc)
            desc_lbl.setObjectName("builtWithDesc")

            row.addWidget(dot)
            row.addWidget(name_lbl)
            row.addWidget(desc_lbl)
            row.addStretch()
            layout.addWidget(row_widget)

        return card

    def _build_sponsor_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("aboutCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setMinimumWidth(360)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        self._sponsor_title_lbl = QLabel("")
        self._sponsor_title_lbl.setObjectName("aboutCardTitle")
        layout.addWidget(self._sponsor_title_lbl)

        self._sponsor_desc_lbl = QLabel("")
        self._sponsor_desc_lbl.setObjectName("aboutMetaText")
        self._sponsor_desc_lbl.setWordWrap(True)
        layout.addWidget(self._sponsor_desc_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.setContentsMargins(0, 0, 0, 0)

        kofi_btn = QPushButton(" Ko-fi")
        kofi_btn.setObjectName("kofiButton")
        kofi_btn.setIcon(QIcon(QPixmap(":/images/graphics/kofiLogo.png").scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
        kofi_btn.setIconSize(QSize(18, 18))
        kofi_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        kofi_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        kofi_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://ko-fi.com/wrexik")))

        github_btn = QPushButton("GitHub")
        github_btn.setObjectName("githubSponsorButton")
        github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/wrex1k/Synapso")))

        btn_row.addWidget(kofi_btn)
        btn_row.addWidget(github_btn)
        layout.addLayout(btn_row)

        return card

    def _rebuild_changelog(self) -> None:
        old = self._left_col_layout.itemAt(1).widget()
        if old is not None:
            self._left_col_layout.removeWidget(old)
            old.deleteLater()

        new_card = self._build_changelog_card()
        self._left_col_layout.insertWidget(1, new_card)

    def _retranslate_ui(self) -> None:
        self._page_title_lbl.setText(translate("AboutView", "About"))
        self._page_subtitle_lbl.setText(
            translate("AboutView", "App information and release notes")
        )
        self._intro_title_lbl.setText(translate("AboutView", "What is Synapso"))
        self._desc_lbl.setText(
            translate(
                "AboutView",
                "<b>Synapso</b> is a cognitive training app designed to improve memory, attention, focus, "
                "and mental flexibility through interactive brain games.<br><br>"
                "<b>Games:</b><br>"
                "\u2022 <b>Stroop Test</b> \u2014 Enhance focus and cognitive control<br>"
                "\u2022 <b>Memory Grid</b> \u2014 Train working memory with pattern recall<br>"
                "\u2022 <b>Mental Rotation</b> \u2014 Improve spatial reasoning<br><br>"
                "Track your performance, monitor progress, and train your brain consistently.",
            )
        )
        self._changelog_title_lbl.setText(translate("AboutView", "Changelog"))
        self._built_with_title_lbl.setText(translate("AboutView", "Built with"))
        self._sponsor_title_lbl.setText(translate("AboutView", "Support the project"))
        self._sponsor_desc_lbl.setText(
            translate("AboutView", "If you like Synapso, consider supporting the project.")
        )
        self._report_card_title_lbl.setText(translate("AboutView", "Report a bug"))
        self._report_hint_lbl.setText(
            translate("AboutView", "Describe the issue and include steps to reproduce.")
        )
        self._report_editor.setPlaceholderText(
            translate("AboutView", "Write your bug report here...")
        )
        self._report_send_btn.setText(translate("AboutView", "Send report"))

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._rebuild_changelog()
        self._retranslate_ui()

    @staticmethod
    def _make_divider() -> QFrame:
        line = QFrame()
        line.setObjectName("aboutDivider")
        line.setFrameShape(QFrame.Shape.HLine)
        return line