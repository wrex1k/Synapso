from __future__ import annotations

from PySide6.QtCharts import QChart, QChartView, QLineSeries, QScatterSeries, QValueAxis
from PySide6.QtCore import QMargins, QPointF, Qt, QEvent, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from app.models.user import User
from app.controller.dashboard_controller import DashboardController
from app.ui.styles.colors import PRIMARY_LIGHT, DASHBOARD_PINK_DOT, DASHBOARD_YELLOW_DOT, DASHBOARD_GRAPH_COLOR, GRAY, GAME_COLORS
from app.ui.styles.dashboard import DASHBOARD_STYLES
from app.ui.styles.fonts import DASHBOARD_FONT_STYLES, get_general_sans
from app.utils.ui_helpers import build_header
from translations.translation import translate


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
    axis.setLabelsColor(QColor(GRAY))
    axis.setLabelsFont(QFont("General Sans", 9))
    axis.setGridLineColor(QColor(255, 255, 255, 12))
    axis.setLinePenColor(QColor(255, 255, 255, 18))
    axis.setTickCount(max(2, tick_count))
    axis.setMinorTickCount(0)

    if label:
        axis.setTitleText(label)
        axis.setTitleBrush(QColor(GRAY))
        axis.setTitleFont(QFont("General Sans", 10))

    return axis


