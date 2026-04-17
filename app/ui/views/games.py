"""Main hub for game discovery, stats, and launching gameplay sessions."""

from __future__ import annotations

import time

from PySide6.QtCore import QEvent, QObject, QSize, Qt, QThread, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget

from app.games.stroop.game import StroopGame
from app.games.memory_grid.game import MemoryGridGame
from app.games.mental_rotation.game import MentalRotationGame
from app.games.core.base_game import BaseGame, GAME_LABELS, GAME_ID_TO_SLUG
from app.games.core.tutorial import TutorialRunner
from app.controller.games_controller import GamesController
from app.service.activity_service import flush_heartbeat
from app.service.game_service import GameService
from app.ui.views.stroop_widget import StroopWidget
from app.ui.views.stroop_tutorial import StroopTutorial
from app.ui.views.memory_grid_tutorial import MemoryGridTutorial
from app.ui.views.mental_rotation_tutorial import MentalRotationTutorial
from app.ui.views.memory_grid_widget import MemoryGridWidget
from app.ui.views.mental_rotation_widget import MentalRotationWidget
from app.ui.styles.colors import SUCCESS, DANGER
from app.repository.stats_repository import subscribe_leaderboard
from app.repository.tutorial_repository import get_tutorial_completed
from app.repository.user_repository import fetch_avatar
from app.core.registry import registry
from app.utils.logger import get_logger
from app.utils.scaling import get_dpi_scale

logger = get_logger(__name__)
from app.utils.ui_helpers import build_header, image_to_rounded
from translations.translation import translate

_GAME_FACTORIES = {
    "stroop": lambda user_id: StroopGame(user_id),
    "memory_grid": lambda user_id: MemoryGridGame(user_id),
    "mental_rotation": lambda user_id: MentalRotationGame(user_id),
}

_INTRO_TUTORIAL_CLASSES: dict[str, type] = {
    "stroop": StroopTutorial,
    "memory_grid": MemoryGridTutorial,
    "mental_rotation": MentalRotationTutorial,
}

_WIDGET_FACTORIES = {
    "stroop": lambda: StroopWidget(),
    "memory_grid": lambda: MemoryGridWidget(),
    "mental_rotation": lambda: MentalRotationWidget(),
}

_GAME_DESCRIPTIONS = {
    "stroop": "The Stroop Test measures attention, processing speed, and cognitive control. The task is to name the color of a word, not the word itself, which creates mental interference.",
    "memory_grid": "The Memory Grid measures visual working memory and attention span. The task is to observe and memorize highlighted tiles in a grid, then reproduce the exact pattern by clicking on the correct tiles as accurately and quickly as possible.",
    "mental_rotation": "The Mental Rotation measures spatial reasoning and the ability to rotate objects in the mind. The task is to decide whether rotated objects are identical or mirrored.",
}

_ACTIVITY_ROWS = [
    ("PP", "Players playing"),
    ("GT", "Games today"),
    ("TW", "This week"),
    ("TG", "Total games"),
]

_STAT_CARDS = [
    ("rt", "Average reaction time"),
    ("acc", "Average accuracy"),
    ("quality", "Average quality"),
]

class _RealtimeWorker(QObject):
    changed = Signal()

    def __init__(self, game_db_id: int):
        super().__init__()
        self._game_db_id = game_db_id
        self._loop = None
        self._asyncio_task = None
        self._stop_requested = False

    def run(self) -> None:
        """Subscribe to real-time player stats updates for game."""
        try:
            subscribe_leaderboard(
                self._game_db_id,
                self.changed.emit,
                on_loop_ready=self._store_loop,
                on_task_ready=self._store_task,
            )
        except Exception as exc:
            logger.warning("Realtime worker exited unexpectedly for game_db_id=%d: %s", self._game_db_id, exc)

    def _store_loop(self, loop) -> None:
        """Store asyncio loop reference before task starts."""
        self._loop = loop

    def _store_task(self, task) -> None:
        """Store subscription task reference after it starts."""
        self._asyncio_task = task
        if self._stop_requested:
            self._cancel_task()

    def _cancel_task(self) -> None:
        task = self._asyncio_task
        loop = self._loop
        if task is not None and loop is not None and not task.done():
            loop.call_soon_threadsafe(task.cancel)

    def stop(self) -> None:
        """Cancel realtime subscription task from any thread."""
        self._stop_requested = True
        self._cancel_task()


