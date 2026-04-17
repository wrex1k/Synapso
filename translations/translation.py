"""
Translation management utilities for the application.

Includes TranslationManager for loading and switching translations,
and get_translation_manager as a singleton accessor.
"""

import os
from typing import Optional

from PySide6.QtCore import QCoreApplication, QLocale, QTranslator, QT_TRANSLATE_NOOP
from PySide6.QtWidgets import QApplication

from app.utils.logger import get_logger

logger = get_logger(__name__)

class TranslationManager:
    """Manages loading and switching UI translations."""

    def __init__(self):
        """Initialize with no translator loaded and English as default."""
        self.translator: Optional[QTranslator] = None
        self.current_language: str = "en"
        self.translations_dir = os.path.dirname(__file__)

    def load_translation(self, language: str = "sk") -> bool:
        """Load a .qm translation file for the given language code."""
        app = QApplication.instance()
        if not app:
            logger.warning("QApplication not yet created")
            return False

        if self.translator:
            app.removeTranslator(self.translator)

        self.translator = QTranslator(app)

        translation_file = os.path.join(
            self.translations_dir,
            f"synapso_{language}.qm"
        )

        if self.translator.load(translation_file):
            app.installTranslator(self.translator)
            self.current_language = language
            logger.info("Translation loaded: %s", language)
            return True

        return False

    def get_system_language(self) -> str:
        """Return the two-letter language code from the system locale."""
        locale = QLocale.system().name()
        return locale.split('_')[0]

    def switch_language(self, language: str) -> bool:
        """Switch the active translation to the given language code."""
        return self.load_translation(language)

_TRANSLATION_MANAGER = None

def get_translation_manager() -> TranslationManager:
    """Return the singleton TranslationManager, creating it if needed."""
    global _TRANSLATION_MANAGER
    if _TRANSLATION_MANAGER is None:
        _TRANSLATION_MANAGER = TranslationManager()
    return _TRANSLATION_MANAGER

def init_translations(language: Optional[str] = None) -> bool:
    """Initialize translations, falling back to system language or English."""
    manager = get_translation_manager()

    if language is None:
        language = manager.get_system_language()
        if language not in ('sk', 'en'):
            language = 'en'

    return manager.load_translation(language)

def translate(context: str, source_text: str) -> str:
    """Look up source_text in the given Qt translation context."""
    return QCoreApplication.translate(context, source_text)

# Error message translation markers
QT_TRANSLATE_NOOP('Errors', 'Invalid email format')
QT_TRANSLATE_NOOP('Errors', 'Invalid password')
QT_TRANSLATE_NOOP('Errors', 'Invalid credentials')
QT_TRANSLATE_NOOP('Errors', 'Email already in use')
QT_TRANSLATE_NOOP('Errors', 'Username already taken')
QT_TRANSLATE_NOOP('Errors', 'Code has expired or is invalid')
QT_TRANSLATE_NOOP('Errors', 'User already registered')
QT_TRANSLATE_NOOP('Errors', 'New password must be different from the old password')

# Validator message translation markers
QT_TRANSLATE_NOOP('Validator', 'Password must be at least %1 characters')
QT_TRANSLATE_NOOP('Validator', 'Password cannot exceed %1 characters')
QT_TRANSLATE_NOOP('Validator', 'Username must be between %1 and %2 characters')
QT_TRANSLATE_NOOP('Validator', 'You must be at least %1 years old to register')

# Forgot password translation markers
QT_TRANSLATE_NOOP('ForgotPassword', 'Please wait before sending another reset request')

def get_error_message(error_code: str, context: str = "Errors") -> str:
    """Return a translated error message for the given error code."""
    error_map = {
        "invalid_email_format": QCoreApplication.translate(context, "Invalid email format"),
        "invalid_password": QCoreApplication.translate(context, "Invalid password"),
        "invalid_credentials": QCoreApplication.translate(context, "Invalid credentials"),
        "email_already_in_use": QCoreApplication.translate(context, "Email already in use"),
        "username_already_taken": QCoreApplication.translate(context, "Username already taken"),
        "user_already_registered": QCoreApplication.translate(context, "User already registered"),
        "token_expired": QCoreApplication.translate(context, "Code has expired or is invalid"),
        "password_same_as_old": QCoreApplication.translate(
            context, "New password must be different from the old password"
        ),
    }
    return error_map.get(error_code, error_code)
