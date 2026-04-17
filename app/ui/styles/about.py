from app.ui.styles.colors import *

ABOUT_STYLES = f"""
    QWidget#aboutView {{
        background-color: transparent;
    }}

    QWidget#aboutCard {{
        background-color: {BACKGROUND_GLASS};
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
        background-color: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 8px;
        color: {OFF_WHITE};
        padding: 10px;
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

    QComboBox#changelogCombo {{
        color: {FONT_PRIMARY};
        background-color: {BACKGROUND_GLASS};
        border: 1px solid rgba(62, 172, 145, 0.25);
        border-radius: 10px;
        padding: 3px 10px;
    }}

    QComboBox#changelogCombo::drop-down {{
        border: none;
        border-radius: 5px;
    }}

    QComboBox#changelogCombo QAbstractItemView {{
        background-color: {BACKGROUND_GLASS};
        color: {OFF_WHITE};
        border: none;
        border-radius: 10px;
        selection-background-color: #22756F;
        outline: none;
    }}

    QComboBox#changelogCombo QAbstractItemView::item {{
        border-radius: 5px;
        padding-left: 3px;
    }}

    QComboBox#changelogCombo QAbstractItemView::item:selected {{
        border: none;
        border-radius: 5px;
    }}

    QComboBox#changelogCombo QAbstractItemView::item:hover {{
        border: none;
        border-radius: 5px;
        background-color: {PRIMARY};
    }}

    QLabel#changelogBullet {{
        color: {FONT_PRIMARY};
    }}

    QScrollArea#changelogScroll {{
        background-color: transparent;
        border: none;
    }}

    QWidget#changelogScrollContent {{
        background-color: transparent;
    }}
"""