from app.ui.styles.colors import *

FORGOT_PASSWORD_STYLES = f"""
    #titleLeft {{
        color: {OFF_WHITE};
    }}

    #titleRight {{
        color: {PRIMARY_LIGHT};
    }}

    #descLabel {{
        color: {DARK_GRAY};
    }}

    #updateButton,
    #verifyButton,
    #approveButton {{
        height: 20px;
        border: none;
        background-color: {PRIMARY};
        padding: 10px 15px;
        color: {OFF_WHITE};
        border-radius: 10px;
        min-width: 150px;
    }}

    #updateButton:hover,
    #verifyButton:hover,
    #approveButton:hover {{
        background-color: {HOVER_PRIMARY};
    }}

    #updateButton:disabled,
    #verifyButton:disabled,
    #approveButton:disabled {{
        background-color: {GRAY};
        color: {LIGHT_GRAY};
    }}

    #resendButton {{
        border: none;
        background-color: transparent;
        color: {PRIMARY_LIGHT};
        padding: 5px 10px;
    }}

    #resendButton:hover:enabled {{
        color: {PRIMARY};
    }}

    #resendButton:disabled {{
        color: {DARK_GRAY};
        text-decoration: none;
    }}

    #timerLabel {{
        color: {DARK_GRAY};
    }}

    QLineEdit[objectName^="otpEdit"] {{
        background-color: transparent;
        border: none;
        border-bottom: 2px solid {GRAY};
        color: {OFF_WHITE};
    }}

    QLineEdit[objectName^="otpEdit"]:focus {{
        border-color: {PRIMARY_LIGHT};
    }}

    QLineEdit[objectName^="otpEdit"]:hover {{
        color: {HOVER_PRIMARY};
        border-color: {HOVER_PRIMARY};
    }}
"""