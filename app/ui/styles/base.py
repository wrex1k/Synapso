from app.ui.styles.colors import *

from app.ui.styles.games import GAMES_STYLES
from app.ui.styles.login import LOGIN_STYLES
from app.ui.styles.register import REGISTER_STYLES
from app.ui.styles.tutorial import TUTORIAL_STYLESHEET
from app.ui.styles.forgot_password import FORGOT_PASSWORD_STYLES
from app.ui.styles.profile import PROFILE_STYLES
from app.ui.styles.settings import SETTINGS_STYLES
from app.ui.styles.dashboard import DASHBOARD_STYLES
from app.ui.styles.about import ABOUT_STYLES
from app.ui.styles.statistics import STATISTICS_STYLES

from app.ui.styles.fonts import get_full_fonts, scale_font_sizes

GLOBAL_STYLES = f"""
    * {{
        outline: none;
        selection-background-color: {PRIMARY};
        selection-color: {OFF_WHITE};
    }}
    
    QLabel {{
        color: {OFF_WHITE};
    }}
"""

BASE_STYLES = f"""
    QLabel#pageSubtitleLabel {{
        color: {GRAY};
    }}
"""

NAVBAR_STYLES = f"""
    QLabel#titleNavbarLabel {{
        color: {FONT_PRIMARY};
    }}

    QWidget#profileWidget {{
        background-color: {PROFILE_WIDGET};
        border: none;
        border-radius: 26px;
        padding: 0px;
    }}

    QWidget#profileWidget:hover {{
        background-color: {PROFILE_WIDGET_HOVER};
    }}

    QLabel#usernameLabel {{
        color: {OFF_WHITE};
        padding-left: 3px;
    }}
"""

SIDEBAR_STYLES = f"""
    QPushButton {{
        border-radius: 27px;
        padding: 15px;
    }}

    QPushButton[selected="false"]:hover {{
        background-color: {BUTTON_FALSE_HOVER};
    }}

    QPushButton[selected="true"] {{
        background-color: {OFF_WHITE};
    }}

    QPushButton[selected="true"]:hover {{
        background-color: {OFF_WHITE};
    }}

    #primarySidebarWidget,
    #secondarySidebarWidget,
    #logoutButton {{
        background-color: {BACKGROUND_GLASS};
        border: 1px solid {BORDER_LIGHTGREY};
        border-radius: 27px;
    }}

    #logoutButton:hover {{
        background-color: {DARK};
    }}
"""


INPUT_FIELD_STYLES = f"""
    QLineEdit#inputEdit {{
        height: 20px;
        color: {OFF_WHITE};
        background-color: transparent;
        border: 1px solid {BORDER_PRIMARY};
        border-radius: 20px;
        padding: 10px 15px;

    }}

    QLineEdit#inputEdit:hover {{
        border-color: {HOVER_PRIMARY};
        color: {OFF_WHITE};
    }}

    QLineEdit#inputEdit:focus {{
        border-color: {HOVER_PRIMARY};
        color: {OFF_WHITE};
    }}
"""

UPLOAD_BUTTON_STYLES = f"""
    QPushButton#uploadButton {{
        height: 25px;
        border: none;
        background-color: {PRIMARY};
        padding: 10px 30px;
        color: {OFF_WHITE};
        border-radius: 20px;
    }}
    QPushButton#uploadButton:hover {{
        background-color: {HOVER_PRIMARY};
    }}
"""

BUTTON_PRIMARY_STYLES = f"""
    QPushButton#primaryButton {{
        height: 25px;
        border: none;
        background-color: {PRIMARY};
        padding: 10px 30px;
        color: {OFF_WHITE};
        border-radius: 20px;
    }}

    QPushButton#primaryButton:hover {{
        background-color: {HOVER_PRIMARY};
    }}

    QPushButton#primaryButton:disabled {{
        background-color: {PRIMARY_DARK};
    }}

    QPushButton#primaryButton[state="loading"],
    QPushButton#primaryButton[state="loading"]:disabled {{
        background-color: {HOVER_PRIMARY};
    }}

    QPushButton#primaryButton[state="error"],
    QPushButton#primaryButton[state="error"]:disabled {{
        background-color: {ERROR};
    }}
"""

