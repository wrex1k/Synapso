from app.ui.styles.colors import *

GAMES_STYLES = f"""
    QWidget#gamesView {{
        background-color: transparent;
    }}

    QWidget#titleWidget {{
        background-color: transparent;
    }}

    QLabel#gameTitle {{
        min-height: 24px;
        color: {OFF_WHITE};
    }}

    QLabel#gameDescription {{
        color: {GRAY};
    }}

    QPushButton#switcherLeft,
    QPushButton#switcherRight {{
        background: transparent;
        padding: 0px;
    }}

    QLabel#switcherTitle {{
        color: {GRAY};
        padding-bottom: 2px;
    }}

    QWidget#switcherWidget {{
        background-color: transparent;
        border: 1px solid {BORDER_LIGHTGREY};
        border-radius: 26px;
        padding: 18px;
        min-height: 15px;
        max-height: 15px;
        min-width: 220px;
        max-width: 220px;
    }}

    QWidget#switcherWidget:hover {{
        border-color: {BORDER_GREY};
    }}

    QLabel#infoCardTitle {{
        color: {OFF_WHITE};
    }}

    QLabel#infoCardDescription {{
        color: {GRAY};
        line-height: 1.4;
    }}

    QWidget#infoCardWidget {{
        background-color: {BACKGROUND_GLASS};
        border: 1px solid {BORDER_LIGHTGREY};
        border-radius: 18px;
    }}

    QLabel#rtCardTitle,
    QLabel#accCardTitle,
    QLabel#piCardTitle {{
        color: {OFF_WHITE};
    }}

    QLabel#rtCardValue,
    QLabel#accCardValue,
    QLabel#piCardValue {{
        color: {GRAY};
    }}

    QLabel#rtCardGlobal,
    QLabel#accCardGlobal,
    QLabel#piCardGlobal {{
        color: {OFF_WHITE};
    }}

    QWidget#rtCardWidget,
    QWidget#accCardWidget,
    QWidget#piCardWidget {{
        background-color: {BACKGROUND_GLASS};
        border: 1px solid {BORDER_LIGHTGREY};
        border-radius: 18px;
    }}

    QLabel#activityCardTitle {{
        color: {OFF_WHITE};
    }}

    QLabel#activityCardDescription {{
        color: rgba(255, 255, 255, 0.5);
    }}

    QLabel#activityPPRowNumber,
    QLabel#activityGTRowNumber,
    QLabel#activityTWRowNumber,
    QLabel#activityTGRowNumber {{
        color: {FONT_PRIMARY};
        padding: 11px 15px;
        background-color: rgba(62, 172, 145, 0.05);
        border: none;
        border-radius: 10px;
    }}

    QLabel#activityPPRowTitle,
    QLabel#activityGTRowTitle,
    QLabel#activityTWRowTitle,
    QLabel#activityTGRowTitle {{
        color: {OFF_WHITE};
    }}

    QWidget#activityPPWidget,
    QWidget#activityGTWidget,
    QWidget#activityTWWidget,
    QWidget#activityTGWidget {{
        border: none;
        border-bottom: 1px solid rgba(95, 122, 117, 0.15);
    }}

    QWidget#activityCardWidget {{
        background-color: {BACKGROUND_GLASS};
        border: 1px solid {BORDER_LIGHTGREY};
        border-radius: 14px;
        min-width: 300px;
    }}

    QPushButton#playButton {{
        border: none;
        background-color: {PRIMARY};
        color: {OFF_WHITE};
        border-radius: 22px;
    }}

    QPushButton#playButton:hover {{
        background-color: {HOVER_PRIMARY};
    }}

    QPushButton#playButton:disabled {{
        background-color: {PRIMARY_DARK};
        color: {DARK_GRAY};
    }}

    QPushButton#tutorialButton {{
        border: 1px solid {PRIMARY};
        background-color: transparent;
        color: {OFF_WHITE};
        padding: 10px 22px;
        border-radius: 22px;
    }}

    QPushButton#tutorialButton:hover{{
        background-color: {HOVER_DARK};
    }}

    QWidget#leaderboardCardWidget {{
        background-color: {BACKGROUND_GLASS};
        border: 1px solid {BORDER_UNDERLINE};
        border-radius: 18px;
        min-width: 300px;
    }}

    QLabel#leaderboardCardTitle {{
        color: {OFF_WHITE};
        border: none;
    }}

    QLabel#leaderboardRowImage {{
        max-width: 40px;
        max-height: 40px;
        border: none;
        border-radius: 10px;
    }}

    QLabel#leaderboardRowTitle {{
        color: {OFF_WHITE};
    }}

    QLabel#leaderboardRowValue {{
        color: {OFF_WHITE};
    }}

    QWidget#leaderboardRowWidget {{
        border: none;
        border-bottom: 1px solid {BORDER_UNDERLINE};
    }}

    QScrollArea#leaderboardScroll {{
        background-color: transparent;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: transparent;
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QWidget#lbContainer {{
        background-color: transparent;
    }}

    QLabel#userRankLabel {{
        color: {OFF_WHITE};
    }}

    QProgressBar#stroopTrialBar {{
        background-color: {PROGRESS_BAR};
        border: none;
        border-radius: 5px;
        min-height: 12px;
    }}
    
    QProgressBar#stroopTrialBar::chunk {{
        background-color: {PROGRESS_BAR_CHUNK};
        border-radius: 5px;
        min-height: 12px;
    }}

    QProgressBar#stroopAccuracyBar {{
        background-color: {TIMER_BAR};
        border: none;
        border-radius: 4px;
        min-height: 8px;
        max-height: 8px;
    }}
    
    QProgressBar#stroopAccuracyBar::chunk {{
        background-color: {TIMER_BAR_CHUNK};
        border-radius: 4px;
        min-width: 0px;
    }}

    QLabel[hud="trial"] {{
        color: {OFF_WHITE};
        font-size: 20px;
        font-weight: 500;
        background: transparent;
    }}
    QLabel[hud="title"] {{
    color: {OFF_WHITE};
    font-size: 20px;
    font-weight: 500;
    }}
    QLabel[hud="hint"] {{
        font-size: 20px;
    }}

"""

