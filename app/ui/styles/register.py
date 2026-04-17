from app.ui.styles.colors import *

REGISTER_STYLES = f"""
    #info,
    #uploadRestriction {{
        color: {GRAY};
    }}

    #uploadImageButton {{
       height: 15px;
       color: {OFF_WHITE};
       background-color: transparent;
       border: 1px solid {BORDER_UPLOAD_BUTTON};
       border-radius: 15px;
       padding: 10px 15px;
    }}

    #uploadImageButton:hover {{
        background-color: {DARK_MID};
        border-color: {HOVER_PRIMARY};
    }}

    #birthMonthBox,
    #dayBox,
    #yearBox {{
        height: 20px;
        color: {OFF_WHITE};
        background-color: transparent;
        border: 1px solid {BORDER_PRIMARY};
        border-radius: 20px;
        padding: 10px 15px;
    }}

    #birthMonthBox:hover,
    #dayBox:hover,
    #yearBox:hover {{
        border-color: {HOVER_PRIMARY};
    }}

    #birthMonthBox::drop-down,
    #dayBox::drop-down,
    #yearBox::drop-down {{
        border: none;
    }}

    #birthMonthBox QAbstractItemView,
    #dayBox QAbstractItemView,
    #yearBox QAbstractItemView {{
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
"""