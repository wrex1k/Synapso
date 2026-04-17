from PySide6.QtCore import QSettings

_settings = QSettings("Synapso", "SynapsoApp")

def get_language() -> str:
    """Return the persisted UI language code."""
    return str(_settings.value("language", "en"))

def set_language(lang: str) -> None:
    """Persist the UI language code (sk or en)."""
    if lang not in ("sk", "en"):
        lang = "en"
    _settings.setValue("language", lang)