def get_stroop_label_style(color: str, size: int, weight: int = 700) -> str:
    return f"color: {color}; font-size: {size}px; font-weight: {weight}; background: transparent;"


def format_hud_progress(label: str, current: str, total: str, primary_color: str = OFF_WHITE, secondary_color: str = GRAY) -> str:
    return (
        f'<span style="color:{primary_color};">{label}</span>&nbsp;&nbsp;'
        f'<span style="color:{secondary_color};">{current}/{total}</span>'
    )


def format_hud_infinite(label: str, primary_color: str = OFF_WHITE, secondary_color: str = GRAY) -> str:
    return (
        f'<span style="color:{primary_color};">{label}</span>&nbsp;&nbsp;'
        f'<span style="color:{secondary_color};">∞</span>'
    )


def format_ratio_counter(current: int, total: int, primary_color: str = OFF_WHITE, secondary_color: str = GRAY) -> str:
    return (
        f'<span style="color:{primary_color};">{current}</span>'
        f'<span style="color:{secondary_color};">/{total}</span>'
    )


# Memory Grid styles
MEMORY_GRID_PANEL_STYLE = "background-color: #173A35; border-radius: 16px;"
MEMORY_GRID_CELL_COLORS = {
    "off": GRAY,
    "on": FONT_PRIMARY,
    "selected": PRIMARY_LIGHT,
    "wrong": INCORRECT_COLOR,
}


def get_memory_grid_phase_style(color: str, size: int, weight: int = 600) -> str:
    return f"color: {color}; font-size: {size}px; font-weight: {weight}; background: transparent;"


def get_memory_grid_counter_style(color: str = OFF_WHITE, size: int = 22, weight: int = 500) -> str:
    return f"color: {color}; font-size: {size}px; font-weight: {weight}; background: transparent;"


def get_memory_grid_cell_style(state: str) -> str:
    color = MEMORY_GRID_CELL_COLORS.get(state, MEMORY_GRID_CELL_COLORS["off"])
    return (
        f"QPushButton {{"
        f"background-color: {color};"
        f"border: none;"
        f"border-radius: 16px;"
        f"}}"
    )
