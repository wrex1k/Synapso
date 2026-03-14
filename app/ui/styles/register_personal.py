from app.ui.styles.colors import *

REGISTER_PERSONAL_STYLES = f"""
    #titleLabel {{
    }}

    #profilePicture,
    #birthMonth,
    #day,
    #year {{
    }}

    #info,
    #uploadRestriction {{
        color: {GRAY};
    }}

    #uploadImageButton {{
       height: 20px;
       color: {OFF_WHITE};
       background-color: transparent;
       border: 1px solid {GRAY};
       border-radius: 10px;
       padding: 5px 10px;
    }}

    #uploadImageButton:hover {{
        background-color: {DARK_MID};
        border-color: {PRIMARY_HOVER};
    }}

    #birthMonthBox,
    #dayBox,
    #yearBox {{
        height: 20px;
        color: {OFF_WHITE};
        background-color: transparent;
        border: 1px solid {BORDER_PRIMARY};
        border-radius: 10px;
        padding: 5px 20px 5px 10px;
    }}

    #birthMonthBox:hover,
    #dayBox:hover,
    #yearBox:hover {{
        border-color: {PRIMARY_HOVER};
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
        outline: none;
    }}

    #birthMonthBox QAbstractItemView::item:hover,
    #dayBox QAbstractItemView::item:hover,
    #yearBox QAbstractItemView::item:hover {{
            background-color: #1B5E56;
            color: #FFFFFF;
            outline: none;
    }}
"""