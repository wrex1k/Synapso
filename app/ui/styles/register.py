from app.ui.styles.colors import *

REGISTER_STYLES = f"""
    QLabel#info,
    QPushButton#uploadRestriction {{
        color: {GRAY};
    }}

    QPushButton#uploadImageButton {{
       height: 15px;
       color: {OFF_WHITE};
       background-color: transparent;
       border: 1px solid {BORDER_UPLOAD_BUTTON};
       border-radius: 15px;
       padding: 10px 15px;
    }}

    QPushButton#uploadImageButton:hover {{
        background-color: {DARK_MID};
        border-color: {HOVER_PRIMARY};
    }}

    QComboBox#birthMonthBox,
    QComboBox#dayBox,
    QComboBox#yearBox {{
        height: 20px;
        color: {OFF_WHITE};
        background-color: transparent;
        border: 1px solid {BORDER_PRIMARY};
        border-radius: 20px;
        padding: 10px 15px;
    }}

    QComboBox#birthMonthBox:hover,
    QComboBox#dayBox:hover,
    QComboBox#yearBox:hover {{
        border-color: {HOVER_PRIMARY};
    }}

    QComboBox#birthMonthBox::drop-down,
    QComboBox#dayBox::drop-down,
    QComboBox#yearBox::drop-down {{
        border: none;
   }}

    QComboBox#birthMonthBox QAbstractItemView,
    QComboBox#dayBox QAbstractItemView,
    QComboBox#yearBox QAbstractItemView {{
        max-height: 200px;
        border: none;
        background-color: transparent;
        selection-background-color: #22756F;
        margin-top: 5px;
    }}

    #birthMonthBox QAbstractItemView::item:hover,
    #dayBox QAbstractItemView::item:hover,
    #yearBox QAbstractItemView::item:hover {{
        background-color: #1B5E56;
        color: #FFFFFF;
    }}

    QPushButton#privacyNotice {{
        color: {GRAY};
        background-color: transparent;
        border: none;
        padding: 0;
        text-align: left;
    }}

    QPushButton#privacyNotice:hover {{
        color: {FONT_PRIMARY};
    }}
"""