class DashboardView(QWidget):
    continue_game_requested = Signal(str)

    def __init__(self, user: User, parent=None):
        super().__init__(parent)

        self.setObjectName("dashboardView")
        self.setStyleSheet(DASHBOARD_FONT_STYLES + DASHBOARD_STYLES)

        self._user = user
        self._controller = DashboardController(user, self)
        self._controller.data_changed.connect(self._refresh_dashboard_sections)

        self._chart_refs: list = []
        self._welcome_refs: dict[str, QLabel] = {}
        self._highlight_refs: dict[str, QLabel] = {}
        self._continue_labels: dict[str, QLabel] = {}

        self._current_continue_slug: str | None = None

        self._trend_chart_layout: QVBoxLayout | None = None
        self._recent_games_layout: QVBoxLayout | None = None

        self._welcome_title_lbl: QLabel | None = None
        self._welcome_subtitle_lbl: QLabel | None = None
        self._goal_title_lbl: QLabel | None = None
        self._favorite_game_title_lbl: QLabel | None = None
        self._latest_training_title_lbl: QLabel | None = None
        self._recent_games_title_lbl: QLabel | None = None
        self._highlights_title_lbl: QLabel | None = None
        self._highlights_subtitle_lbl: QLabel | None = None
        self._continue_play_btn: QPushButton | None = None

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(60_000)
        self._refresh_timer.timeout.connect(self._controller.load)

        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(25, 30, 25, 60)
        root.setSpacing(28)

        header, self._page_title_lbl, self._page_subtitle_lbl = build_header(
            translate("DashboardView", "Dashboard"),
            translate("DashboardView", "Continue your training and stay on track"),
        )
        root.addWidget(header)

        top_row = QHBoxLayout()
        top_row.setSpacing(20)
        top_row.addWidget(self._build_welcome_card(), 2)
        top_row.addWidget(self._build_goal_card(), 1)
        root.addLayout(top_row)

        middle_row = QHBoxLayout()
        middle_row.setSpacing(20)
        middle_row.addWidget(self._build_most_played_chart_card(), 3)
        middle_row.addWidget(self._build_highlights_card(), 1)
        root.addLayout(middle_row, 1)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)
        bottom_row.addWidget(self._build_recent_games_card(), 2)
        bottom_row.addWidget(self._build_continue_card(), 1)
        root.addLayout(bottom_row)

    def _build_welcome_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("dashboardHeroCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(10)

        username = getattr(self._user, "username", None) or translate("DashboardView", "Player")

        self._welcome_title_lbl = QLabel(
            f"{translate('DashboardView', 'Welcome back,')} "
            f"<span style='color: {PRIMARY_LIGHT};'>{username}</span>"
        )
        self._welcome_title_lbl.setObjectName("dashboardHeroTitle")
        self._welcome_title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._welcome_subtitle_lbl = QLabel(
            translate("DashboardView", "Are you ready for another training session?")
        )
        self._welcome_subtitle_lbl.setObjectName("dashboardCardSubtitle")
        self._welcome_subtitle_lbl.setWordWrap(True)
        self._welcome_subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)

        stats_wrapper = QWidget()
        stats_wrapper.setObjectName("dashboardHeroStatsWrapper")
        stats_wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        stats_row = QHBoxLayout(stats_wrapper)
        stats_row.setContentsMargins(0, 8, 0, 0)
        stats_row.setSpacing(0)

        stats_row.addWidget(self._build_inline_stat(translate("DashboardView", "Daily streak"), "—", "daily_streak"))
        stats_row.addStretch()
        stats_row.addWidget(self._build_inline_stat(translate("DashboardView", "Total Games"), "—", "total_games"))
        stats_row.addStretch()
        stats_row.addWidget(self._build_inline_stat(translate("DashboardView", "Time played"), "—", "time_played"))
        stats_row.addStretch()
        stats_row.addWidget(self._build_inline_stat(translate("DashboardView", "Favorite game"), "—", "favorite_game"))

        layout.addWidget(self._welcome_title_lbl)
        layout.addWidget(self._welcome_subtitle_lbl)

        divider = QFrame()
        divider.setObjectName("dashboardDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)

        layout.addWidget(divider)
        layout.addWidget(stats_wrapper)
        return card

    def _build_goal_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("dashboardSideCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(10)

        self._goal_title_lbl = QLabel(translate("DashboardView", "Daily Goal"))
        self._goal_title_lbl.setObjectName("dashboardCardTitle")

        self._goal_progress_value = QLabel("—")
        self._goal_progress_value.setObjectName("dashboardGoalValue")

        self._goal_hint = QLabel("")
        self._goal_hint.setObjectName("dashboardMutedText")
        self._goal_hint.setWordWrap(True)

        layout.addWidget(self._goal_title_lbl)
        layout.addWidget(self._goal_progress_value)
        layout.addWidget(self._goal_hint)
        return card

    def _build_most_played_chart_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("dashboardCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        self._favorite_game_title_lbl = QLabel(translate("DashboardView", "Favorite Game"))
        self._favorite_game_title_lbl.setObjectName("dashboardCardTitle")

        header_row.addWidget(self._favorite_game_title_lbl)
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

        self._latest_training_title_lbl = QLabel(translate("DashboardView", "Latest Training"))
        self._latest_training_title_lbl.setObjectName("dashboardCardTitle")

        self._continue_labels["game_name"] = QLabel("—")
        self._continue_labels["game_name"].setObjectName("dashboardHighlightValue")

        self._continue_labels["info"] = QLabel("—")
        self._continue_labels["info"].setObjectName("dashboardMutedText")

        self._continue_play_btn = QPushButton(translate("DashboardView", "Play again"))
        self._continue_play_btn.setObjectName("dashboardPrimaryButton")
        self._continue_play_btn.setEnabled(False)
        self._continue_play_btn.clicked.connect(self._emit_continue_requested)

        layout.addWidget(self._latest_training_title_lbl)
        layout.addStretch()
        layout.addWidget(self._continue_labels["game_name"])
        layout.addWidget(self._continue_labels["info"])
        layout.addStretch()
        layout.addWidget(self._continue_play_btn)
        return card

    def _build_recent_games_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("dashboardCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)

        self._recent_games_title_lbl = QLabel(translate("DashboardView", "Recent Games"))
        self._recent_games_title_lbl.setObjectName("dashboardCardTitle")

        self._recent_games_container = QWidget()
        self._recent_games_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._recent_games_layout = QVBoxLayout(self._recent_games_container)
        self._recent_games_layout.setContentsMargins(0, 0, 0, 0)
        self._recent_games_layout.setSpacing(60)
        self._recent_games_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        empty = QLabel(translate("DashboardView", "Loading..."))
        empty.setObjectName("dashboardCardSubtitle")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._recent_games_layout.addWidget(empty)

        layout.addWidget(self._recent_games_title_lbl)
        layout.addWidget(self._recent_games_container)

        return card

    def _build_highlights_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("dashboardCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(8)

        self._highlights_title_lbl = QLabel(translate("DashboardView", "Highlights"))
        self._highlights_title_lbl.setObjectName("dashboardCardTitle")

        self._highlights_subtitle_lbl = QLabel(translate("DashboardView", "from favorite game"))
        self._highlights_subtitle_lbl.setObjectName("dashboardCardSubtitle")

        w1, value1 = self._build_badge_row(translate("DashboardView", "Accuracy"), "—", DASHBOARD_PINK_DOT)
        self._highlight_refs["best_accuracy"] = value1

        w2, value2 = self._build_badge_row(translate("DashboardView", "Reaction time"), "—", DASHBOARD_YELLOW_DOT)
        self._highlight_refs["fastest_reaction"] = value2

        layout.addWidget(self._highlights_title_lbl)
        layout.addWidget(self._highlights_subtitle_lbl)
        layout.addWidget(w1)
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

    def _build_badge_row(self, label_text: str, value_text: str, color: str) -> tuple[QWidget, QLabel]:
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 4, 0, 4)
        row_layout.setSpacing(10)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 20px;")

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

    def _build_recent_game_tile(self, game_text: str, date_text: str, pi_text: str, reaction_text: str, acc_text: str) -> QWidget:
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

        value_lbl = QLabel(f"{pi_text} | {reaction_text} | {acc_text}")
        value_lbl.setObjectName("recentGameValue")
        value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tile.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(date_lbl)
        layout.addWidget(value_lbl)
        layout.addStretch()

        return tile

    def showEvent(self, event) -> None:
        super().showEvent(event)

        if not self._controller.loaded_once:
            self._controller.mark_loaded_once()
            self._controller.load()
        elif not self._controller.is_loading():
            self._controller.load()
            self._update_welcome_title()

        self._refresh_timer.start()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self._refresh_timer.stop()

    def changeEvent(self, event) -> None:
        super().changeEvent(event)

        if event.type() != QEvent.LanguageChange:
            return

        self._retranslate_ui()

    def _update_welcome_title(self) -> None:
        if self._welcome_title_lbl:
            username = getattr(self._user, "username", None) or translate("DashboardView", "Player")
            self._welcome_title_lbl.setText(
                f"{translate('DashboardView', 'Welcome back,')} "
                f"<span style='color: {PRIMARY_LIGHT};'>{username}</span>"
            )

    def _retranslate_ui(self) -> None:
        self._page_title_lbl.setText(translate("DashboardView", "Dashboard"))
        self._page_subtitle_lbl.setText(translate("DashboardView", "Continue your training and stay on track"))

        self._update_welcome_title()

        if self._welcome_subtitle_lbl:
            self._welcome_subtitle_lbl.setText(
                translate("DashboardView", "Are you ready for another training session?")
            )

        self._update_labels(
            "dashboardInlineStatLabel",
            [
                "Daily streak",
                "Total Games",
                "Time played",
                "Favorite game",
            ],
        )

        self._update_labels(
            "dashboardRowTitle",
            [
                "Accuracy",
                "Reaction time",
            ],
        )

        if self._goal_title_lbl:
            self._goal_title_lbl.setText(translate("DashboardView", "Daily Goal"))
        if self._favorite_game_title_lbl:
            self._favorite_game_title_lbl.setText(translate("DashboardView", "Favorite Game"))
        if self._latest_training_title_lbl:
            self._latest_training_title_lbl.setText(translate("DashboardView", "Latest Training"))
        if self._recent_games_title_lbl:
            self._recent_games_title_lbl.setText(translate("DashboardView", "Recent Games"))
        if self._highlights_title_lbl:
            self._highlights_title_lbl.setText(translate("DashboardView", "Highlights"))
        if self._highlights_subtitle_lbl:
            self._highlights_subtitle_lbl.setText(translate("DashboardView", "from favorite game"))
        if self._continue_play_btn:
            self._continue_play_btn.setText(translate("DashboardView", "Play again"))

        self._refresh_dashboard_sections()

    def _update_labels(self, object_name: str, keys: list[str]) -> None:
        labels = self.findChildren(QLabel, object_name)
        for label, key in zip(labels, keys):
            label.setText(translate("DashboardView", key))

    def _refresh_dashboard_sections(self) -> None:
        for fn in (
            self._populate_welcome,
            self._populate_activity,
            self._populate_recent_games,
            self._populate_trend_chart,
            self._populate_highlights,
            self._populate_continue,
        ):
            fn()

    def _populate_welcome(self) -> None:
        model = self._controller.get_welcome_model()

        self._welcome_refs["daily_streak"].setText(model["daily_streak"])
        self._welcome_refs["total_games"].setText(model["total_games"])
        self._welcome_refs["time_played"].setText(model["time_played"])
        self._welcome_refs["favorite_game"].setText(model["favorite_game"])

    def _populate_activity(self) -> None:
        model = self._controller.get_activity_model()

        self._goal_progress_value.setText(model["goal_progress"])
        self._goal_hint.setText(model["goal_hint"])

    def _populate_recent_games(self) -> None:
        if self._recent_games_layout is None:
            return

        self._clear_layout(self._recent_games_layout)
        items = self._controller.get_recent_games_model()

        if not items:
            lbl = QLabel(translate("DashboardView", "No recent runs"))
            lbl.setObjectName("dashboardCardSubtitle")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._recent_games_layout.addWidget(lbl)
            return

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(80)
        row_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        for item in items:
            tile = self._build_recent_game_tile(
                item["game"],
                item["date"],
                item["pi"],
                item.get("reaction", "—"),
                item.get("accuracy", "—"),
            )
            tile.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            tile.setMinimumWidth(220)
            row_layout.addWidget(tile)

        self._recent_games_layout.addWidget(row_widget)

    def _populate_trend_chart(self) -> None:
        if self._trend_chart_layout is None:
            return

        self._clear_layout(self._trend_chart_layout)
        self._chart_refs.clear()

        model = self._controller.get_trend_chart_model()
        values = model["values"]
        game_color = GAME_COLORS.get(model.get("slug") or "", DASHBOARD_GRAPH_COLOR)

        if not values:
            lbl = QLabel(translate("DashboardView", "No run data yet"))
            lbl.setObjectName("dashboardCardSubtitle")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._trend_chart_layout.addWidget(lbl)
            return

        chart = _setup_chart()

        series = QLineSeries()
        pen = QPen(QColor(game_color), 2.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        series.setPen(pen)

        for i, value in enumerate(values, start=1):
            series.append(QPointF(i, value))

        chart.addSeries(series)

        scatter = QScatterSeries()
        scatter.setMarkerSize(8.0)

        scatter_pen = QPen(QColor(game_color))
        scatter_pen.setWidthF(0.5)
        scatter.setPen(scatter_pen)
        scatter.setBrush(QBrush(QColor(game_color)))

        for i, value in enumerate(values, start=1):
            scatter.append(QPointF(i, value))

        chart.addSeries(scatter)

        n = len(values)
        axis_x = _value_axis("", tick_count=max(2, n))
        axis_x.setRange(1, max(1, n))
        axis_x.setLabelFormat("%d")

        y_low, y_high = model["y_range"]
        axis_y = _value_axis("PI")
        axis_y.setRange(y_low, y_high)
        axis_y.setLabelFormat("%.1f")

        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)

        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        scatter.attachAxis(axis_x)
        scatter.attachAxis(axis_y)

        view = _create_chart_view(chart)
        self._trend_chart_layout.addWidget(view)

        self._chart_refs.extend([chart, series, scatter, view])

        text_items: list[tuple[int, float, object]] = []

        def _reposition_labels() -> None:
            plot_rect = chart.plotArea()
            for i, value, text_item in text_items:
                point_pos = chart.mapToPosition(QPointF(i, value), series)
                text_rect = text_item.boundingRect()
                x = point_pos.x() - text_rect.width() / 2
                y = point_pos.y() - text_rect.height() - 10
                y = max(plot_rect.top(), y)
                text_item.setPos(x, y)

        def _add_point_labels() -> None:
            if not view.scene():
                return

            font = get_general_sans(9)

            for i, value in enumerate(values, start=1):
                text_item = view.scene().addText(f"{value:.2f}")
                text_item.setFont(font)
                text_item.setDefaultTextColor(QColor("#EAEAEA"))
                text_item.setZValue(9999)
                text_items.append((i, value, text_item))
                self._chart_refs.append(text_item)

            _reposition_labels()

        # Create labels after the chart is first laid out …
        QTimer.singleShot(0, _add_point_labels)
        # … and reposition them every time the plot area changes (resize, DPI, re-render).
        chart.plotAreaChanged.connect(lambda _rect: _reposition_labels())

    def _populate_highlights(self) -> None:
        model = self._controller.get_highlights_model()

        self._highlight_refs["best_accuracy"].setText(model["best_accuracy"])
        self._highlight_refs["fastest_reaction"].setText(model["fastest_reaction"])

    def _populate_continue(self) -> None:
        model = self._controller.get_continue_model()

        self._current_continue_slug = model["slug"]
        self._continue_labels["game_name"].setText(model["game_name"])
        self._continue_labels["info"].setText(model["info"])

        if self._continue_play_btn:
            self._continue_play_btn.setEnabled(model["enabled"])

    def _emit_continue_requested(self) -> None:
        if self._current_continue_slug:
            self.continue_game_requested.emit(self._current_continue_slug)

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)