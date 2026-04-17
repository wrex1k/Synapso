"""StatisticsView: Non-scrollable game analytics overview."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QMargins, QPointF, Qt, QThread
from PySide6.QtGui import QBrush, QColor, QCursor, QFont, QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget
from PySide6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QLineSeries, QValueAxis

from app.core.registry import registry
from app.games.core.base_game import GAME_ID_MAP
from app.repository.activity_repository import get_time_played
from app.repository.run_repository import fetch_user_run_history
from app.repository.stats_repository import fetch_all_user_stats, fetch_player_game_stats
from app.ui.styles.colors import GAME_COLORS
from app.ui.styles.statistics import STATISTICS_STYLES
from app.utils.logger import get_logger
from app.utils.ui_helpers import build_header
from translations.translation import translate

logger = get_logger(__name__)

_TEXT_GRAY = "#A9A9A9"

_GAME_SLUGS = ["stroop", "memory_grid", "mental_rotation"]
_GAME_LABELS = {
    "stroop": "Stroop Test",
    "memory_grid": "Memory Grid",
    "mental_rotation": "Mental Rotation",
}


# formate float
def _fmt_float(v: float | None, decimals: int = 2) -> str:
    return f"{v:.{decimals}f}" if v is not None else "—"


def _fmt_int(v: int | None) -> str:
    return str(v) if v is not None else "—"


def _fmt_pct(v: float | None) -> str:
    if v is None:
        return "—"
    pct = v * 100 if v <= 1.0 else v
    return f"{pct:.0f}%"


def _fmt_ms(v: float | None) -> str:
    return f"{int(v)} ms" if v is not None else "—"

def _make_divider() -> QFrame:
    line = QFrame()
    line.setObjectName("statDivider")
    line.setFrameShape(QFrame.Shape.HLine)
    return line


def _show_trend_hover(lbl: QLabel, view: "QChartView", chart: QChart, series: QLineSeries, pt: QPointF) -> None:
    nearest = round(pt.x())
    if nearest < 1 or abs(pt.x() - nearest) > 0.30:
        lbl.hide()
        return
    scene_pos = chart.mapToPosition(QPointF(nearest, series.at(nearest - 1).y()), series)
    widget_pos = view.mapFromScene(scene_pos)
    lbl.setText(f"{series.at(nearest - 1).y():.2f}")
    lbl.adjustSize()
    x = int(widget_pos.x() - lbl.width() / 2)
    y = int(widget_pos.y() - lbl.height() - 8)
    lbl.move(x, y)
    lbl.show()
    lbl.raise_()


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
    chart.legend().setVisible(True)
    chart.legend().setLabelColor(QColor(_TEXT_GRAY))
    chart.legend().setFont(QFont("General Sans", 9))
    chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
    chart.legend().setBackgroundVisible(False)
    return chart


def _value_axis(label: str = "", tick_count: int = 6) -> QValueAxis:
    axis = QValueAxis()
    axis.setLabelsColor(QColor(_TEXT_GRAY))
    axis.setLabelsFont(QFont("General Sans", 9))
    axis.setGridLineColor(QColor(255, 255, 255, 12))
    axis.setLinePenColor(QColor(255, 255, 255, 18))
    axis.setTickCount(tick_count)
    axis.setMinorTickCount(0)
    if label:
        axis.setTitleText(label)
        axis.setTitleBrush(QColor(_TEXT_GRAY))
        axis.setTitleFont(QFont("General Sans", 10))
    return axis


class StatisticsView(QWidget):
    def __init__(self, user_id: str, parent=None):
        super().__init__(parent)
        self.setObjectName("statisticsView")
        self.setStyleSheet(STATISTICS_STYLES)

        self._user_id = user_id
        self._chart_refs: list = []
        self._threads: list[QThread] = []
        self._fetch_op = registry.operation("statistics-fetch")

        self._time_played: int = 0
        self._all_stats: dict = {"games": []}
        self._per_game: dict[str, dict | None] = {}
        self._run_histories: dict[str, list] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(25, 30, 25, 80)
        root.setSpacing(28)

        header, self._page_title_lbl, self._page_subtitle_lbl = build_header(
            translate("StatisticsView", "Statistics"),
            translate("StatisticsView", "Your performance analytics and progress over time")
        )
        root.addWidget(header)

        content_row = QHBoxLayout()
        content_row.setSpacing(20)
        content_row.setContentsMargins(0, 0, 0, 0)

        left_col = QVBoxLayout()
        left_col.setSpacing(16)
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.addWidget(self._build_trend_card(), 3)
        left_col.addLayout(self._build_game_cards_row(), 2)
        content_row.addLayout(left_col, 3)

        right_col = QVBoxLayout()
        right_col.setSpacing(16)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.addWidget(self._build_insights_card(), 1)
        right_col.addWidget(self._build_comparison_card(), 2)
        content_row.addLayout(right_col, 1)

        root.addLayout(content_row, 1)

    def _build_summary_row(self) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        cards = []

        for title, value, subtitle, attr in cards:
            lbl = QLabel(value)
            lbl.setObjectName("statOverviewValue")
            setattr(self, attr, lbl)
            layout.addWidget(self._build_summary_card(title, lbl, subtitle))

        return wrapper

    def _build_summary_card(self, title_text: str, value_lbl: QLabel, subtitle_text: str) -> QWidget:
        card = QWidget()
        card.setObjectName("statOverviewCard")
        card.setMinimumHeight(112)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(6)

        title = QLabel(title_text)
        title.setObjectName("statOverviewLabel")

        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("statOverviewSubtext")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(value_lbl)
        layout.addWidget(subtitle)
        layout.addStretch()

        return card

    def _build_trend_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("statChartCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(8)

        title = QLabel(translate("StatisticsView", "Performance Trend"))
        title.setObjectName("statChartTitle")
        self._trend_title_lbl = title

        layout.addWidget(title)

        self._trend_chart_placeholder = QWidget()
        self._trend_chart_placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._trend_chart_layout = QVBoxLayout(self._trend_chart_placeholder)
        self._trend_chart_layout.setContentsMargins(0, 0, 0, 0)

        empty = QLabel(translate("StatisticsView", "Loading..."))
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.setObjectName("statChartSubtitle")
        self._trend_chart_layout.addWidget(empty)

        layout.addWidget(self._trend_chart_placeholder, 1)

        return card

    def _build_game_cards_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(16)
        row.setContentsMargins(0, 0, 0, 0)

        self._game_cards: dict[str, dict] = {}
        for slug in _GAME_SLUGS:
            card_widget, labels = self._build_game_card(slug)
            self._game_cards[slug] = labels
            row.addWidget(card_widget, 1)

        return row

    def _build_insights_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("statGameCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        title = QLabel(translate("StatisticsView", "Quick Insights"))
        title.setObjectName("statGameTitle")
        self._insights_title_lbl = title
        layout.addWidget(title)

        insight_rows = [
            ("Best game", "_ins_best_game", "_ins_best_game_key"),
            ("Strongest metric", "_ins_best_metric", "_ins_best_metric_key"),
            ("Needs improvement", "_ins_worst_metric", "_ins_worst_metric_key"),
        ]

        for label_text, attr, key_attr in insight_rows:
            val_lbl = QLabel("—")
            val_lbl.setObjectName("statGameMetricValue")
            setattr(self, attr, val_lbl)
            lbl = QLabel(translate("StatisticsView", label_text))
            lbl.setObjectName("statGameMetricLabel")
            setattr(self, key_attr, lbl)
            layout.addWidget(self._build_metric_row_with_lbl(lbl, val_lbl))

        layout.addStretch()
        return card

    def _build_comparison_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("statChartCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(8)

        title = QLabel(translate("StatisticsView", "Game Comparison"))
        title.setObjectName("statChartTitle")
        self._comparison_title_lbl = title

        layout.addWidget(title)

        self._comparison_placeholder = QWidget()
        self._comparison_placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._comparison_layout = QVBoxLayout(self._comparison_placeholder)
        self._comparison_layout.setContentsMargins(0, 0, 0, 0)

        empty = QLabel(translate("StatisticsView", "Loading..."))
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.setObjectName("statChartSubtitle")
        self._comparison_layout.addWidget(empty)

        layout.addWidget(self._comparison_placeholder, 1)

        return card

    def _build_game_card(self, slug: str) -> tuple[QWidget, dict]:
        color_hex = GAME_COLORS[slug]
        title_text = _GAME_LABELS[slug]

        card = QWidget()
        card.setObjectName("statGameCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color_hex}; font-size: 14px;")

        title = QLabel(title_text)
        title.setObjectName("statGameTitle")

        header_row.addWidget(dot)
        header_row.addWidget(title)
        header_row.addStretch()

        layout.addLayout(header_row)
        layout.addWidget(_make_divider())

        metric_defs = [
            ("Runs", "runs"),
            ("ELO Rating", "elo_rating"),
            ("Best PI", "best_pi"),
            ("Average accuracy", "avg_acc"),
            ("Average reaction time", "avg_rt"),
        ]

        labels: dict[str, QLabel] = {}
        for label_text, key in metric_defs:
            val_lbl = QLabel("—")
            val_lbl.setObjectName("statGameMetricValue")
            labels[key] = val_lbl
            lbl = QLabel(translate("StatisticsView", label_text))
            lbl.setObjectName("statGameMetricLabel")
            labels[f"_lbl_{key}"] = lbl
            layout.addWidget(self._build_metric_row_with_lbl(lbl, val_lbl))

        layout.addStretch()
        return card, labels

    def _build_metric_row_with_lbl(self, label_lbl: QLabel, value_lbl: QLabel) -> QWidget:
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 2, 0, 2)
        row_layout.setSpacing(0)

        row_layout.addWidget(label_lbl)
        row_layout.addStretch()
        row_layout.addWidget(value_lbl)

        return row_widget

    def showEvent(self, event):
        super().showEvent(event)
        self._load_data()

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() != QEvent.Type.LanguageChange:
            return
        self._retranslate_ui()

    def _retranslate_ui(self) -> None:
        self._page_title_lbl.setText(translate("StatisticsView", "Statistics"))
        self._page_subtitle_lbl.setText(
            translate("StatisticsView", "Your performance analytics and progress over time")
        )
        self._trend_title_lbl.setText(translate("StatisticsView", "Performance Trend"))
        self._insights_title_lbl.setText(translate("StatisticsView", "Quick Insights"))
        self._comparison_title_lbl.setText(translate("StatisticsView", "Game Comparison"))

        self._ins_best_game_key.setText(translate("StatisticsView", "Best game"))
        self._ins_best_metric_key.setText(translate("StatisticsView", "Strongest metric"))
        self._ins_worst_metric_key.setText(translate("StatisticsView", "Needs improvement"))

        for labels in self._game_cards.values():
            labels["_lbl_runs"].setText(translate("StatisticsView", "Runs"))
            labels["_lbl_best_pi"].setText(translate("StatisticsView", "Best PI"))
            labels["_lbl_avg_acc"].setText(translate("StatisticsView", "Average accuracy"))
            labels["_lbl_avg_rt"].setText(translate("StatisticsView", "Average reaction time"))

        self._chart_refs.clear()
        self._populate_trend_chart()
        self._populate_comparison_chart()
        self._populate_insights()

    def _keep_thread(self, thread: QThread) -> None:
        self._threads.append(thread)
        thread.finished.connect(lambda t=thread: self._threads.remove(t) if t in self._threads else None)

    def _load_data(self):
        self._fetch_op.start(
            registry.run_thread,
            self._fetch_all,
            self._on_data_loaded,
            name="stats-fetch",
        )

    def _fetch_all(self) -> dict:
        time_played = 0
        try:
            time_played = get_time_played(self._user_id) or 0
        except Exception:
            pass

        all_stats = fetch_all_user_stats(self._user_id)

        per_game = {}
        histories = {}
        for slug in _GAME_SLUGS:
            per_game[slug] = fetch_player_game_stats(self._user_id, slug)
            histories[slug] = fetch_user_run_history(self._user_id, slug, limit=20)

        return {
            "time_played": time_played,
            "all_stats": all_stats,
            "per_game": per_game,
            "histories": histories,
        }

    def _on_data_loaded(self, result: dict | None) -> None:
        if not result:
            return

        self._time_played = result["time_played"]
        self._all_stats = result["all_stats"]
        self._per_game = result["per_game"]
        self._run_histories = result["histories"]

        self._chart_refs.clear()
        self._populate_game_cards()
        self._populate_insights()
        self._populate_trend_chart()
        self._populate_comparison_chart()

    def _populate_game_cards(self) -> None:
        for slug, labels in self._game_cards.items():
            stats = self._per_game.get(slug)
            if stats is None:
                continue
            labels["runs"].setText(_fmt_int(stats.get("total_runs")))
            labels["elo_rating"].setText(_fmt_int(stats.get("elo_rating")))
            labels["best_pi"].setText(_fmt_float(stats.get("best_pi_run")))
            labels["avg_acc"].setText(_fmt_pct(stats.get("avg_accuracy")))
            labels["avg_rt"].setText(_fmt_ms(stats.get("avg_reaction_time_ms")))

    def _populate_insights(self) -> None:
        games_data = self._all_stats.get("games", [])
        id_to_slug = {v: k for k, v in GAME_ID_MAP.items()}

        best_game_row = max(
            (g for g in games_data if g.get("elo_rating") is not None),
            key=lambda g: g["elo_rating"],
            default=None,
        )
        if best_game_row:
            slug = id_to_slug.get(best_game_row["game_id"], "")
            self._ins_best_game.setText(_GAME_LABELS.get(slug, slug))
        else:
            self._ins_best_game.setText("—")

        best_acc = max((game.get("avg_accuracy") or 0.0 for game in games_data), default=0.0)
        rt_values = [
            g["avg_reaction_time_ms"]
            for g in games_data
            if g.get("avg_reaction_time_ms") is not None and g["avg_reaction_time_ms"] > 0
        ]
        best_rt = min(rt_values) if rt_values else None
        _RT_REF = 1200.0
        rt_score = max(0.0, 1.0 - (best_rt / _RT_REF)) if best_rt is not None else 0.0

        if best_acc == 0.0 and rt_score == 0.0:
            self._ins_best_metric.setText("—")
        elif best_acc >= rt_score:
            self._ins_best_metric.setText(translate("StatisticsView", "Accuracy"))
        else:
            self._ins_best_metric.setText(translate("StatisticsView", "Reaction time"))

        worst_game_row = min(
            (g for g in games_data if g.get("elo_rating") is not None),
            key=lambda g: g["elo_rating"],
            default=None,
        )
        if worst_game_row and worst_game_row != best_game_row:
            slug = id_to_slug.get(worst_game_row["game_id"], "")
            self._ins_worst_metric.setText(_GAME_LABELS.get(slug, slug))
        else:
            self._ins_worst_metric.setText("—")

    def _populate_trend_chart(self) -> None:
        while self._trend_chart_layout.count():
            item = self._trend_chart_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        chart = _setup_chart()
        all_series = []
        has_data = False
        max_x = 0
        all_vals: list[float] = []

        for slug in _GAME_SLUGS:
            history = self._run_histories.get(slug, [])
            pi_values = [r["pi_run"] for r in history if r.get("pi_run") is not None]
            if not pi_values:
                continue
            has_data = True

            series = QLineSeries()
            series.setName(_GAME_LABELS[slug])
            pen = QPen(QColor(GAME_COLORS[slug]), 2.6)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            series.setPen(pen)
            series.setPointsVisible(True)

            for i, v in enumerate(pi_values, start=1):
                series.append(QPointF(i, v))

            chart.addSeries(series)
            all_series.append(series)
            self._chart_refs.append(series)
            max_x = max(max_x, len(pi_values))
            all_vals.extend(pi_values)

        if has_data:
            ax_x = _value_axis(translate("StatisticsView", "Runs"), min(max_x, 8))
            ax_x.setRange(1, max(max_x, 2))
            ax_x.setLabelFormat("%d")

            y_min = min(all_vals) * 0.9
            y_max = max(all_vals) * 1.1
            ax_y = _value_axis("")
            ax_y.setRange(round(y_min, 1), round(y_max, 1))

            chart.addAxis(ax_x, Qt.AlignmentFlag.AlignBottom)
            chart.addAxis(ax_y, Qt.AlignmentFlag.AlignLeft)
            for s in all_series:
                s.attachAxis(ax_x)
                s.attachAxis(ax_y)

            view = _create_chart_view(chart)
            view.setMinimumHeight(200)

            hover_lbl = QLabel(view)
            hover_lbl.setObjectName("trendHoverLabel")
            hover_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            hover_lbl.hide()

            for s in all_series:
                s.hovered.connect(
                    lambda pt, state, _s=s, _c=chart, _v=view, _l=hover_lbl: (
                        _show_trend_hover(_l, _v, _c, _s, pt) if state else _l.hide()
                    )
                )

            self._chart_refs.extend([chart, view])
            self._trend_chart_layout.addWidget(view)
        else:
            lbl = QLabel(translate("StatisticsView", "No run data yet"))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setObjectName("statChartSubtitle")
            self._trend_chart_layout.addWidget(lbl)

    def _populate_comparison_chart(self) -> None:
        while self._comparison_layout.count():
            item = self._comparison_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        slugs_with_data = [s for s in _GAME_SLUGS if self._per_game.get(s) is not None]
        if not slugs_with_data:
            lbl = QLabel(translate("StatisticsView", "No data yet"))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setObjectName("statChartSubtitle")
            self._comparison_layout.addWidget(lbl)
            return

        accuracy_vals = []
        quality_vals = []
        consistency_vals = []
        labels = []

        for slug in slugs_with_data:
            stats = self._per_game[slug]
            acc = stats.get("avg_accuracy")
            accuracy_vals.append(round((acc * 100) if acc is not None else 0, 1))
            qual = stats.get("avg_quality")
            if qual is not None and 0 < qual <= 1:
                qual = qual * 100
            quality_vals.append(round(qual if qual is not None else 0, 1))
            cons = stats.get("avg_consistency")
            if cons is not None and 0 < cons <= 1:
                cons = cons * 100
            consistency_vals.append(round(cons if cons is not None else 0, 1))
            labels.append(_GAME_LABELS[slug].replace(" ", "\n"))

        chart = _setup_chart()

        accuracy_set = QBarSet(translate("StatisticsView", "Accuracy"))
        accuracy_set.setColor(QColor(GAME_COLORS["stroop"]))
        accuracy_set.setBorderColor(QColor(0, 0, 0, 0))
        accuracy_set.append(accuracy_vals)

        quality_set = QBarSet(translate("StatisticsView", "Quality"))
        quality_set.setColor(QColor(GAME_COLORS["memory_grid"]))
        quality_set.setBorderColor(QColor(0, 0, 0, 0))
        quality_set.append(quality_vals)

        consistency_set = QBarSet(translate("StatisticsView", "Consistency"))
        consistency_set.setColor(QColor(GAME_COLORS["mental_rotation"]))
        consistency_set.setBorderColor(QColor(0, 0, 0, 0))
        consistency_set.append(consistency_vals)

        series = QBarSeries()
        series.setBarWidth(0.68)
        series.append(accuracy_set)
        series.append(quality_set)
        series.append(consistency_set)

        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        axis_x.setLabelsColor(QColor(_TEXT_GRAY))
        axis_x.setLabelsFont(QFont("General Sans", 9))
        axis_x.setGridLineColor(QColor(255, 255, 255, 10))
        axis_x.setLinePenColor(QColor(255, 255, 255, 18))

        axis_y = _value_axis("", 6)
        axis_y.setRange(0, 100)

        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        self._chart_refs.extend([chart, series, accuracy_set, quality_set, consistency_set])

        view = _create_chart_view(chart)
        view.setMinimumHeight(180)
        self._chart_refs.append(view)
        self._comparison_layout.addWidget(view)

