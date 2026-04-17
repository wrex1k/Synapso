from app.ui.styles.colors import *

LOGIN_STYLES = f"""
    QPushButton#langSkBtn,
    QPushButton#langEnBtn {{
        padding: 5px;
        border-bottom: 1px solid {DARK_GRAY};
        background-color: transparent;
        color: {GRAY};
    }}

    QPushButton#langSkBtn[selected="true"],
    QPushButton#langEnBtn[selected="true"] {{
        border-bottom: 1px solid {PRIMARY_LIGHT};
        color: {PRIMARY};
    }}

    QLabel#titleLabelLeft {{
        color: {OFF_WHITE};
    }}

    QLabel#titleLabelRight {{
        color: {PRIMARY_LIGHT};
    }}

    QPushButton#forgotPasswordLink {{
        border: none;
        background-color: transparent;
        color: {GRAY};
        text-align: left;
        padding: 0;
    }}

    QPushButton#forgotPasswordLink:hover {{
        color: {PRIMARY};
    }}

    QPushButton#startRegistration,
    QPushButton#startRegistrationLabel {{
        border: none;
        background-color: transparent;
        color: {GRAY};
        padding: 0;
    }}

    QPushButton#startRegistration:hover {{
        color: {PRIMARY};
    }}
"""