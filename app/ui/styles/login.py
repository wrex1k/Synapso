from app.ui.styles.colors import *

LOGIN_STYLES = f"""
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