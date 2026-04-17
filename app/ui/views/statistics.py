"""StatisticsView: Non-scrollable game analytics overview."""

from __future__ import annotations

from PySide6.QtCore import QMargins, QPointF, Qt, QThread
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget
from PySide6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QLineSeries, QValueAxis

from app.core.registry import registry
from app.games.core.base_game import GAME_ID_MAP
from app.models.user import User
from app.repository.activity_repository import get_time_played
from app.repository.run_repository import fetch_user_run_history
from app.repository.stats_repository import fetch_all_user_stats, fetch_player_game_stats
from app.ui.styles.statistics import STATISTICS_STYLES
from app.utils.logger import get_logger
from app.utils.ui_helpers import build_header

logger = get_logger(__name__)

_ACCENT = "#3EAC91"
_TEXT_GRAY = "#A9A9A9"

_GAME_SLUGS = ["stroop", "memory_grid", "mental_rotation"]
_GAME_LABELS = {
    "stroop": "Stroop",
    "memory_grid": "Memory Grid",
    "mental_rotation": "Mental Rotation",
}
_GAME_COLORS_HEX = {
    "stroop": "#3EAC91",
    "memory_grid": "#4FC3F7",
    "mental_rotation": "#FFB74D",
}


def _fmt_float(v: float | None, decimals: int = 2) -> str:
    return f"{v:.{decimals}f}" if v is not None else "—"


def _fmt_int(v: int | None) -> str:
    return str(v) if v is not None else "—"


def _fmt_pct(v: float | None) -> str:
    """v is 0-1 fraction or 0-100; treat >1 as already 0-100."""
    if v is None:
        return "—"
    pct = v * 100 if v <= 1.0 else v
    return f"{pct:.0f}%"


def _fmt_ms(v: float | None) -> str:
    return f"{int(v)} ms" if v is not None else "—"


def _fmt_time(seconds: int) -> str:
    if not seconds:
        return "0 min"
    h, rem = divmod(int(seconds), 3600)
    m = rem // 60
    if h:
        return f"{h}h {m}m"
    return f"{m} min"


