from app.ui.styles.colors import *

from app.ui.styles.games import GAMES_STYLES
from app.ui.styles.login import LOGIN_STYLES
from app.ui.styles.register import REGISTER_STYLES
from app.ui.styles.tutorial import TUTORIAL_STYLESHEET
from app.ui.styles.forgot_password import FORGOT_PASSWORD_STYLES

from app.ui.styles.fonts import get_full_fonts

GLOBAL_STYLES = f"""
    * {{
        outline: none;
    }}
    
    QLabel {{
        color: {OFF_WHITE};
    }}
"""

NAVBAR_STYLES = f"""
    #titleNavbarLabel {{
            color: {FONT_PRIMARY};
            font-size: 38px;
            font-weight: 600;
    }}

    #profileWidget {{
        background-color: {PROFILE_WIDGET};
        border: none;
        border-radius: 26px;
    }}

    #profileWidget:hover {{
        background-color: {PROFILE_WIDGET_HOVER};
    }}

    QLabel#usernameLabel {{
        color: {OFF_WHITE};
        font-size: 14px;
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
        background-color: {BACKGROUND_SIDEBAR};
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
        background-color: {HOVER_LIGHT};
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

def get_full_stylesheet():
    return (
        get_full_fonts()
        + GLOBAL_STYLES
        + NAVBAR_STYLES
        + SIDEBAR_STYLES
        + INPUT_FIELD_STYLES
        + UPLOAD_BUTTON_STYLES
        + BUTTON_PRIMARY_STYLES
            + PROGRESS_BAR_STYLES
            + BUTTON_TRANSPARENT_STYLES
        + KEY_CHIP_STYLES
        + BACK_BUTTON_STYLES
        + GAMES_STYLES
        + TUTORIAL_STYLESHEET
        + LOGIN_STYLES
        + REGISTER_STYLES
        + FORGOT_PASSWORD_STYLES
    )