BUTTON_TRANSPARENT_STYLES = f"""
    QPushButton#transparentButton {{
        border: 1px solid {PRIMARY};
        background-color: transparent;
        color: {OFF_WHITE};
        border-radius: 22px;
    }}

    QPushButton#transparentButton:hover {{
        background-color: {HOVER_DARK};
    }}
"""

BACK_BUTTON_STYLES = f"""
    QPushButton#back {{
        background-color: transparent;
        color: {OFF_WHITE};
        border: none;
    }}
"""

PROGRESS_BAR_STYLES = f"""
    QProgressBar {{
        margin-top: 6px;
        background-color: {DARK_MID};
        max-height: 10px;
        border-radius: 5px;
    }}

    QProgressBar::chunk {{
        border-radius: 5px;
    }}

    QProgressBar[strength="weak"]::chunk {{
        background-color: {ERROR};
    }}

    QProgressBar[strength="mid"]::chunk {{
        background-color: {WARNING};
    }}

    QProgressBar[strength="strong"]::chunk {{
        background-color: {SUCCESS};
    }}
"""

KEY_CHIP_STYLES = f"""
    QWidget#keyWidget {{
        background-color: {BACKGROUND_KEY_CHIP};
        border-radius: 10px;
    }}

    QLabel#keyLabel {{
        color: {OFF_WHITE};
        background: transparent;
    }}
"""

DIALOG_WINDOW_STYLES = f"""
    QDialog#deleteConfirmDialog {{
        background-color: {DARK};
        border: 1px solid {BORDER_LIGHTGREY};
        border-radius: 16px;
    }}
    
    QLabel#deleteDialogTitle {{
        color: {DANGER};
        font-size: 17px;
        font-weight: 700;
    }}

    QLabel#deleteDialogDesc {{
        color: {GRAY};
        font-size: 15px;
    }}

    QPushButton#deleteDialogCancelBtn {{
        background-color: transparent;
        color: {GRAY};
        border: 1px solid {BORDER_LIGHTGREY};
        border-radius: 12px;
        padding: 0 16px;
        font-size: 15px;
    }}
    
    QPushButton#deleteDialogCancelBtn:hover {{
        background-color: {HOVER_DARK};
        color: {OFF_WHITE};
    }}

    QPushButton#deleteDialogConfirmBtn {{
        background-color: {DANGER_BACKGROUND};
        color: {DANGER};
        border: 1px solid {DANGER_BACKGROUND};
        border-radius: 12px;
        padding: 0 16px;
        font-size: 15px;
    }}
    
    QPushButton#deleteDialogConfirmBtn:hover {{
        background-color: {DANGER_BORDER_HOVER};
    }}
"""

CLOSE_BTN_STYLES = f"""
    QPushButton#closeBtnOverlay {{
        border: none;
        background-color: transparent;
        color: transparent;
        border-radius: 17px;
        font-weight: 400;
    }}

    QPushButton#closeBtnOverlay:hover {{
        color: {OFF_WHITE};
        background-color: {BACKGROUND_GLASS};
        border: 1px solid {BORDER_LIGHTGREY};
    }}

    QPushButton#closeBtnOverlay:pressed {{
        background-color: {DARK};
        color: {OFF_WHITE};
    }}
"""

def get_full_stylesheet():
    raw = (
        get_full_fonts()
        + BASE_STYLES
        + GLOBAL_STYLES
        + NAVBAR_STYLES
        + SIDEBAR_STYLES
        + INPUT_FIELD_STYLES
        + UPLOAD_BUTTON_STYLES
        + BUTTON_PRIMARY_STYLES
        + PROGRESS_BAR_STYLES
        + BUTTON_TRANSPARENT_STYLES
        + KEY_CHIP_STYLES
        + DIALOG_WINDOW_STYLES
        + BACK_BUTTON_STYLES
        + GAMES_STYLES
        + TUTORIAL_STYLESHEET
        + LOGIN_STYLES
        + REGISTER_STYLES
        + FORGOT_PASSWORD_STYLES
        + PROFILE_STYLES
        + SETTINGS_STYLES
        + CLOSE_BTN_STYLES
        + DASHBOARD_STYLES
        + ABOUT_STYLES
        + STATISTICS_STYLES
    )
    return scale_font_sizes(raw)