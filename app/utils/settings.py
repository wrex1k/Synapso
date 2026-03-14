from PySide6.QtCore import QSettings

"""
This module provides utilities for application settings management, such as:
- get_language: retrieve the current language setting from persistent storage
- set_language: update the language setting in persistent storage
"""

_settings = QSettings("Synapso", "SynapsoApp")

def get_language() -> str:
    return str(_settings.value("language", "en"))

def set_language(lang: str) -> None:
    if lang not in ("sk", "en"):
        lang = "en"
    _settings.setValue("language", lang)
