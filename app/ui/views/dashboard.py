"""DashboardView: Non-scrollable overview page with quick activity and progress summary."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import QMargins, QPointF, Qt, QThread, Signal, QEvent
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QFrame,
)

from app.core.registry import registry
from app.games.core.base_game import GAME_ID_MAP
from app.models.user import User
from app.repository.activity_repository import get_time_played
from app.repository.run_repository import fetch_user_run_history
from app.repository.stats_repository import fetch_all_user_stats, fetch_player_game_stats
from app.ui.styles.colors import PRIMARY_LIGHT
from app.ui.styles.dashboard import DASHBOARD_STYLES
from app.ui.styles.fonts import DASHBOARD_FONT_STYLES
from app.utils.logger import get_logger
from app.utils.ui_helpers import build_header
from translations.translation import translate

logger = get_logger(__name__)

_ACCENT = "#3EAC91"
_TEXT_GRAY = "#A9A9A9"
_SUCCESS = "#12A54C"
_WARNING = "#E7A93C"

_GAME_SLUGS = ["stroop", "memory_grid", "mental_rotation"]
_GAME_LABELS = {
    "stroop": "Stroop",
    "memory_grid": "Memory Grid",
    "mental_rotation": "Mental Rotation",
}
_GAME_DESCRIPTIONS = {
    "stroop": "Stroop color and word test",
    "memory_grid": "Memory Grid Test",
    "mental_rotation": "Mental Rotation Test",
}
_MIN_UTC = datetime.min.replace(tzinfo=timezone.utc)


def _create_chart_view(chart: QChart) -> QChartView:
    view = QChartView(chart)
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    view.setBackgroundBrush(QBrush(QColor(0, 0, 0, 0)))
    view.setAutoFillBackground(False)
    view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    view.viewport().setAutoFillBackground(False)
    view.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    view.setStyleSheet("background: transparent; border: none;")
    return view


def _setup_chart() -> QChart:
    chart = QChart()
    chart.setBackgroundVisible(False)
    chart.setPlotAreaBackgroundVisible(False)
    chart.setBackgroundBrush(QBrush(QColor(0, 0, 0, 0)))
    chart.setMargins(QMargins(0, 0, 0, 0))
    chart.legend().setVisible(False)
    return chart


def _value_axis(label: str = "", tick_count: int = 6) -> QValueAxis:
    axis = QValueAxis()
    axis.setLabelsColor(QColor(_TEXT_GRAY))
    axis.setLabelsFont(QFont("General Sans", 9))
    axis.setGridLineColor(QColor(255, 255, 255, 12))
    axis.setLinePenColor(QColor(255, 255, 255, 18))
    axis.setTickCount(max(2, tick_count))
    axis.setMinorTickCount(0)
    if label:
        axis.setTitleText(label)
        axis.setTitleBrush(QColor(_TEXT_GRAY))
        axis.setTitleFont(QFont("General Sans", 10))
    return axis


class DashboardView(QWidget):
    continue_game_requested = Signal(str)

    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardView")
        self.setStyleSheet(DASHBOARD_FONT_STYLES + DASHBOARD_STYLES)

        self._user = user
        self._threads: list[QThread] = []
        self._chart_refs: list = []
        self._loaded_once = False

        self._time_played_total: int = 0
        self._all_stats: dict = {"games": []}
        self._per_game: dict[str, dict | None] = {}
        self._run_histories: dict[str, list[dict]] = {}

        self._welcome_refs: dict[str, QLabel] = {}
        self._activity_refs: dict[str, QLabel] = {}
        self._highlight_refs: dict[str, QLabel] = {}
        self._continue_labels: dict[str, QLabel] = {}
        self._continue_play_btn: QPushButton | None = None
        self._current_continue_slug: str | None = None

        self._most_played_title_label: QLabel | None = None
        self._trend_chart_layout: QVBoxLayout | None = None
        self._recent_games_layout: QVBoxLayout | None = None

        logger.debug(
            "DashboardView initialized: user_id=%s username=%s",
            getattr(self._user, "id", None),
            getattr(self._user, "username", None),
        )

        self._build_ui()

    def _build_ui(self) -> None:
        logger.debug("DashboardView._build_ui: building dashboard UI")

        root = QVBoxLayout(self)
        root.setContentsMargins(25, 30, 25, 60)
        root.setSpacing(28)

        header, self._page_title_lbl, self._page_subtitle_lbl = build_header(
            translate("DashboardView", "Dashboard"),
            translate("DashboardView", "Your activity overview and quick access to continue training"),
        )
        root.addWidget(header)

        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.addWidget(self._build_welcome_card(), 2)
        top_row.addWidget(self._build_goal_card(), 1)
        root.addLayout(top_row)

        middle_row = QHBoxLayout()
        middle_row.setSpacing(20)
        middle_row.setContentsMargins(0, 0, 0, 0)
        middle_row.addWidget(self._build_activity_card(), 1)
        middle_row.addWidget(self._build_most_played_chart_card(), 2)
        middle_row.addWidget(self._build_highlights_card(), 1)
        root.addLayout(middle_row, 1)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.addWidget(self._build_recent_games_card(), 2)
        bottom_row.addWidget(self._build_continue_card(), 1)
        root.addLayout(bottom_row)

        logger.debug(
            "DashboardView._build_ui: UI build complete welcome_refs=%s activity_refs=%s highlight_refs=%s",
            list(self._welcome_refs.keys()),
            list(self._activity_refs.keys()),
            list(self._highlight_refs.keys()),
        )

    def _build_welcome_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("dashboardHeroCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(10)

        username = getattr(self._user, "username", None) or translate("DashboardView", "Player")

        title = QLabel(
            f"{translate('DashboardView', 'Welcome back,')} "
            f"<span style='color: {PRIMARY_LIGHT};'>{username}</span>"
        )
        title.setObjectName("dashboardHeroTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        subtitle = QLabel(
            translate("DashboardView", "Are you ready for another training session?")
        )
        subtitle.setObjectName("dashboardCardSubtitle")
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignLeft)

        stats_wrapper = QWidget()
        stats_wrapper.setObjectName("dashboardHeroStatsWrapper")
        # Allow the stats wrapper to expand so items can be spaced with stretches
        stats_wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        stats_row = QHBoxLayout(stats_wrapper)
        # keep the same top spacing but use full available width inside the card
        stats_row.setContentsMargins(0, 8, 0, 0)
        stats_row.setSpacing(0)

        stats_row.addWidget(self._build_inline_stat(translate("DashboardView", "Current streak"), "—", "current_streak"))
        stats_row.addStretch()
        stats_row.addWidget(self._build_inline_stat(translate("DashboardView", "Weekly play time"), "—", "weekly_play_time"))
        stats_row.addStretch()
        stats_row.addWidget(self._build_inline_stat(translate("DashboardView", "Runs this week"), "—", "sessions_this_week"))
        stats_row.addStretch()
        stats_row.addWidget(self._build_inline_stat(translate("DashboardView", "Favorite game"), "—", "favorite_game"))

        layout.addWidget(title)
        layout.addWidget(subtitle)
        # horizontal divider between subtitle and stats
        divider = QFrame()
        divider.setObjectName("dashboardDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(divider)
        # add stats wrapper normally so it spans the card's content area (margins already set on the card)
        layout.addWidget(stats_wrapper)

        return card

    def _build_goal_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("dashboardSideCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(10)

        title = QLabel(translate("DashboardView", "Daily Goal"))
        title.setObjectName("dashboardCardTitle")

        self._goal_progress_value = QLabel("—")
        self._goal_progress_value.setObjectName("dashboardGoalValue")

        self._goal_hint = QLabel("")
        self._goal_hint.setObjectName("dashboardMutedText")
        self._goal_hint.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(self._goal_progress_value)
        layout.addWidget(self._goal_hint)
        return card

    def _build_activity_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("dashboardCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        title = QLabel(translate("DashboardView", "Activity"))
        title.setObjectName("dashboardCardTitle")

        layout.addWidget(title)
        layout.addWidget(self._build_metric_row(translate("DashboardView", "Total runs"), "—", "total_runs"))
        layout.addWidget(self._build_metric_row(translate("DashboardView", "Total trials"), "—", "total_trials"))
        layout.addWidget(self._build_metric_row(translate("DashboardView", "Current streak"), "—", "current_streak"))
        layout.addWidget(self._build_metric_row(translate("DashboardView", "Time played"), "—", "time_played"))
        layout.addStretch()
        return card

    def _build_most_played_chart_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("dashboardCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(10)

        title = QLabel(translate("DashboardView", "Favorite Game"))
        title.setObjectName("dashboardCardTitle")

        header_row.addWidget(title)
        header_row.addStretch()

        chart_placeholder = QWidget()
        chart_placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._trend_chart_layout = QVBoxLayout(chart_placeholder)
        self._trend_chart_layout.setContentsMargins(0, 0, 0, 0)

        empty = QLabel(translate("DashboardView", "Loading..."))
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.setObjectName("dashboardCardSubtitle")
        self._trend_chart_layout.addWidget(empty)

        layout.addLayout(header_row)
        layout.addWidget(chart_placeholder, 1)
        return card

    def _build_continue_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("dashboardCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        title = QLabel(translate("DashboardView", "Latest Training"))
        title.setObjectName("dashboardCardTitle")

        self._continue_labels["game_name"] = QLabel("—")
        self._continue_labels["game_name"].setObjectName("dashboardHighlightValue")

        self._continue_labels["info"] = QLabel("—")
        self._continue_labels["info"].setObjectName("dashboardMutedText")

        self._continue_play_btn = QPushButton(translate("DashboardView", "Play again"))
        self._continue_play_btn.setObjectName("dashboardPrimaryButton")
        self._continue_play_btn.setEnabled(False)
        self._continue_play_btn.clicked.connect(self._emit_continue_requested)

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self._continue_labels["game_name"])
        layout.addWidget(self._continue_labels["info"])
        layout.addStretch()
        layout.addWidget(self._continue_play_btn)
        return card

    def _build_recent_games_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("dashboardCard")
        # Responsive: allow the card to expand vertically instead of forcing a minimum height
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)

        title = QLabel(translate("DashboardView", "Recent Games"))
        title.setObjectName("dashboardCardTitle")

        self._recent_games_container = QWidget()
        self._recent_games_layout = QVBoxLayout(self._recent_games_container)
        self._recent_games_layout.setContentsMargins(0, 0, 0, 0)
        self._recent_games_layout.setSpacing(60)

        empty = QLabel(translate("DashboardView", "Loading..."))
        empty.setObjectName("dashboardCardSubtitle")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._recent_games_layout.addWidget(empty)

        layout.addWidget(title)
        layout.addWidget(self._recent_games_container)
        layout.addStretch()
        return card

    def _build_highlights_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("dashboardCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(8)

        title = QLabel(translate("DashboardView", "Highlights"))
        title.setObjectName("dashboardCardTitle")

        w, value = self._build_badge_row(translate("DashboardView", "Best accuracy"), "—", _SUCCESS)
        self._highlight_refs["best_accuracy"] = value

        w2, value2 = self._build_badge_row(translate("DashboardView", "Fastest reaction"), "—", _ACCENT)
        self._highlight_refs["fastest_reaction"] = value2

        layout.addWidget(title)
        layout.addWidget(w)
        layout.addWidget(w2)
        layout.addStretch()
        return card

    def _build_inline_stat(self, label_text: str, value_text: str, key: str) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        value = QLabel(value_text)
        value.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        value.setObjectName("dashboardInlineStatValue")
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        label.setObjectName("dashboardInlineStatLabel")

        layout.addWidget(value)
        layout.addWidget(label)
        self._welcome_refs[key] = value
        return wrapper

    def _build_metric_row(self, label_text: str, value_text: str, key: str) -> QWidget:
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 2, 0, 2)
        row_layout.setSpacing(0)

        label = QLabel(label_text)
        label.setObjectName("dashboardMetricLabel")

        value = QLabel(value_text)
        value.setObjectName("dashboardMetricValue")

        row_layout.addWidget(label)
        row_layout.addStretch()
        row_layout.addWidget(value)
        self._activity_refs[key] = value
        return row_widget

    def _build_badge_row(self, label_text: str, value_text: str, color: str) -> tuple[QWidget, QLabel]:
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 4, 0, 4)
        row_layout.setSpacing(10)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 12px;")

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        label = QLabel(label_text)
        label.setObjectName("dashboardRowTitle")

        value = QLabel(value_text)
        value.setObjectName("dashboardRowSubtitle")

        text_col.addWidget(label)
        text_col.addWidget(value)

        row_layout.addWidget(dot)
        row_layout.addLayout(text_col)
        row_layout.addStretch()
        return row, value

    def _build_recent_game_row(self, game_text: str, date_text: str, pi_text: str) -> QWidget:
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 6, 0, 6)
        row_layout.setSpacing(0)

        left_col = QHBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(10)

        game_lbl = QLabel(game_text)
        game_lbl.setObjectName("dashboardRowTitle")

        date_lbl = QLabel(date_text)
        date_lbl.setObjectName("dashboardRowSubtitle")
        date_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        value_lbl = QLabel(pi_text)
        value_lbl.setObjectName("dashboardRowValue")
        value_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        left_col.addWidget(game_lbl)
        left_col.addWidget(date_lbl)
        row_layout.addLayout(left_col)
        row_layout.addStretch()
        row_layout.addWidget(value_lbl)
        return row

    def _build_recent_game_tile(self, game_text: str, date_text: str, pi_text: str) -> QWidget:
        """Build a centered tile: game title above date (and PI) stacked vertically."""
        tile = QWidget()
        layout = QVBoxLayout(tile)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        title = QLabel(game_text)
        title.setObjectName("recentGameTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        date_lbl = QLabel(date_text)
        date_lbl.setObjectName("recentGameSubtitle")
        date_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pi_lbl = QLabel(pi_text)
        pi_lbl.setObjectName("recentGameValue")
        pi_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tile.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(date_lbl)
        layout.addWidget(pi_lbl)
        layout.addStretch()
        return tile

    def showEvent(self, event):
        super().showEvent(event)
        logger.debug(
            "DashboardView.showEvent: loaded_once=%s visible=%s user_id=%s",
            self._loaded_once,
            self.isVisible(),
            getattr(self._user, "id", None),
        )
        if not self._loaded_once:
            self._loaded_once = True
            logger.debug("DashboardView.showEvent: first show -> triggering _load_data()")
            self._load_data()
        else:
            running = any(getattr(t, "isRunning", lambda: False)() for t in self._threads)
            """ # Refresh data whenever the dashboard becomes visible again (e.g., after a game session)
            # but avoid spawning redundant background fetches when one is already running.
            if running:
                logger.debug("DashboardView.showEvent: fetch already running, skipping refresh")
            else:
                logger.debug("DashboardView.showEvent: visible again -> refreshing data")
                self._load_data() """

    def changeEvent(self, event) -> None:
        super().changeEvent(event)

        if event.type() != QEvent.LanguageChange:
            return

        try:
            logger.debug("DashboardView.changeEvent: LanguageChange received, retranslating UI")
            self._retranslate_ui()
        except Exception:
            logger.exception("DashboardView.changeEvent: failed while handling language change")


    def _retranslate_ui(self) -> None:
        try:
            self._set_text_if_exists(
                "_page_title_lbl",
                translate("DashboardView", "Dashboard"),
            )
            self._set_text_if_exists(
                "_page_subtitle_lbl",
                translate(
                    "DashboardView",
                    "Your activity overview",
                ),
            )
            self._set_text_if_exists(
                "_continue_play_btn",
                translate("DashboardView", "Play again"),
            )

            self._update_first_label(
                "dashboardCardSubtitle",
                translate("DashboardView", "Are you ready for another training session?"),
            )

            self._update_labels(
                "dashboardInlineStatLabel",
                [
                    "Current streak",
                    "Weekly play time",
                    "Runs this week",
                    "Favorite game",
                ],
            )

            self._update_card_titles(
                {
                    "Daily Goal": "Daily Goal",
                    "Activity": "Activity",
                    "Favorite game": "Favorite game",
                    "Latest Training": "Latest Training",
                    "Recent Games": "Recent Games",
                    "Highlights": "Highlights",
                }
            )

            self._refresh_dashboard_sections()

        except Exception:
            logger.exception("DashboardView._retranslate_ui: unexpected error")


    def _set_text_if_exists(self, attr_name: str, text: str) -> None:
        widget = getattr(self, attr_name, None)
        if widget is not None:
            widget.setText(text)


    def _update_first_label(self, object_name: str, text: str) -> None:
        labels = self.findChildren(QLabel, object_name)
        if labels:
            labels[0].setText(text)


    def _update_labels(self, object_name: str, keys: list[str]) -> None:
        labels = self.findChildren(QLabel, object_name)
        for label, key in zip(labels, keys):
            label.setText(translate("DashboardView", key))


    def _update_card_titles(self, mapping: dict[str, str]) -> None:
        titles = self.findChildren(QLabel, "dashboardCardTitle")
        for title in titles:
            current_text = title.text() or ""
            for needle, key in mapping.items():
                if needle in current_text:
                    title.setText(translate("DashboardView", key))
                    break


    def _refresh_dashboard_sections(self) -> None:
        for fn in (
            self._populate_welcome,
            self._populate_activity,
            self._populate_recent_games,
            self._populate_trend_chart,
            self._populate_highlights,
            self._populate_continue,
        ):
            try:
                fn()
            except Exception:
                logger.exception(
                    "DashboardView._refresh_dashboard_sections: failed while calling %s",
                    fn.__name__,
                )

    def _keep_thread(self, thread: QThread) -> None:
        logger.debug("DashboardView._keep_thread: registering thread=%s", thread)
        self._threads.append(thread)

        def _cleanup_thread(t=thread):
            logger.debug("DashboardView thread finished: thread=%s", t)
            if t in self._threads:
                self._threads.remove(t)
                logger.debug("DashboardView thread removed from registry: remaining=%d", len(self._threads))

        thread.finished.connect(_cleanup_thread)

    def _load_data(self) -> None:
        logger.debug("DashboardView._load_data: starting background fetch")
        thread = registry.run_thread(self._fetch_all, self._on_data_loaded, name="dashboard-fetch")
        self._keep_thread(thread)

    def _fetch_all(self) -> dict:
        logger.debug("DashboardView._fetch_all: begin user_id=%s", getattr(self._user, "id", None))

        time_played_total = 0
        try:
            time_played_total = get_time_played(self._user.id) or 0
            logger.debug("DashboardView._fetch_all: total_time_played=%s", time_played_total)
        except Exception:
            logger.exception("Failed to load total time played")

        try:
            all_stats = fetch_all_user_stats(self._user.id)
            logger.debug(
                "DashboardView._fetch_all: all_stats loaded games_count=%d payload=%s",
                len((all_stats or {}).get("games", [])),
                all_stats,
            )
        except Exception:
            logger.exception("Failed to load all user stats")
            all_stats = {"games": []}

        per_game: dict[str, dict | None] = {}
        histories: dict[str, list[dict]] = {}
        for slug in _GAME_SLUGS:
            try:
                per_game[slug] = fetch_player_game_stats(self._user.id, slug)
                logger.debug("DashboardView._fetch_all: per_game[%s]=%s", slug, per_game[slug])
            except Exception:
                logger.exception("Failed to load per-game stats for %s", slug)
                per_game[slug] = None
            try:
                histories[slug] = fetch_user_run_history(self._user.id, slug, limit=20)
                logger.debug(
                    "DashboardView._fetch_all: histories[%s] count=%d sample=%s",
                    slug,
                    len(histories[slug] or []),
                    (histories[slug] or [None])[0],
                )
            except Exception:
                logger.exception("Failed to load run history for %s", slug)
                histories[slug] = []

        result = {
            "time_played_total": time_played_total,
            "all_stats": all_stats,
            "per_game": per_game,
            "histories": histories,
        }
        logger.debug("DashboardView._fetch_all: finished result_keys=%s", list(result.keys()))
        return result

    def _on_data_loaded(self, result: dict | None) -> None:
        logger.debug("DashboardView._on_data_loaded: result=%s", result)

        if not result:
            logger.debug("DashboardView._on_data_loaded: empty result, aborting populate")
            return

        self._time_played_total = result.get("time_played_total", 0)
        self._all_stats = result.get("all_stats", {"games": []})
        self._per_game = result.get("per_game", {})
        self._run_histories = result.get("histories", {})

        logger.debug(
            "DashboardView._on_data_loaded: stored time_total=%s games=%d per_game_keys=%s histories_counts=%s",
            self._time_played_total,
            len(self._all_stats.get("games", [])),
            list(self._per_game.keys()),
            {slug: len(hist or []) for slug, hist in self._run_histories.items()},
        )

        for fn in (
            self._populate_welcome,
            self._populate_activity,
            self._populate_recent_games,
            self._populate_trend_chart,
            self._populate_highlights,
            self._populate_continue,
        ):
            try:
                logger.debug("DashboardView._on_data_loaded: running %s", fn.__name__)
                fn()
                logger.debug("DashboardView._on_data_loaded: finished %s", fn.__name__)
            except Exception:
                logger.exception("Dashboard populate failed in %s", fn.__name__)

    def _populate_welcome(self) -> None:
        logger.debug("DashboardView._populate_welcome: start")

        streak = self._compute_current_streak()
        self._welcome_refs["current_streak"].setText(
            self._format_day_label(streak) if streak else "—"
        )

        weekly_time = self._get_weekly_time_seconds()
        self._welcome_refs["weekly_play_time"].setText(
            self._format_time(weekly_time) if weekly_time else "—"
        )

        sessions_this_week = self._get_sessions_this_week()
        self._welcome_refs["sessions_this_week"].setText(
            str(sessions_this_week) if sessions_this_week else "—"
        )

        favorite_game_slug = self._get_most_played_slug()
        self._welcome_refs["favorite_game"].setText(self._label_for_slug(favorite_game_slug))

        logger.debug(
            "DashboardView._populate_welcome: streak=%d weekly_time=%d sessions_this_week=%d favorite_game=%s",
            streak,
            weekly_time,
            sessions_this_week,
            favorite_game_slug,
        )

    def _populate_activity(self) -> None:
        logger.debug("DashboardView._populate_activity: start")

        history_runs = self._get_all_runs_sorted_desc()
        total_runs = len(history_runs)
        total_trials = sum((row.get("total_trials") or 0) for _, _, row in history_runs)
        streak = self._compute_current_streak()

        self._activity_refs["total_runs"].setText(str(total_runs) if total_runs else "—")
        self._activity_refs["total_trials"].setText(str(total_trials) if total_trials else "—")
        self._activity_refs["current_streak"].setText(self._format_day_label(streak) if streak else "—")
        self._activity_refs["time_played"].setText(self._format_time(self._time_played_total))

        goal = self._estimate_daily_goal()
        done = len(self._get_today_runs())
        self._goal_progress_value.setText(f"{done} / {goal}")

        if done >= goal and goal > 0:
            self._goal_hint.setText(translate("DashboardView", "Goal completed for today"))
        elif done == 0:
            self._goal_hint.setText(translate("DashboardView", "Start a session to begin today’s goal"))
        else:
            remaining = max(goal - done, 0)
            self._goal_hint.setText(
                translate("DashboardView", "{count} more session(s) to reach today’s goal").format(count=remaining)
            )

        logger.debug(
            "DashboardView._populate_activity: total_runs=%d total_trials=%d streak=%d total_time=%s goal=%d done_today=%d hint=%s",
            total_runs,
            total_trials,
            streak,
            self._time_played_total,
            goal,
            done,
            self._goal_hint.text(),
        )

    def _populate_recent_games(self) -> None:
        logger.debug("DashboardView._populate_recent_games: start")
        if self._recent_games_layout is None:
            return

        self._clear_layout(self._recent_games_layout)
        runs = self._get_all_runs_sorted_desc()

        if not runs:
            lbl = QLabel(translate("DashboardView", "No recent runs"))
            lbl.setObjectName("dashboardCardSubtitle")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._recent_games_layout.addWidget(lbl)
            logger.debug("DashboardView._populate_recent_games: no runs")
            return

        logger.debug(
            "DashboardView._populate_recent_games: total_runs=%d top3=%s",
            len(runs),
            [
                {
                    "dt": dt.isoformat() if dt else None,
                    "slug": slug,
                    "pi_run": row.get("pi_run"),
                }
                for dt, slug, row in runs[:3]
            ],
        )

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(80)
        row_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        for dt, slug, row in runs[:3]:
            pi = row.get("pi_run")
            pi_text = f"{pi:.2f} PI" if isinstance(pi, (int, float)) else "—"
            tile = self._build_recent_game_tile(
                self._label_for_slug(slug),
                self._relative_datetime_text(dt),
                pi_text,
            )
            tile.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            tile.setMinimumWidth(220)
            row_layout.addWidget(tile)

        self._recent_games_layout.addWidget(row_widget)
        

    def _populate_trend_chart(self) -> None:
        logger.debug("DashboardView._populate_trend_chart: start")
        if self._trend_chart_layout is None:
            return

        self._clear_layout(self._trend_chart_layout)
        self._chart_refs.clear()

        most_played_slug = self._get_most_played_slug()

        if self._most_played_title_label is not None:
            self._most_played_title_label.setText(self._label_for_slug(most_played_slug))

        if not most_played_slug:
            lbl = QLabel(translate("DashboardView", "No run data yet"))
            lbl.setObjectName("dashboardCardSubtitle")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._trend_chart_layout.addWidget(lbl)
            logger.debug("DashboardView._populate_trend_chart: no most_played_slug")
            return

        runs = []
        for row in self._run_histories.get(most_played_slug, []) or []:
            pi = row.get("pi_run")
            if pi is None:
                continue
            runs.append((self._parse_dt(row.get("started_at")), float(pi)))

        runs.sort(key=lambda item: item[0] or _MIN_UTC)
        values = [pi for _, pi in runs][-7:]

        logger.debug(
            "DashboardView._populate_trend_chart: slug=%s raw_points=%d last_values=%s",
            most_played_slug,
            len(runs),
            values,
        )

        if not values:
            lbl = QLabel(translate("DashboardView", "No run data yet"))
            lbl.setObjectName("dashboardCardSubtitle")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._trend_chart_layout.addWidget(lbl)
            logger.debug("DashboardView._populate_trend_chart: no chart data")
            return

        chart = _setup_chart()
        series = QLineSeries()
        pen = QPen(QColor(_ACCENT), 2.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        series.setPen(pen)

        for i, value in enumerate(values, start=1):
            series.append(QPointF(i, value))

        chart.addSeries(series)

        axis_x = _value_axis(
            "",
            tick_count=max(2, min(len(values), 7)),
        )
        axis_x.setRange(0.85, len(values) + 0.15)
        axis_x.setLabelFormat("%d")

        y_low, y_high = self._safe_y_range(values)
        axis_y = _value_axis("PI")
        axis_y.setRange(y_low, y_high)

        logger.debug(
            "DashboardView._populate_trend_chart: axis_x=(1,%s) axis_y=(%s,%s)",
            max(2, len(values)),
            y_low,
            y_high,
        )

        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        view = _create_chart_view(chart)
        self._chart_refs.extend([chart, series, view])
        self._trend_chart_layout.addWidget(view)

    def _populate_highlights(self) -> None:
        logger.debug("DashboardView._populate_highlights: start")

        games_data = self._all_stats.get("games", [])
        if not games_data:
            for lbl in self._highlight_refs.values():
                lbl.setText("—")
            logger.debug("DashboardView._populate_highlights: no games_data")
            return

        best_acc = max(
            (g for g in games_data if g.get("avg_accuracy_overall") is not None),
            key=lambda g: g.get("avg_accuracy_overall") or 0,
            default=None,
        )
        self._highlight_refs["best_accuracy"].setText(
            self._fmt_pct(best_acc.get("avg_accuracy_overall")) if best_acc else "—"
        )

        fastest = min(
            (g for g in games_data if g.get("avg_reaction_time_ms") is not None),
            key=lambda g: g.get("avg_reaction_time_ms") or 0,
            default=None,
        )
        self._highlight_refs["fastest_reaction"].setText(
            self._fmt_ms(fastest.get("avg_reaction_time_ms")) if fastest else "—"
        )

        logger.debug(
            "DashboardView._populate_highlights: best_acc=%s fastest=%s",
            best_acc,
            fastest,
        )

    def _populate_continue(self) -> None:
        logger.debug("DashboardView._populate_continue: start")
        runs = self._get_all_runs_sorted_desc()
        if not runs:
            self._current_continue_slug = None
            self._continue_labels["game_name"].setText("—")
            self._continue_labels["info"].setText("—")
            if self._continue_play_btn:
                self._continue_play_btn.setEnabled(False)
            logger.debug("DashboardView._populate_continue: no runs available")
            return

        dt, slug, _row = runs[0]
        self._current_continue_slug = slug
        self._continue_labels["game_name"].setText(self._label_for_slug(slug))
        self._continue_labels["info"].setText(self._relative_datetime_text(dt))

        if self._continue_play_btn:
            self._continue_play_btn.setEnabled(True)

        logger.debug(
            "DashboardView._populate_continue: slug=%s dt=%s",
            slug,
            dt.isoformat() if dt else None,
        )

    def _emit_continue_requested(self) -> None:
        logger.debug(
            "DashboardView._emit_continue_requested: current_continue_slug=%s",
            self._current_continue_slug,
        )
        if self._current_continue_slug:
            self.continue_game_requested.emit(self._current_continue_slug)

    def _get_today_runs(self) -> list[tuple[datetime | None, str, dict]]:
        today = datetime.now(timezone.utc).date()
        runs = [item for item in self._get_all_runs_sorted_desc() if item[0] and item[0].date() == today]
        logger.debug(
            "DashboardView._get_today_runs: today=%s count=%d",
            today,
            len(runs),
        )
        return runs

    def _get_sessions_this_week(self) -> int:
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        count = sum(
            1
            for dt, _, _ in self._get_all_runs_sorted_desc()
            if dt and dt >= week_ago
        )

        logger.debug(
            "DashboardView._get_sessions_this_week: week_ago=%s count=%d",
            week_ago.isoformat(),
            count,
        )
        return count

    def _get_weekly_time_seconds(self) -> int:
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        total = 0
        counted = 0
        skipped = 0

        for started_at, _, row in self._get_all_runs_sorted_desc():
            if not started_at or started_at < week_ago:
                continue

            ended_at = self._parse_dt(row.get("ended_at"))
            if not ended_at:
                skipped += 1
                continue

            diff = int((ended_at - started_at).total_seconds())
            if diff > 0:
                total += diff
                counted += 1
            else:
                skipped += 1

        logger.debug(
            "DashboardView._get_weekly_time_seconds: week_ago=%s counted=%d skipped=%d total=%d",
            week_ago.isoformat(),
            counted,
            skipped,
            total,
        )
        return total

    def _get_all_runs_sorted_desc(self) -> list[tuple[datetime | None, str, dict]]:
        runs: list[tuple[datetime | None, str, dict]] = []
        for slug, hist in self._run_histories.items():
            for row in hist or []:
                runs.append((self._parse_dt(row.get("started_at")), slug, row))

        runs.sort(key=lambda item: item[0] or _MIN_UTC, reverse=True)

        logger.debug(
            "DashboardView._get_all_runs_sorted_desc: total=%d per_slug=%s top=%s",
            len(runs),
            {slug: len(hist or []) for slug, hist in self._run_histories.items()},
            [
                {
                    "dt": dt.isoformat() if dt else None,
                    "slug": slug,
                    "pi_run": row.get("pi_run"),
                }
                for dt, slug, row in runs[:3]
            ],
        )
        return runs

    def _compute_today_time_seconds(self, today_runs: list[tuple[datetime | None, str, dict]]) -> int:
        total = 0
        counted = 0
        skipped = 0

        for started_at, _, row in today_runs:
            ended_at = self._parse_dt(row.get("ended_at"))
            if not started_at or not ended_at:
                skipped += 1
                continue

            diff = int((ended_at - started_at).total_seconds())
            if diff > 0:
                total += diff
                counted += 1
            else:
                skipped += 1

        logger.debug(
            "DashboardView._compute_today_time_seconds: today_runs=%d counted=%d skipped=%d total_secs=%d",
            len(today_runs),
            counted,
            skipped,
            total,
        )
        return total

    def _compute_current_streak(self) -> int:
        today = datetime.now(timezone.utc).date()
        days = {
            dt.date()
            for dt, _, _ in self._get_all_runs_sorted_desc()
            if dt is not None and dt.date() <= today
        }

        if not days:
            logger.debug("DashboardView._compute_current_streak: no days available")
            return 0

        cursor = today if today in days else today - timedelta(days=1)
        streak = 0
        while cursor in days:
            streak += 1
            cursor -= timedelta(days=1)

        logger.debug(
            "DashboardView._compute_current_streak: today=%s unique_days=%d streak=%d",
            today,
            len(days),
            streak,
        )
        return streak

    def _estimate_daily_goal(self) -> int:
        runs_by_day: dict = {}
        for dt, _, _ in self._get_all_runs_sorted_desc():
            if dt is None:
                continue
            day = dt.date()
            runs_by_day[day] = runs_by_day.get(day, 0) + 1

        if not runs_by_day:
            logger.debug("DashboardView._estimate_daily_goal: no runs_by_day, fallback=3")
            return 3

        avg = sum(runs_by_day.values()) / len(runs_by_day)
        goal = max(1, round(avg))

        logger.debug(
            "DashboardView._estimate_daily_goal: runs_by_day=%s avg=%.3f goal=%d",
            runs_by_day,
            avg,
            goal,
        )
        return goal

    def _get_most_played_row(self) -> dict | None:
        games = self._all_stats.get("games", [])
        row = max(
            (g for g in games if g.get("total_runs") is not None),
            key=lambda g: g.get("total_runs") or 0,
            default=None,
        )
        logger.debug("DashboardView._get_most_played_row: row=%s", row)
        return row

    def _get_most_played_slug(self) -> str | None:
        row = self._get_most_played_row()
        if not row:
            return None
        slug = self._game_slug_from_id(row.get("game_id"))
        logger.debug("DashboardView._get_most_played_slug: slug=%s", slug)
        return slug

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        removed = 0
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                removed += 1
        logger.debug("DashboardView._clear_layout: removed=%d", removed)

    def _safe_y_range(self, values: list[float]) -> tuple[float, float]:
        low = min(values)
        high = max(values)

        if abs(high - low) < 1e-9:
            padding = max(0.1, abs(low) * 0.1)
            result = (round(low - padding, 3), round(high + padding, 3))
            logger.debug(
                "DashboardView._safe_y_range: flat values=%s result=%s",
                values,
                result,
            )
            return result

        padding = (high - low) * 0.12
        result = (round(low - padding, 3), round(high + padding, 3))
        logger.debug(
            "DashboardView._safe_y_range: low=%s high=%s padding=%s result=%s",
            low,
            high,
            padding,
            result,
        )
        return result

    def _label_for_slug(self, slug: str | None) -> str:
        if not slug:
            return "—"
        return translate("DashboardView", _GAME_LABELS.get(slug, slug))

    def _game_slug_from_id(self, game_id) -> str | None:
        inverse = {value: key for key, value in GAME_ID_MAP.items()}
        slug = inverse.get(game_id)
        logger.debug("DashboardView._game_slug_from_id: game_id=%s slug=%s", game_id, slug)
        return slug

    def _parse_dt(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt + timedelta(hours=1)
        except Exception:
            logger.exception("DashboardView._parse_dt: failed to parse value=%s", value)
            return None

    def _relative_date_text(self, dt: datetime | None) -> str:
        if dt is None:
            return "—"

        now = datetime.now(timezone.utc)
        delta = now - dt

        if delta < timedelta(days=1) and dt.date() == now.date():
            return translate("DashboardView", "Today")
        if dt.date() == (now.date() - timedelta(days=1)):
            return translate("DashboardView", "Yesterday")
        if delta.days < 7:
            return translate("DashboardView", "{count} days ago").format(count=delta.days)
        return dt.strftime("%d.%m.%Y")

    def _relative_datetime_text(self, dt: datetime | None) -> str:
        if dt is None:
            return "—"

        now = datetime.now(timezone.utc)

        if dt.date() == now.date():
            return translate("DashboardView", "Today at {time}").format(time=dt.strftime("%H:%M"))
        if dt.date() == (now.date() - timedelta(days=1)):
            return translate("DashboardView", "Yesterday at {time}").format(time=dt.strftime("%H:%M"))
        return dt.strftime("%d.%m.%Y • %H:%M")

    def _format_time(self, seconds: int) -> str:
        if not seconds:
            return translate("DashboardView", "0 min")

        hours, rem = divmod(int(seconds), 3600)
        minutes = rem // 60

        if hours:
            return translate("DashboardView", "{hours}h {minutes}m").format(hours=hours, minutes=minutes)
        return translate("DashboardView", "{minutes} min").format(minutes=minutes)

    def _format_time_today(self, seconds: int) -> str:
        if not seconds:
            return "0m"
        if seconds < 60:
            return f"{seconds}s"

        hours, rem = divmod(int(seconds), 3600)
        minutes = rem // 60
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def _format_day_label(self, count: int) -> str:
        if count == 1:
            return translate("DashboardView", "1 day")
        return translate("DashboardView", "{count} days").format(count=count)

    def _fmt_pct(self, value: float | None) -> str:
        if value is None:
            return "—"
        pct = value * 100 if value <= 1.0 else value
        return f"{pct:.0f}%"

    def _fmt_ms(self, value: float | None) -> str:
        if value is None:
            return "—"
        return f"{int(value)} ms"