from .colors import *
from .base import *
from .login import LOGIN_STYLES
from .register_auth import REGISTER_AUTH_STYLES
from .register_personal import REGISTER_PERSONAL_STYLES

__all__ = [
    # Colors
    "PRIMARY",
    "PRIMARY_HOVER",
    "PRIMARY_DARK",
    "PRIMARY_LIGHT",
    "WHITE",
    "OFF_WHITE",
    "LIGHT_GRAY",
    "GRAY",
    "DARK_GRAY",
    "DARKER_GRAY",
    "DARK",
    "ERROR",
    "WARNING",
    "SUCCESS",
    # Global styles
    "GLOBAL_STYLES",
    "INPUT_FIELD_STYLES",
    "BUTTON_PRIMARY_STYLES",
    "BUTTON_SECONDARY_STYLES",
    "PROGRESS_BAR_STYLES",
    "COMBOBOX_STYLES",
    "get_full_stylesheet",
    # View specific styles
    "LOGIN_STYLES",
    "REGISTER_AUTH_STYLES",
    "REGISTER_PERSONAL_STYLES",
]