def _make_divider() -> QFrame:
    line = QFrame()
    line.setObjectName("statDivider")
    line.setFrameShape(QFrame.Shape.HLine)
    return line


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

        # data state
        self._time_played: int = 0
        self._all_stats: dict = {"games": []}
        self._per_game: dict[str, dict | None] = {}
        self._run_histories: dict[str, list] = {}

        self._build_ui()

    # ── layout ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(25, 30, 25, 80)
        root.setSpacing(28)

        header, self._page_title_lbl, self._page_subtitle_lbl = build_header(
            "Statistics",
            "Your performance analytics and progress over time"
        )
        root.addWidget(header)
        root.addWidget(self._build_summary_row())

        content_row = QHBoxLayout()
        content_row.setSpacing(20)
        content_row.setContentsMargins(0, 0, 0, 0)

        # Left column: trend chart on top, 3 game cards in a horizontal row below
        left_col = QVBoxLayout()
        left_col.setSpacing(16)
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.addWidget(self._build_trend_card(), 3)
        left_col.addLayout(self._build_game_cards_row(), 2)
        content_row.addLayout(left_col, 3)

        # Right column: quick insights on top, game comparison below
        right_col = QVBoxLayout()
        right_col.setSpacing(16)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.addWidget(self._build_insights_card(), 1)
        right_col.addWidget(self._build_comparison_card(), 1)
        content_row.addLayout(right_col, 1)

        root.addLayout(content_row, 1)

    def _build_summary_row(self) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        cards = [
            ("Total runs", "—", "All completed sessions", "_sum_total_runs_lbl"),
            ("Average PI", "—", "Across all games", "_avg_pi_lbl"),
            ("Accuracy", "—", "Overall average", "_avg_acc_lbl"),
            ("Avg reaction", "—", "Mean response time", "_avg_rt_lbl"),
        ]

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
        layout.setContentsMargins(18, 16, 18, 16)
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
        layout.setContentsMargins(20, 20, 20, 14)
        layout.setSpacing(8)

        title = QLabel("Performance Trend")
        title.setObjectName("statChartTitle")

        subtitle = QLabel("Performance index across your recent sessions")
        subtitle.setObjectName("statChartSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        self._trend_chart_placeholder = QWidget()
        self._trend_chart_placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._trend_chart_layout = QVBoxLayout(self._trend_chart_placeholder)
        self._trend_chart_layout.setContentsMargins(0, 0, 0, 0)

        empty = QLabel("Loading...")
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
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Quick Insights")
        title.setObjectName("statGameTitle")
        layout.addWidget(title)
        layout.addWidget(_make_divider())

        insight_rows = [
            ("Best game", "_ins_best_game"),
            ("Strongest metric", "_ins_best_metric"),
            ("Needs improvement", "_ins_worst_metric"),
            ("Total time played", "_ins_time_played"),
        ]

        for label_text, attr in insight_rows:
            val_lbl = QLabel("—")
            val_lbl.setObjectName("statGameMetricValue")
            setattr(self, attr, val_lbl)
            layout.addWidget(self._build_metric_row_with_lbl(label_text, val_lbl))

        layout.addStretch()
        return card

    def _build_comparison_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("statChartCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 14)
        layout.setSpacing(8)

        title = QLabel("Game Comparison")
        title.setObjectName("statChartTitle")

        subtitle = QLabel("Accuracy, quality and consistency by game")
        subtitle.setObjectName("statChartSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        self._comparison_placeholder = QWidget()
        self._comparison_placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._comparison_layout = QVBoxLayout(self._comparison_placeholder)
        self._comparison_layout.setContentsMargins(0, 0, 0, 0)

        empty = QLabel("Loading...")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.setObjectName("statChartSubtitle")
        self._comparison_layout.addWidget(empty)

        layout.addWidget(self._comparison_placeholder, 1)

        return card

    def _build_game_card(self, slug: str) -> tuple[QWidget, dict]:
        color_hex = _GAME_COLORS_HEX[slug]
        title_text = _GAME_LABELS[slug]

        card = QWidget()
        card.setObjectName("statGameCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
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
            ("Avg PI", "avg_pi"),
            ("Best PI", "best_pi"),
            ("Accuracy", "accuracy"),
            ("Avg RT", "avg_rt"),
        ]

        labels: dict[str, QLabel] = {}
        for label_text, key in metric_defs:
            val_lbl = QLabel("—")
            val_lbl.setObjectName("statGameMetricValue")
            labels[key] = val_lbl
            layout.addWidget(self._build_metric_row_with_lbl(label_text, val_lbl))

        layout.addStretch()
        return card, labels

    def _build_metric_row_with_lbl(self, label_text: str, value_lbl: QLabel) -> QWidget:
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 2, 0, 2)
        row_layout.setSpacing(0)

        label = QLabel(label_text)
        label.setObjectName("statGameMetricLabel")

        row_layout.addWidget(label)
        row_layout.addStretch()
        row_layout.addWidget(value_lbl)

        return row_widget

    # ── data loading ───────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        self._load_data()

    def _keep_thread(self, thread: QThread) -> None:
        self._threads.append(thread)
        thread.finished.connect(lambda t=thread: self._threads.remove(t) if t in self._threads else None)

    def _load_data(self):
        self._keep_thread(registry.run_thread(
            self._fetch_all,
            self._on_data_loaded,
            name="stats-fetch",
        ))

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

        self._populate_summary()
        self._populate_game_cards()
        self._populate_insights()
        self._populate_trend_chart()
        self._populate_comparison_chart()

    # ── populate ───────────────────────────────────────────────────

    def _populate_summary(self) -> None:
        games_data = self._all_stats.get("games", [])

        total_runs = sum(g.get("total_runs") or 0 for g in games_data)
        self._sum_total_runs_lbl.setText(_fmt_int(total_runs))

        pi_vals = [g["accumulated_pi"] for g in games_data if g.get("accumulated_pi") is not None]
        avg_pi = sum(pi_vals) / len(pi_vals) if pi_vals else None
        self._avg_pi_lbl.setText(_fmt_float(avg_pi))

        acc_vals = [g["avg_accuracy_overall"] for g in games_data if g.get("avg_accuracy_overall") is not None]
        avg_acc = sum(acc_vals) / len(acc_vals) if acc_vals else None
        self._avg_acc_lbl.setText(_fmt_pct(avg_acc))

        rt_vals = [g["avg_reaction_time_ms"] for g in games_data if g.get("avg_reaction_time_ms") is not None]
        avg_rt = sum(rt_vals) / len(rt_vals) if rt_vals else None
        self._avg_rt_lbl.setText(_fmt_ms(avg_rt))

    def _populate_game_cards(self) -> None:
        for slug, labels in self._game_cards.items():
            stats = self._per_game.get(slug)
            if stats is None:
                continue
            labels["runs"].setText(_fmt_int(stats.get("total_runs")))
            labels["avg_pi"].setText(_fmt_float(stats.get("accumulated_pi")))
            labels["best_pi"].setText(_fmt_float(stats.get("best_pi_run")))
            labels["accuracy"].setText(_fmt_pct(stats.get("avg_accuracy_overall")))
            labels["avg_rt"].setText(_fmt_ms(stats.get("avg_reaction_time_ms")))

    def _populate_insights(self) -> None:
        games_data = self._all_stats.get("games", [])
        id_to_slug = {v: k for k, v in GAME_ID_MAP.items()}

        # Best game by accumulated_pi
        best_game_row = max(
            (g for g in games_data if g.get("accumulated_pi") is not None),
            key=lambda g: g["accumulated_pi"],
            default=None,
        )
        if best_game_row:
            slug = id_to_slug.get(best_game_row["game_id"], "")
            self._ins_best_game.setText(_GAME_LABELS.get(slug, slug))
        else:
            self._ins_best_game.setText("—")

        # Strongest metric (across games: highest of avg_accuracy or pi relative to others)
        all_acc = [g.get("avg_accuracy_overall") or 0 for g in games_data]
        all_rt  = [g.get("avg_reaction_time_ms") or 0 for g in games_data]
        if all_acc and max(all_acc) > 0:
            # simple heuristic: compare normalised accuracy vs reaction speed
            norm_acc = max(all_acc)
            norm_rt  = min(all_rt) if all_rt else None
            if norm_rt is not None and norm_acc >= 0.75:
                self._ins_best_metric.setText("Accuracy")
            elif norm_rt is not None and norm_rt < 600:
                self._ins_best_metric.setText("Reaction time")
            else:
                self._ins_best_metric.setText("—")
        else:
            self._ins_best_metric.setText("—")

        # Needs improvement: lowest accumulated_pi game
        worst_game_row = min(
            (g for g in games_data if g.get("accumulated_pi") is not None),
            key=lambda g: g["accumulated_pi"],
            default=None,
        )
        if worst_game_row and worst_game_row != best_game_row:
            slug = id_to_slug.get(worst_game_row["game_id"], "")
            self._ins_worst_metric.setText(_GAME_LABELS.get(slug, slug))
        else:
            self._ins_worst_metric.setText("—")

        self._ins_time_played.setText(_fmt_time(self._time_played))

    def _populate_trend_chart(self) -> None:
        # Clear the placeholder
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
            pen = QPen(QColor(_GAME_COLORS_HEX[slug]), 2.6)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            series.setPen(pen)

            for i, v in enumerate(pi_values, start=1):
                series.append(QPointF(i, v))

            chart.addSeries(series)
            all_series.append(series)
            self._chart_refs.append(series)
            max_x = max(max_x, len(pi_values))
            all_vals.extend(pi_values)

        if has_data:
            ax_x = _value_axis("Run #", min(max_x, 8))
            ax_x.setRange(1, max(max_x, 2))
            ax_x.setLabelFormat("%d")

            y_min = min(all_vals) * 0.9
            y_max = max(all_vals) * 1.1
            ax_y = _value_axis("PI")
            ax_y.setRange(round(y_min, 1), round(y_max, 1))

            chart.addAxis(ax_x, Qt.AlignmentFlag.AlignBottom)
            chart.addAxis(ax_y, Qt.AlignmentFlag.AlignLeft)
            for s in all_series:
                s.attachAxis(ax_x)
                s.attachAxis(ax_y)

            view = _create_chart_view(chart)
            view.setMinimumHeight(200)
            self._chart_refs.extend([chart, view])
            self._trend_chart_layout.addWidget(view)
        else:
            lbl = QLabel("No run data yet")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setObjectName("statChartSubtitle")
            self._trend_chart_layout.addWidget(lbl)

    def _populate_comparison_chart(self) -> None:
        # Clear the placeholder
        while self._comparison_layout.count():
            item = self._comparison_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        slugs_with_data = [s for s in _GAME_SLUGS if self._per_game.get(s) is not None]
        if not slugs_with_data:
            lbl = QLabel("No data yet")
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
            acc = stats.get("avg_accuracy_overall")
            accuracy_vals.append(round((acc * 100) if acc is not None else 0, 1))
            qual = stats.get("quality_average")
            quality_vals.append(round((qual * 100) if qual is not None else 0, 1))
            cons = stats.get("consistency_average")
            consistency_vals.append(round((cons * 100) if cons is not None else 0, 1))
            labels.append(_GAME_LABELS[slug].replace(" ", "\n"))

        chart = _setup_chart()

        accuracy_set = QBarSet("Accuracy")
        accuracy_set.setColor(QColor(_GAME_COLORS_HEX["stroop"]))
        accuracy_set.setBorderColor(QColor(0, 0, 0, 0))
        accuracy_set.append(accuracy_vals)

        quality_set = QBarSet("Quality")
        quality_set.setColor(QColor(_GAME_COLORS_HEX["memory_grid"]))
        quality_set.setBorderColor(QColor(0, 0, 0, 0))
        quality_set.append(quality_vals)

        consistency_set = QBarSet("Consistency")
        consistency_set.setColor(QColor(_GAME_COLORS_HEX["mental_rotation"]))
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

        axis_y = _value_axis("%", 6)
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

