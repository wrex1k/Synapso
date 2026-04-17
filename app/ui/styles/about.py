from app.ui.styles.colors import *

ABOUT_STYLES = f"""
    QWidget#aboutView {{
        background-color: transparent;
    }}

    QWidget#aboutCard {{
        background-color: {BACKGROUND_GLASS};
        border: 1px solid {BORDER_LIGHTGREY};
        border-radius: 20px;
    }}

    QLabel#aboutCardTitle {{
        color: {OFF_WHITE};
    }}

    QLabel#aboutSectionTitle {{
        color: {OFF_WHITE};
        margin-top: 4px;
    }}

    QLabel#aboutDescriptionText {{
        color: {GRAY};
        line-height: 1.6;
    }}

    QLabel#aboutMetaText {{
        color: {GRAY};
        line-height: 1.5;
    }}

    QFrame#aboutDivider {{
        background-color: rgba(95, 122, 117, 0.20);
        max-height: 1px;
        min-height: 1px;
        border: none;
        margin-top: 8px;
        margin-bottom: 8px;
    }}

    QTextEdit#reportEditor {{
        background-color: {INPUT_FIELD_BACKGROUND};
        border: 1px solid {INPUT_FIELD_BORDER};
        border-radius: 8px;
        color: {OFF_WHITE};
        padding: 10px;
    }}

    QTextEdit#reportEditor:focus {{
        border-color: {PRIMARY};
    }}

    QPushButton#reportSendButton {{
        color: {OFF_WHITE};
        background-color: {PRIMARY};
        border: none;
        border-radius: 15px;
        padding: 10px 20px;
    }}
    
    QPushButton#reportSendButton:disabled {{
        background-color: {PRIMARY_DARK} 
    }}

    QLabel#builtWithDot {{
        color: rgba(255, 255, 255, 0.25);
        font-size: 18px;
        font-weight: 700;
    }}

    QLabel#builtWithName {{
        color: {OFF_WHITE};
    }}

    QLabel#builtWithDesc {{
        color: rgba(255, 255, 255, 0.42);
    }}

    QPushButton#kofiButton {{
        background-color: rgba(255, 94, 91, 0.12);
        color: #FF5E5B;
        border: none;
        border-radius: 15px;
        padding: 10px 0px;
        font-weight: 600;
        font-size: 13px;
    }}

    QPushButton#kofiButton:hover {{
        background-color: rgba(255, 94, 91, 0.20);
    }}

    QPushButton#githubSponsorButton {{
        background-color: {PRIMARY};
        color: {OFF_WHITE};
        border: none;
        border-radius: 15px;
        padding: 10px 0px;
        font-weight: 600;
        font-size: 13px;
    }}

    QPushButton#githubSponsorButton:hover {{
        background-color: {HOVER_PRIMARY};
    }}

    QComboBox#changelogCombo {{
        background-color: {BACKGROUND_GLASS};
        border: 1px solid rgba(62, 172, 145, 0.25);
        border-radius: 10px;
        padding: 3px 10px;
    }}

    QComboBox#changelogCombo::drop-down {{
        border: none;
    }}

    QComboBox#changelogCombo QAbstractItemView {{
        background-color: {BACKGROUND_GLASS};
        border: 1px solid {BORDER_LIGHTGREY};
        border-radius: 10px;
        padding: 4px;
        outline: none;
    }}

    QComboBox#changelogCombo QAbstractItemView::item {{
        background-color: transparent;
        padding: 4px 8px;
        color: {OFF_WHITE};
        border-radius: 6px;
    }}

    QComboBox#changelogCombo QAbstractItemView::item:selected {{
        background-color: rgba(62, 172, 145, 0.15);
        color: {OFF_WHITE};
    }}

    QComboBox#changelogCombo QAbstractItemView::item:hover {{
        background-color: rgba(62, 172, 145, 0.10);
        color: {OFF_WHITE};
    }}

    QLabel#changelogBullet {{
        color: {OFF_WHITE};
    }}

    QScrollArea#changelogScroll {{
        background-color: transparent;
        border: none;
    }}

    QWidget#changelogScrollContent {{
        background-color: transparent;
    }}
"""