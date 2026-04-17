from app.ui.styles.colors import *

PROFILE_STYLES = f"""
    QWidget#profileView {{
        background-color: transparent;
    }}

    QFrame#profileHeroCard,
    QFrame#profileMainCard {{
        background-color: {BACKGROUND_GLASS};
        border-radius: 20px;
        border: 1px solid {BORDER_LIGHTGREY};
    }}

    QLabel#profileUsernameLabel {{
        color: {OFF_WHITE};
    }}

    QLabel#profileHandleLabel {{
        color: {PRIMARY_LIGHT};
    }}

    QLabel#profileMemberLabel {{
        color: {DARK_GRAY};
    }}

    QLabel#profileHeroMetaValue {{
        color: {OFF_WHITE};
    }}

    QLabel#profileHeroMetaSubtext {{
        color: {GRAY};
    }}

    QLabel#profileSectionTitle {{
        color: {OFF_WHITE};
    }}

    QLabel#profileInputLabel {{
        color: {GRAY};
    }}

    QLabel#profileReadonlyValue {{
        color: {DARK_GRAY};
        padding: 11px 14px;
        background-color: {INPUT_FIELD_BACKGROUND};
        border: 1px solid {INPUT_FIELD_BORDER};
        border-radius: 12px;
    }}

    QLineEdit#profileLineEdit,
    QDateEdit#profileDateEdit,
    QComboBox#profileBirthMonthBox,
    QComboBox#profileDayBox,
    QComboBox#profileYearBox {{
        color: {OFF_WHITE};
        padding: 0 14px;
        min-height: 42px;
        background-color: {INPUT_FIELD_BACKGROUND};
        border: 1px solid {INPUT_FIELD_BORDER};
        border-radius: 12px;
    }}

    #profileLineEdit:hover,
    #profileDateEdit:hover,
    #profileBirthMonthBox:hover,
    #profileDayBox:hover,
    #profileYearBox:hover {{
        border: 1px solid {HOVER_PRIMARY};
    }}

    QLineEdit#profileLineEdit:focus,
    QDateEdit#profileDateEdit:focus,
    QComboBox#profileBirthMonthBox:focus,
    QComboBox#profileDayBox:focus,
    QComboBox#profileYearBox:focus {{
        border: 1px solid {PRIMARY_LIGHT};
    }}

    #QComboBox::drop-down#profileBirthMonthBox,
    #QComboBox::drop-down#profileDayBox,
    #QComboBox::drop-down#profileYearBox {{
        border: none;
    }}

    QComboBox#profileBirthMonthBox QAbstractItemView,
    QComboBox#profileDayBox QAbstractItemView,
    QComboBox#profileYearBox QAbstractItemView {{
        max-height: 200px;
        border: none;
        background-color: transparent;
        selection-background-color: {PRIMARY};
        margin-top: 5px;
    }}

    QLabel#profileFeedbackLabel {{
        color: {PRIMARY_LIGHT};
    }}

    QLabel#profileFeedbackLabel[error="true"] {{
        color: {ERROR};
    }}

    QPushButton#profilePrimaryButton {{
        background-color: {PRIMARY_LIGHT};
        color: white;
        border: none;
        border-radius: 14px;
        padding: 0 16px;
        min-width: 140px;
    }}

    QPushButton#profilePrimaryButton:hover {{
        background-color: {FONT_PRIMARY};
    }}

    QLabel#profileDangerTitle {{
        color: {DANGER};
    }}

    QLabel#profileDangerDescription {{
        color: {GRAY};
    }}

    QPushButton#profileDangerButton {{
        background-color: {DANGER_BACKGROUND};
        color: {DANGER};
        border: 1px solid {DANGER_BORDER};
        border-radius: 14px;
        padding: 0 16px;
        min-width: 140px;
    }}

    QPushButton#profileDangerButton:hover {{
        background-color: {DANGER_BORDER_HOVER};
    }}
""" 