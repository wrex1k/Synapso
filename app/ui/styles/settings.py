from app.ui.styles.colors import *

SETTINGS_STYLES = f"""
    QWidget#settingsView {{
        background-color: transparent;
    }}

    QWidget#settingsCard {{
        background-color: {BACKGROUND_GLASS};
        border: 1px solid {BORDER_LIGHTGREY};
        border-radius: 18px;
        padding: 0px;
    }}

    QLabel#settingsCardTitle {{
        color: {OFF_WHITE};
    }}

    QLabel#settingsCardDescription {{
        color: {GRAY};
    }}

    QPushButton#langBtn {{
        background-color: transparent;
        border: 1px solid {FONT_PRIMARY};
        color: {FONT_PRIMARY};
        border-radius: 6px;
        padding: 6px 18px;
    }}

    QPushButton#langBtn:hover {{
        background-color: {FONT_PRIMARY};
        color: {OFF_WHITE};
    }}

    QPushButton#langBtn[active="true"] {{
        background-color: {FONT_PRIMARY};
        color: {OFF_WHITE};
    }}

    QPushButton#themeBtn {{
        background-color: transparent;
        border: 1px solid {FONT_PRIMARY};
        color: {FONT_PRIMARY};
        border-radius: 6px;
        padding: 6px 18px;
    }}

    QPushButton#themeBtn:hover {{
        background-color: {FONT_PRIMARY};
        color: {OFF_WHITE};
    }}

    QPushButton#themeBtn[active="true"] {{
        background-color: {FONT_PRIMARY};
        color: {OFF_WHITE};
    }}

    QPushButton#themeBtn:disabled {{
        border-color: {DARK_GRAY};
        color: {DARK_GRAY};
    }}
"""
