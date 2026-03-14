from app.ui.styles.colors import *

from app.ui.styles.login import LOGIN_STYLES
from app.ui.styles.register_auth import REGISTER_AUTH_STYLES
from app.ui.styles.register_personal import REGISTER_PERSONAL_STYLES
from app.ui.styles.forgot_password import FORGOT_PASSWORD_STYLES
from app.ui.styles.fonts import FONT_SIZE_STYLESHEET


GLOBAL_STYLES = f"""
    * {{
        font-family: "General Sans";
        font-weight: 400;
        outline: none;
    }}
    
    QLabel {{
        color: {OFF_WHITE};
    }}
"""


INPUT_FIELD_STYLES = f"""
    QLabel#inputLabel {{
    }}

    QLineEdit#inputEdit {{
        height: 20px;
        font-size: 14px;
        color: {OFF_WHITE};
        background-color: transparent;
        border: 1px solid {BORDER_PRIMARY};
        border-radius: 10px;
        padding: 5px 10px;
    }}

    QLineEdit#inputEdit:hover {{
        border-color: {PRIMARY_HOVER};
        color: {OFF_WHITE};
    }}

    QLineEdit#inputEdit:focus {{
        border-color: {PRIMARY_HOVER};
        color: {OFF_WHITE};
    }}
"""


BUTTON_PRIMARY_STYLES = f"""
    QPushButton#primaryButton {{
        height: 20px;
        border: none;
        background-color: {PRIMARY};
        padding: 10px 15px;
        color: {OFF_WHITE};
        border-radius: 10px;
    }}

    QPushButton#primaryButton:hover {{
        background-color: {PRIMARY_HOVER};
    }}

    QPushButton#primaryButton:disabled {{
        background-color: {PRIMARY_DARK};
    }}

    QPushButton#primaryButton[state="loading"],
    QPushButton#primaryButton[state="loading"]:disabled {{
        background-color: {PRIMARY_HOVER};
    }}

    QPushButton#primaryButton[state="error"],
    QPushButton#primaryButton[state="error"]:disabled {{
        background-color: {ERROR};
    }}
"""

BACK_BUTTON_STYLES = f"""
    QPushButton#back {{
        background-color: transparent;
        color: {OFF_WHITE};
        font-size: 15px;
        border: none;
        outline: none;
    }}

    QPushButton#back:hover {{
        font-size: 18px;
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

def get_full_stylesheet():
    return (
        GLOBAL_STYLES
        + FONT_SIZE_STYLESHEET
        + INPUT_FIELD_STYLES
        + BUTTON_PRIMARY_STYLES
        + PROGRESS_BAR_STYLES
        + BACK_BUTTON_STYLES
        + LOGIN_STYLES
        + REGISTER_AUTH_STYLES
        + REGISTER_PERSONAL_STYLES
        + FORGOT_PASSWORD_STYLES
    )