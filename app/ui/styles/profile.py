from app.ui.styles.colors import *

PROFILE_STYLES = f"""
    QWidget#profileView {{
        background-color: transparent;
    }}

    QWidget#profileHeaderCard {{
        background-color: {BACKGROUND_GLASS};
        border-radius: 20px;
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

    QWidget#profileInfoCard {{
        background-color: {BACKGROUND_GLASS};
        border-radius: 20px;
    }}

    QLabel#profileSectionTitle {{
        color: {OFF_WHITE};
    }}

    QLabel#profileInfoKey {{
        color: {GRAY};
    }}

    QLabel#profileInfoValue {{
        color: {OFF_WHITE};
    }}

    QFrame#profileDivider {{
        background-color: rgba(95, 122, 117, 0.20);
        max-height: 1px;
        min-height: 1px;
        border: none;
    }}
"""