class GamesView(QWidget):
    launch_game_requested = Signal(QWidget)

    def __init__(self, user_id: str, parent=None):
        super().__init__(parent)
        self.setObjectName("gamesView")
        self._user_id = user_id

        self._controller = GamesController(user_id, self)
        self._controller.games_loaded.connect(self._on_games_loaded)
        self._controller.stats_loaded.connect(self._on_stats_loaded)
        self._controller.leaderboard_loaded.connect(self._on_leaderboard_loaded)
        self._controller.avatar_loaded.connect(lambda: self.refresh_leaderboard_layout())

        self._tutorial_btns: dict[str, QPushButton] = {}
        self._play_btns: dict[str, QPushButton] = {}
        self._play_unlocked: dict[str, bool] = {}
        self._game_keys: list[str] = []
        self._game_db_ids: dict[str, int] = {}
        self._current_index: int = 0
        self._game_panels: dict[str, QWidget] = {}
        self._threads: list = []

        self._rt_workers: dict[int, tuple[QThread, _RealtimeWorker]] = {}
        self._dying_threads: list[QThread] = []

        self._current_user_rank: int | None = None
        self._lb_render_gen: int = 0
        self._lb_avatar_slots: dict[tuple[int, int], QLabel] = {}
        self._last_rendered_lb_id: int | None = None

        self._build_ui()
        self._retranslate_ui()
        self._controller.load_games()

    def _keep_thread(self, thread) -> None:
        self._threads.append(thread)
        thread.finished.connect(lambda t=thread: self._threads.remove(t) if t in self._threads else None)

    def refresh_user_avatar(self, avatar_path: str, data: bytes) -> None:
        if not avatar_path or not data:
            return
        pix = QPixmap()
        if pix.loadFromData(data):
            self._controller._data.avatars[avatar_path] = data
            if self._game_keys:
                db_id = self._game_db_ids.get(self._game_keys[self._current_index])
                if db_id is not None:
                    self._controller.invalidate_leaderboard(db_id)
                    self._controller.load_leaderboard(db_id)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(25, 30, 25, 80)
        root.setSpacing(28)

        header_layout = QHBoxLayout()

        header, self._page_title_lbl, self._page_subtitle_lbl = build_header(
            "Games",
            "Select a game to play and view your stats"
        )
        header_layout.addWidget(header)
        header_layout.addStretch()

        self._switcher_pill = QWidget()
        self._switcher_pill.setObjectName("switcherWidget")
        self._switcher_pill.setMaximumWidth(250)
        pill_layout = QHBoxLayout(self._switcher_pill)

        self._btn_prev = QPushButton()
        self._btn_prev.setObjectName("switcherLeft")
        self._btn_prev.setEnabled(False)
        self._btn_prev.setIcon(QIcon(":/images/icons/arrow-left.png"))
        self._btn_prev.setIconSize(QSize(20, 20))
        self._btn_prev.clicked.connect(self._prev_game)

        self._lbl_game_name = QLabel("")
        self._lbl_game_name.setObjectName("switcherTitle")
        self._lbl_game_name.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        self._lbl_game_name.setMinimumWidth(150)

        self._btn_next = QPushButton()
        self._btn_next.setObjectName("switcherRight")
        self._btn_next.setEnabled(False)
        self._btn_next.setIcon(QIcon(":/images/icons/arrow-right.png"))
        self._btn_next.setIconSize(QSize(20, 20))
        self._btn_next.clicked.connect(self._next_game)

        pill_layout.addWidget(self._btn_prev)
        pill_layout.addWidget(self._lbl_game_name)
        pill_layout.addWidget(self._btn_next)

        header_layout.addWidget(self._switcher_pill)
        root.addLayout(header_layout)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(20)
        body_layout.setContentsMargins(0, 0, 0, 0)

        self._game_stack = QStackedWidget()
        self._game_stack.setObjectName("gameStack")
        body_layout.addWidget(self._game_stack, 3)

        right_col = QVBoxLayout()
        right_col.setSpacing(20)
        right_col.setContentsMargins(0, 0, 0, 0)
        self._leaderboard_panel = self._build_leaderboard_panel()
        right_col.addWidget(self._leaderboard_panel, 1)
        
        self._user_rank_lbl = QLabel("")
        self._user_rank_lbl.setObjectName("userRankLabel")
        self._user_rank_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_col.addWidget(self._user_rank_lbl, 0)
        
        body_layout.addLayout(right_col, 1)

        root.addLayout(body_layout, 1)

    def _build_leaderboard_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("leaderboardCardWidget")
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        panel.setMaximumWidth(350)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(25)

        self._leaderboard_title_lbl = QLabel("")
        self._leaderboard_title_lbl.setObjectName("leaderboardCardTitle")
        layout.addWidget(self._leaderboard_title_lbl)
        layout.addSpacing(15)

        self._lb_container = QWidget()
        self._lb_container.setObjectName("lbContainer")
        self._lb_layout = QVBoxLayout(self._lb_container)
        self._lb_layout.setContentsMargins(0, 0, 0, 0)
        self._lb_layout.setSpacing(28)
        self._lb_layout.addStretch()

        self._lb_scroll = QScrollArea()
        self._lb_scroll.setWidgetResizable(True)
        self._lb_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._lb_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._lb_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._lb_scroll.setObjectName("leaderboardScroll")

        self._lb_scroll.setWidget(self._lb_container)
        layout.addWidget(self._lb_scroll, 1)

        return panel

    def _build_game_panel(self, game_slug: str) -> QWidget:
        panel = QWidget()
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(28)

        info_card = QWidget()
        info_card.setObjectName("infoCardWidget")
        info_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(28, 28, 28, 28)
        info_layout.setSpacing(10)

        game_title = GAME_LABELS.get(game_slug, "")
        game_desc = _GAME_DESCRIPTIONS.get(game_slug, "")
        info_title = QLabel(translate("GamesView", game_title))
        info_title.setObjectName("infoCardTitle")
        info_desc = QLabel(translate("GamesView", game_desc))
        info_desc.setObjectName("infoCardDescription")
        info_desc.setWordWrap(True)

        info_layout.addWidget(info_title)
        info_layout.addWidget(info_desc)
        outer.addWidget(info_card)

        panel._info_title_lbl = info_title
        panel._info_desc_lbl = info_desc
        panel._game_slug = game_slug

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)
        bottom_row.setContentsMargins(0, 0, 0, 0)

        activity_card, num_lbls, activity_title_lbl, activity_desc_lbl, activity_row_title_lbls = self._build_activity_card()
        stats_card, stat_lbls, stat_title_lbls = self._build_stats_card()

        bottom_row.addWidget(activity_card, 7)
        bottom_row.addWidget(stats_card, 13)

        outer.addLayout(bottom_row, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)
        btn_row.setContentsMargins(0, 0, 0, 0)

        tutorial_btn = QPushButton(translate("GamesView", "Tutorial"))
        tutorial_btn.setObjectName("tutorialButton")
        tutorial_btn.setFixedSize(165, 44)
        tutorial_btn.setProperty("unplayed", True)

        play_btn = QPushButton(translate("GamesView", "Play"))
        play_btn.setObjectName("playButton")
        play_btn.setFixedSize(165, 44)
        play_btn.setEnabled(False)

        btn_row.addStretch()
        btn_row.addWidget(tutorial_btn)
        btn_row.addWidget(play_btn)
        outer.addLayout(btn_row)

        self._tutorial_btns[game_slug] = tutorial_btn
        self._play_btns[game_slug] = play_btn
        self._play_unlocked[game_slug] = False

        tutorial_btn.clicked.connect(lambda _, gid=game_slug: self._launch_tutorial(gid))
        play_btn.clicked.connect(lambda _, gid=game_slug: self._launch_play(gid))

        panel._num_lbls = num_lbls
        panel._stat_lbls = stat_lbls
        panel._activity_title_lbl = activity_title_lbl
        panel._activity_desc_lbl = activity_desc_lbl
        panel._activity_row_title_lbls = activity_row_title_lbls
        panel._stat_title_lbls = stat_title_lbls

        return panel

    def _build_activity_card(self) -> tuple[QWidget, list[QLabel], QLabel, QLabel, dict[str, QLabel]]:
        card = QWidget()
        card.setObjectName("activityCardWidget")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        title_container = QVBoxLayout()
        title_container.setSpacing(6)
        act_title = QLabel("Activity")
        act_title.setObjectName("activityCardTitle")
        act_desc = QLabel("Below you can read the basic activity stats about this game")
        act_desc.setObjectName("activityCardDescription")
        act_desc.setWordWrap(True)
        title_container.addWidget(act_title)
        title_container.addWidget(act_desc)
        layout.addLayout(title_container)

        rows_container = QVBoxLayout()
        rows_container.setSpacing(0)
        rows_container.setContentsMargins(0, 0, 0, 0)

        num_lbls: list[QLabel] = []
        row_title_lbls: dict[str, QLabel] = {}
        for suffix, label_text in _ACTIVITY_ROWS:
            row_widget = QWidget()
            row_widget.setObjectName(f"activity{suffix}Widget")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 13, 13, 13)
            row_layout.setSpacing(13)

            num_lbl = QLabel("0")
            num_lbl.setObjectName(f"activity{suffix}RowNumber")
            num_lbl.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

            title_lbl = QLabel(label_text)
            title_lbl.setObjectName(f"activity{suffix}RowTitle")
            row_title_lbls[suffix] = title_lbl

            row_layout.addWidget(num_lbl)
            row_layout.addWidget(title_lbl)
            rows_container.addWidget(row_widget)
            num_lbls.append(num_lbl)

        layout.addLayout(rows_container)
        layout.addStretch()
        return card, num_lbls, act_title, act_desc, row_title_lbls

    def _build_stats_card(self) -> tuple[QWidget, dict, dict[str, QLabel]]:
        card = QWidget()
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card.setObjectName("statsCardWidget")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        stat_lbls: dict[str, tuple[QLabel, QLabel]] = {}
        stat_title_lbls: dict[str, QLabel] = {}

        for suffix, title_text in _STAT_CARDS:
            stat_widget = QWidget()
            stat_widget.setObjectName(f"{suffix}CardWidget")
            stat_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(28, 28, 28, 28)
            stat_layout.setSpacing(4)

            title_lbl = QLabel(title_text)
            title_lbl.setObjectName(f"{suffix}CardTitle")
            stat_layout.addWidget(title_lbl)
            stat_title_lbls[suffix] = title_lbl

            value_row = QHBoxLayout()
            value_row.setSpacing(0)

            val_lbl = QLabel("")
            val_lbl.setObjectName(f"{suffix}CardValue")

            delta_lbl = QLabel("")
            delta_lbl.setObjectName(f"{suffix}CardGlobal")
            delta_lbl.setTextFormat(Qt.TextFormat.RichText)

            value_row.addWidget(val_lbl)
            value_row.addStretch()
            value_row.addWidget(delta_lbl)

            stat_layout.addLayout(value_row)

            layout.addWidget(stat_widget, 1)
            stat_lbls[suffix] = (val_lbl, delta_lbl)

        return card, stat_lbls, stat_title_lbls

    def _retranslate_panel(self, panel: QWidget) -> None:
        activity_row_texts = {
            "PP": translate("GamesView", "Players playing"),
            "GT": translate("GamesView", "Games today"),
            "TW": translate("GamesView", "This week"),
            "TG": translate("GamesView", "Total games"),
        }
        stat_title_texts = {
            "rt": translate("GamesView", "Average reaction time"),
            "acc": translate("GamesView", "Average accuracy"),
            "quality": translate("GamesView", "Average quality"),
        }

        if hasattr(panel, "_info_title_lbl"):
            game_title = GAME_LABELS.get(panel._game_slug, "")
            game_desc = _GAME_DESCRIPTIONS.get(panel._game_slug, "")
            panel._info_title_lbl.setText(translate("GamesView", game_title))
            panel._info_title_lbl.setObjectName("infoCardTitle")
            panel._info_desc_lbl.setText(translate("GamesView", game_desc))
            panel._info_desc_lbl.setObjectName("infoCardDescription")
        if hasattr(panel, "_activity_title_lbl"):
            panel._activity_title_lbl.setText(translate("GamesView", "Activity"))
        if hasattr(panel, "_activity_desc_lbl"):
            panel._activity_desc_lbl.setText(
                translate("GamesView", "Below you can read the basic activity stats about this game")
            )
        if hasattr(panel, "_activity_row_title_lbls"):
            for suffix, _label_text in _ACTIVITY_ROWS:
                title_lbl = panel._activity_row_title_lbls.get(suffix)
                if title_lbl is not None:
                    title_lbl.setText(activity_row_texts.get(suffix, _label_text))
        if hasattr(panel, "_stat_title_lbls"):
            for suffix, _title_text in _STAT_CARDS:
                title_lbl = panel._stat_title_lbls.get(suffix)
                if title_lbl is not None:
                    title_lbl.setText(stat_title_texts.get(suffix, _title_text))

        if hasattr(panel, "_last_stats") and panel._last_stats:
            self._on_stats_loaded(self._game_db_ids[panel._game_slug])

    def _retranslate_ui(self) -> None:
        self._page_title_lbl.setText(translate("GamesView", "Games"))
        self._page_subtitle_lbl.setText(
            translate("GamesView", "Explore global game statistics and compete on the leaderboard")
        )
        self._leaderboard_title_lbl.setText(translate("GamesView", "Leaderboard"))

        for panel in self._game_panels.values():
            self._retranslate_panel(panel)

        for game_id, btn in self._tutorial_btns.items():
            if self._play_unlocked.get(game_id, False):
                btn.setText(translate("GamesView", "Tutorial passed"))
            else:
                btn.setText(translate("GamesView", "Tutorial"))
        for btn in self._play_btns.values():
            btn.setText(translate("GamesView", "Play"))

        rank = self._current_user_rank
        self._user_rank_lbl.setText(
            translate("GamesView", "Your rank: {rank}").format(rank=rank) if rank else translate("GamesView", "Your rank: —")
        )

    def _on_games_loaded(self) -> None:
        """Handle games loaded and build UI panels."""
        games = self._controller._data.games
        for g in games:
            db_id = g["id"]
            impl_key = GAME_ID_TO_SLUG.get(db_id)
            if impl_key is None:
                logger.debug("No implementation for db game id=%d, skipping", db_id)
                continue
            panel = self._build_game_panel(impl_key)
            self._game_stack.addWidget(panel)
            self._game_keys.append(impl_key)
            self._game_db_ids[impl_key] = db_id
            self._game_panels[impl_key] = panel

        self._retranslate_ui()
        self._refresh_play_buttons()
        self._switcher_refresh()

        if self._game_keys:
            game_db_ids = [self._game_db_ids[key] for key in self._game_keys]
            self._controller.load_all_stats(game_db_ids)
            for db_id in game_db_ids:
                self._controller.load_leaderboard(db_id)
            for key in self._game_keys:
                self._start_realtime_for(self._game_db_ids[key])

    def _on_stats_loaded(self, game_db_id: int) -> None:
        """Handle stats loaded and update panel display."""
        game_key = next((k for k, v in self._game_db_ids.items() if v == game_db_id), None)
        if not game_key:
            return
        
        panel = self._game_panels.get(game_key)
        stats = self._controller._data.stats.get(game_db_id)
        if not panel or not stats:
            return

        panel._last_stats = stats

        num_lbls: list[QLabel] = panel._num_lbls
        if num_lbls:
            num_lbls[0].setText(str(stats.get("players_playing", 0)))
            num_lbls[1].setText(str(stats.get("games_today", 0)))
            week = stats.get("games_this_week")
            num_lbls[2].setText(f"{week:,}" if isinstance(week, int) else "0")
            total = stats.get("total_games")
            num_lbls[3].setText(f"{total:,}" if isinstance(total, int) else "0")

        stat_lbls: dict = panel._stat_lbls

        rt = stats.get("avg_reaction_time_ms")
        val, delta = stat_lbls["rt"]
        val.setText(f"{int(rt)}ms" if rt is not None else "0 ms")
        rt_diff = stats.get("rt_diff_ms")
        if rt_diff is not None:
            is_better = rt_diff < 0
            direction = "↑" if is_better else "↓"
            color = f"{SUCCESS}" if is_better else f"{DANGER}"
            if is_better:
                message = translate("GamesView", "you are {value}ms faster than global avg").format(
                    value=abs(int(rt_diff))
                )
            else:
                message = translate("GamesView", "you are {value}ms slower than global avg").format(
                    value=abs(int(rt_diff))
                )
            delta.setText(f'<span style="color:{color}; font-weight: 600;">{direction}</span>&nbsp;<span style="color:#FAFAFA;">{message}</span>')
        else:
            delta.setText("")

        acc = stats.get("avg_accuracy")
        val, delta = stat_lbls["acc"]
        val.setText(f"{int(acc)}%" if acc is not None else "0%")
        acc_diff = stats.get("acc_diff")
        if acc_diff is not None:
            is_better = acc_diff > 0
            direction = "↑" if is_better else "↓"
            color = f"{SUCCESS}" if is_better else f"{DANGER}"
            if is_better:
                message = translate("GamesView", "you are {value}% more accurate than global avg").format(
                    value=f"{abs(acc_diff):.1f}"
                )
            else:
                message = translate("GamesView", "you are {value}% less accurate than global avg").format(
                    value=f"{abs(acc_diff):.1f}"
                )
            delta.setText(f'<span style="color:{color}; font-weight: 600;">{direction}</span>&nbsp;<span style="color:#FAFAFA;">{message}</span>')
        else:
            delta.setText("")

        avg_quality = stats.get("avg_quality")
        val, delta = stat_lbls["quality"]
        val.setText(f"{avg_quality:.0f}%" if avg_quality is not None else "0%")
        quality_diff = stats.get("quality_diff")
        if quality_diff is not None:
            is_better = quality_diff > 0
            direction = "↑" if is_better else "↓"
            color = f"{SUCCESS}" if is_better else f"{DANGER}"
            if is_better:
                message = translate("GamesView", "your quality is {value}% above global avg").format(
                    value=f"{abs(quality_diff):.1f}"
                )
            else:
                message = translate("GamesView", "your quality is {value}% below global avg").format(
                    value=f"{abs(quality_diff):.1f}"
                )
            delta.setText(f'<span style="color:{color}; font-weight: 600;">{direction}</span>&nbsp;<span style="color:#FAFAFA;">{message}</span>')
        else:
            delta.setText("")

    def _on_leaderboard_loaded(self, game_db_id: int) -> None:
        """Handle leaderboard loaded and render for current game."""
        if not self._game_keys:
            return
        current_key = self._game_keys[self._current_index]
        current_db_id = self._game_db_ids.get(current_key)
        if game_db_id == current_db_id:
            data = self._controller._data.leaderboards.get(game_db_id)
            if data:
                entries = data.get("entries", [])
                avatar_paths = [e.get("avatar_path") for e in entries if e.get("avatar_path")]
                self._controller.preload_avatars(avatar_paths)
                self._render_leaderboard(data)
                self._last_rendered_lb_id = game_db_id

    def _render_leaderboard(self, data: dict) -> None:
        entries = data.get("entries", [])
        user_rank = data.get("user_rank")
        self._current_user_rank = user_rank

        self._lb_render_gen += 1
        self._lb_avatar_slots.clear()

        new_container = QWidget()
        new_container.setObjectName("lbContainer")
        new_layout = QVBoxLayout(new_container)
        new_layout.setContentsMargins(0, 0, 0, 0)
        new_layout.setSpacing(28)

        for slot_idx, entry in enumerate(entries):
            row_widget = self._build_lb_row(entry, slot_idx)
            new_layout.addWidget(row_widget)
        new_layout.addStretch()

        self._lb_scroll.setWidget(new_container)
        self._lb_container = new_container
        self._lb_layout = new_layout

        self._current_user_rank = user_rank
        self._user_rank_lbl.setText(
            translate("GamesView", "Your rank: {rank}").format(rank=user_rank) if user_rank else translate("GamesView", "Your rank: —")
        )

    def refresh_leaderboard_layout(self) -> None:
        """Re-render leaderboard from cache after window resize."""
        if not self._game_keys:
            return
        db_id = self._game_db_ids.get(self._game_keys[self._current_index])
        if db_id and self._last_rendered_lb_id != db_id:
            data = self._controller._data.leaderboards.get(db_id)
            if data:
                self._render_leaderboard(data)
                self._last_rendered_lb_id = db_id

    def _build_lb_row(self, entry: dict, slot_idx: int) -> QWidget:
        is_online = entry.get("is_online", False)

        row = QWidget()
        row.setObjectName("leaderboardRowWidget")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(12)

        avatar_lbl = QLabel()
        avatar_lbl.setObjectName("leaderboardRowImage")
        _av = max(32, int(40 * get_dpi_scale()))
        avatar_lbl.setFixedSize(_av, _av)
        avatar_lbl.setScaledContents(True)
        default_pix = QPixmap(_av, _av)
        default_pix.fill(QColor("#2A2A2A"))
        avatar_lbl.setPixmap(default_pix)
        image_to_rounded(avatar_lbl)
        layout.addWidget(avatar_lbl)

        middle_col = QVBoxLayout()
        middle_col.setContentsMargins(0, 0, 0, 0)
        middle_col.setSpacing(2)
        
        name_lbl = QLabel(entry.get("username", translate("GamesView", "Player")))
        name_lbl.setObjectName("leaderboardRowTitle")
        middle_col.addWidget(name_lbl)

        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(0)
        status_color = "#3A9A8F" if is_online else "#9E3F3F"
        status_text = translate("GamesView", "Online") if is_online else translate("GamesView", "Offline")
        status_lbl = QLabel(f'<span style="color:{status_color};">⬤ {status_text}</span>')
        status_lbl.setObjectName("leaderboardRowStatus")
        status_lbl.setTextFormat(Qt.TextFormat.RichText)
        status_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        status_row.addWidget(status_lbl)
        middle_col.addLayout(status_row)
        
        layout.addLayout(middle_col)
        layout.addStretch()

        elo_rating = entry.get('elo_rating', 1000)
        score_lbl = QLabel(f"{int(elo_rating)}")
        score_lbl.setObjectName("leaderboardRowValue")
        score_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(score_lbl)

        avatar_path = entry.get("avatar_path")
        requested_avatar = avatar_path or "default.webp"
        
        cached_data = self._controller._data.avatars.get(requested_avatar)
        if cached_data:
            pix = QPixmap()
            if pix.loadFromData(cached_data):
                avatar_lbl.setPixmap(pix)
                avatar_lbl.setScaledContents(True)
                image_to_rounded(avatar_lbl)
        else:
            render_gen = self._lb_render_gen
            self._lb_avatar_slots[(render_gen, slot_idx)] = avatar_lbl
            self._keep_thread(registry.run_thread(
                lambda p=requested_avatar: fetch_avatar(p),
                lambda data, p=requested_avatar, gen=render_gen, idx=slot_idx: (
                    self._apply_lb_avatar(p, data, gen, idx)
                ),
            ))

        return row

    def _apply_lb_avatar(
        self,
        avatar_path: str,
        data: bytes | None,
        render_gen: int,
        slot_idx: int,
    ) -> None:
        lbl = self._lb_avatar_slots.pop((render_gen, slot_idx), None)
        if lbl is None:
            return
        try:
            lbl.objectName()
        except RuntimeError:
            return
        if not data:
            fallback = QPixmap(":/images/graphics/avatar.png")
            if not fallback.isNull():
                lbl.setPixmap(fallback)
                lbl.setScaledContents(True)
                image_to_rounded(lbl)
            return
        pix = QPixmap()
        if pix.loadFromData(data):
            # Cache in controller
            self._controller._data.avatars[avatar_path] = data
            lbl.setPixmap(pix)
            lbl.setScaledContents(True)
            image_to_rounded(lbl)
        else:
            logger.warning("Failed to load avatar from bytes (corrupted?), using resource fallback")
            default_data = self._controller._data.avatars.get("default.webp")
            if default_data:
                default_pix = QPixmap()
                if default_pix.loadFromData(default_data):
                    lbl.setPixmap(default_pix)
                    lbl.setScaledContents(True)
                    image_to_rounded(lbl)
                    return
            fallback = QPixmap(":/images/graphics/avatar.png")
            if not fallback.isNull():
                lbl.setPixmap(fallback)
                lbl.setScaledContents(True)
                image_to_rounded(lbl)

    def _launch_tutorial(self, game_id: str):
        if game_id in _INTRO_TUTORIAL_CLASSES:
            self._launch_intro_tutorial(game_id)
            return

        self._launch_game_tutorial(game_id)

    def _launch_game_tutorial(self, game_id: str) -> None:
        """Launch gameplay tutorial session."""
        if self._play_unlocked.get(game_id, False):
            logger.info("Tutorial already completed for %s — gameplay blocked", game_id)
            return

        factory = _GAME_FACTORIES.get(game_id)
        if factory is None:
            logger.error("Unknown game_id: %s", game_id)
            return
        game = factory(self._user_id)
        service = GameService(game)
        runner = service.create_tutorial_runner()
        logger.info("Launching tutorial for game=%s", game_id)
        self._open_session(game_id, "tutorial", game, service, runner)

    def _launch_intro_tutorial(self, game_id: str) -> None:
        """Show intro tutorial and practice session."""
        self._set_buttons_locked(game_id, True, lock_play=False)
        already_done = self._play_unlocked.get(game_id, False)
        tutorial_cls = _INTRO_TUTORIAL_CLASSES[game_id]
        widget = tutorial_cls(allow_gameplay_tutorial=not already_done)
        widget.start_game_tutorial_requested.connect(
            lambda gid=game_id: self._launch_game_tutorial(gid)
        )
        widget.session_done.connect(
            lambda _passed=False, gid=game_id: self._set_buttons_locked(gid, False)
        )
        self.launch_game_requested.emit(widget)

    def _launch_play(self, game_id: str):
        factory = _GAME_FACTORIES.get(game_id)
        if factory is None:
            logger.error("Unknown game_id: %s", game_id)
            return
        game = factory(self._user_id)
        service = GameService(game)
        logger.info("Launching play for game=%s", game_id)
        self._open_session(game_id, "play", game, service, None)

    def _open_session(
        self,
        game_id: str,
        mode: str,
        game: BaseGame,
        service: GameService,
        runner: TutorialRunner | None,
    ):
        self._set_buttons_locked(game_id, True)
        widget_factory = _WIDGET_FACTORIES.get(game_id)
        if widget_factory is None:
            logger.error("No widget factory for game_id: %s", game_id)
            self._set_buttons_locked(game_id, False)
            return

        widget = widget_factory()
        widget.session_done.connect(
            lambda passed, gid=game_id, m=mode: self._on_session_done(gid, m, passed, widget)
        )
        self.launch_game_requested.emit(widget)
        if mode == "tutorial":
            widget.start_tutorial(game, service, runner)
        else:
            widget.start_play(game, service)

    def _on_session_done(self, game_id: str, mode: str, passed: bool, widget: QWidget):
        widget.deleteLater()
        if mode == "tutorial" and passed:
            self._play_unlocked[game_id] = True
            tut_btn = self._tutorial_btns.get(game_id)
            if tut_btn:
                tut_btn.setProperty("unplayed", False)
                tut_btn.setText(translate("GamesView", "Tutorial passed"))
                tut_btn.style().unpolish(tut_btn)
                tut_btn.style().polish(tut_btn)
                tut_btn.update()
            logger.info("Tutorial passed for %s — Play button unlocked", game_id)
        self._set_buttons_locked(game_id, False)
        if mode == "play":
            game_db_id = self._game_db_ids.get(game_id)
            if game_db_id:
                self._controller.invalidate_stats(game_db_id)
            self._load_stats_for_current()
            self._switch_leaderboard()

    def _refresh_play_buttons(self):
        game_ids = list(self._play_btns.keys())
        user_id = self._user_id

        def _check_all() -> dict[str, bool]:
            results: dict[str, bool] = {}
            for game_id in game_ids:
                try:
                    results[game_id] = get_tutorial_completed(user_id, game_id)
                except Exception as exc:
                    logger.warning("Could not check tutorial status for %s: %s", game_id, exc)
                    results[game_id] = False
            return results

        def _apply(results: dict[str, bool]) -> None:
            for game_id, completed in results.items():
                self._play_unlocked[game_id] = completed
                self._play_btns[game_id].setEnabled(completed)
                tut_btn = self._tutorial_btns.get(game_id)
                if tut_btn:
                    tut_btn.setProperty("unplayed", not completed)
                    if completed:
                        tut_btn.setText(translate("GamesView", "Tutorial passed"))
                    tut_btn.style().unpolish(tut_btn)
                    tut_btn.style().polish(tut_btn)
                    tut_btn.update()

        self._keep_thread(registry.run_thread(_check_all, _apply))

    def _set_buttons_locked(self, game_id: str, locked: bool, lock_play: bool = True):
        self._tutorial_btns[game_id].setEnabled(not locked)
        if lock_play:
            self._play_btns[game_id].setEnabled(
                (not locked) and self._play_unlocked.get(game_id, False)
            )

    def _switcher_refresh(self) -> None:
        total = len(self._game_keys)
        if total == 0:
            self._lbl_game_name.setText(translate("GamesView", "No data"))
            self._btn_prev.setEnabled(False)
            self._btn_next.setEnabled(False)
            return
        key = self._game_keys[self._current_index]
        self._game_stack.setCurrentWidget(self._game_panels[key])
        panel = self._game_panels[key]
        info_title = next(
            (w for w in panel.findChildren(QLabel) if w.objectName() == "infoCardTitle"),
            None,
        )
        self._lbl_game_name.setText(info_title.text() if info_title else key)
        self._btn_prev.setEnabled(self._current_index > 0)
        self._btn_next.setEnabled(self._current_index < total - 1)

    def _prev_game(self) -> None:
        if self._current_index > 0:
            self._current_index -= 1
            self._last_rendered_lb_id = None
            self._switcher_refresh()
            self._load_stats_for_current()
            self._switch_leaderboard()

    def _next_game(self) -> None:
        if self._current_index < len(self._game_keys) - 1:
            self._current_index += 1
            self._last_rendered_lb_id = None
            self._switcher_refresh()
            self._load_stats_for_current()
            self._switch_leaderboard()

    def _switch_leaderboard(self) -> None:
        """Switch leaderboard to current game - render cached data atomically."""
        if not self._game_keys:
            return
        game_db_id = self._game_db_ids.get(self._game_keys[self._current_index])
        if not game_db_id:
            return
        cached_lb = self._controller._data.leaderboards.get(game_db_id)
        if cached_lb:
            self._render_leaderboard(cached_lb)
            self._last_rendered_lb_id = game_db_id
        else:
            self._clear_leaderboard()
        self._controller.invalidate_leaderboard(game_db_id)
        self._controller.load_leaderboard(game_db_id)

    def _clear_leaderboard(self) -> None:
        """Remove all leaderboard rows so stale data from the previous game is never visible."""
        new_container = QWidget()
        new_container.setObjectName("lbContainer")
        new_layout = QVBoxLayout(new_container)
        new_layout.setContentsMargins(0, 0, 0, 0)
        new_layout.setSpacing(28)
        new_layout.addStretch()
        self._lb_scroll.setWidget(new_container)
        self._lb_container = new_container
        self._lb_layout = new_layout
        self._user_rank_lbl.setText(translate("GamesView", "Your rank: \u2014"))

    def _load_stats_for_current(self) -> None:
        """Load stats for the currently displayed game."""
        if not self._game_keys:
            return
        key = self._game_keys[self._current_index]
        game_db_id = self._game_db_ids.get(key)
        if game_db_id:
            self._controller.load_stats(game_db_id)

    def _load_leaderboard_for_current(self) -> None:
        """Load leaderboard for the currently displayed game."""
        if not self._game_keys:
            return
        game_db_id = self._game_db_ids.get(self._game_keys[self._current_index])
        if game_db_id:
            cached_lb = self._controller._data.leaderboards.get(game_db_id)
            if cached_lb and self._last_rendered_lb_id != game_db_id:
                entries = cached_lb.get("entries", [])
                avatar_paths = [e.get("avatar_path") for e in entries if e.get("avatar_path")]
                self._controller.preload_avatars(avatar_paths)
                self._render_leaderboard(cached_lb)
                self._last_rendered_lb_id = game_db_id
            elif not cached_lb:
                self._controller.load_leaderboard(game_db_id)

    def _start_realtime_for(self, game_db_id: int) -> None:
        if game_db_id in self._rt_workers:
            return

        logger.info("Starting realtime subscription for game_db_id=%d", game_db_id)
        thread = QThread()
        thread.setObjectName(f"rt-pgs-{game_db_id}")
        worker = _RealtimeWorker(game_db_id)
        worker.moveToThread(thread)
        worker.changed.connect(
            lambda gid=game_db_id: self._on_realtime_change(gid),
            Qt.ConnectionType.QueuedConnection,
        )
        thread.started.connect(worker.run)
        thread.finished.connect(worker.deleteLater)
        self._rt_workers[game_db_id] = (thread, worker)
        thread.start()

    def _on_realtime_change(self, game_db_id: int) -> None:
        now = time.monotonic()
        last = getattr(self, "_rt_last_change", {})
        if now - last.get(game_db_id, 0) < 2.0:

            return
        last[game_db_id] = now
        self._rt_last_change = last


        flush_heartbeat()
        
        key = next((k for k, v in self._game_db_ids.items() if v == game_db_id), None)
        if key is None:
            return
        current_db_id = self._game_db_ids.get(self._game_keys[self._current_index])
        if game_db_id == current_db_id:
            self._last_rendered_lb_id = None
        self._controller.invalidate_leaderboard(game_db_id)
        self._controller.invalidate_stats(game_db_id)
        self._controller.load_leaderboard(game_db_id)
        self._controller.load_stats(game_db_id)

    def _stop_all_realtime(self) -> None:
        logger.info("Stopping all realtime subscriptions")
        self._lb_avatar_slots.clear()
        for _db_id, (thread, worker) in list(self._rt_workers.items()):
            try:
                worker.changed.disconnect()
            except RuntimeError:
                pass
            worker.stop()
            self._dying_threads.append(thread)
            thread.finished.connect(
                lambda t=thread: self._dying_threads.remove(t) if t in self._dying_threads else None
            )
            thread.finished.connect(thread.deleteLater)
        self._rt_workers.clear()

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.LanguageChange:
            self._retranslate_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self._retranslate_ui()
        if self._game_keys:
            self._load_leaderboard_for_current()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self._lb_render_gen += 1
        self._lb_avatar_slots.clear()

    def closeEvent(self, event):
        self._stop_all_realtime()
        super().closeEvent(event)

